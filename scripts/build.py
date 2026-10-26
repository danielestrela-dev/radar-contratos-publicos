"""Coleta paginada do PNCP, qualidade, SQLite e exportação pública."""
import argparse, hashlib, json, logging, sqlite3, time
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from urllib.error import HTTPError, URLError
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
API='https://pncp.gov.br/api/consulta/v1/contratos'
def cents(value):
    if value is None or isinstance(value,bool): return None
    try:
        n=Decimal(str(value))
        return int((n*100).quantize(Decimal('1'),rounding=ROUND_HALF_UP)) if n.is_finite() else None
    except (InvalidOperation,ValueError): return None
def iso(value):
    try: return date.fromisoformat(str(value)[:10]).isoformat()
    except ValueError: return None
def request(params):
    for attempt in range(4):
        try:
            with urlopen(Request(API+'?'+urlencode(params),headers={'User-Agent':'RadarContratos/1.0'}),timeout=120) as r:
                body=r.read()
                return json.loads(body) if body else dict(data=[],totalPaginas=0,totalRegistros=0)
        except HTTPError as e:
            if e.code not in (429,500,502,503,504) or attempt==3: raise
        except (URLError,TimeoutError):
            if attempt==3: raise
        time.sleep(2**attempt)
def collect(cfg,offline=False):
    folder=ROOT/'data/raw'/f"{cfg['orgao_cnpj']}_{cfg['inicio']}_{cfg['fim']}"
    folder.mkdir(parents=True,exist_ok=True)
    rows,hashes,page,total=[],{},1,None
    while total is None or page<=total:
        path=folder/f'page_{page:04}.json'
        if not offline:
            payload=request(dict(dataInicial=cfg['inicio'],dataFinal=cfg['fim'],cnpjOrgao=cfg['orgao_cnpj'],pagina=page,tamanhoPagina=500))
            temp=path.with_suffix('.tmp'); temp.write_text(json.dumps(payload,ensure_ascii=False),encoding='utf-8'); temp.replace(path)
        payload=json.loads(path.read_text(encoding='utf-8-sig'))
        if not isinstance(payload.get('data'),list): raise ValueError('Resposta inválida')
        if total is not None and total!=payload['totalPaginas']: raise ValueError('Paginação mudou; repita')
        total=payload['totalPaginas']
        if payload.get('numeroPagina',page)!=page: raise ValueError('Página inesperada')
        hashes[path.name]=hashlib.sha256(path.read_bytes()).hexdigest()
        rows.extend(payload['data']); logging.info('Página %s/%s: %s registros',page,total,len(rows)); page+=1
    if len(rows)!=payload['totalRegistros']: raise ValueError('Contagem difere da API')
    return rows,hashes
def normalize(records,cfg):
    rows,seen,duplicates=[],set(),0
    for r in sorted(records,key=lambda x:str(x.get('dataAtualizacaoGlobal') or x.get('dataAtualizacao') or ''),reverse=True):
        key=r.get('numeroControlePNCP')
        if not key: raise ValueError('Chave PNCP ausente')
        if key in seen:
            duplicates+=1; continue
        seen.add(key)
        if (r.get('orgaoEntidade') or {}).get('cnpj')!=cfg['orgao_cnpj']: raise ValueError('Órgão fora do recorte')
        pub=iso(r.get('dataPublicacaoPncp'))
        if not pub or not cfg['inicio']<=pub.replace('-','')<=cfg['fim']: raise ValueError('Publicação fora do período')
        start,end=iso(r.get('dataVigenciaInicio')),iso(r.get('dataVigenciaFim')); value=cents(r.get('valorGlobal')); issues=[]
        if value is None or value<0: issues.append('valor_invalido')
        if not start or not end: issues.append('vigencia_ausente')
        elif end<start: issues.append('vigencia_invertida')
        if not r.get('niFornecedor'): issues.append('fornecedor_ausente')
        nature='receita' if r.get('receita') is True else 'despesa' if r.get('receita') is False else 'nao_informada'
        if nature=='nao_informada': issues.append('natureza_ausente')
        pj=r.get('tipoPessoa')=='PJ'
        supplier=str(r['niFornecedor']) if pj and r.get('niFornecedor') else 'NAO_PJ_OU_AUSENTE'
        rows.append(dict(id=key,publicacao=pub,mes=pub[:7],inicio=start,fim=end,fornecedor_id=supplier,fornecedor=r.get('nomeRazaoSocialFornecedor') if pj else 'Pessoa física / outro / não informado',tipo_pessoa=r.get('tipoPessoa'),valor_centavos=value,natureza=nature,tipo=(r.get('tipoContrato') or {}).get('nome'),uf=(r.get('unidadeOrgao') or {}).get('ufSigla'),qualidade=';'.join(issues),vigencia_valida=int(bool(start and end and end>=start))))
    df=pd.DataFrame(rows)
    if len(df): df['valor_centavos']=pd.array(df.valor_centavos,dtype='Int64')
    return df,duplicates
def findings(df,cfg):
    expense=df[(df.natureza=='despesa') & df.valor_centavos.notna() & (df.valor_centavos>=0)]
    total=int(expense.valor_centavos.sum()); top=expense[expense.fornecedor_id!='NAO_PJ_OU_AUSENTE'].groupby('fornecedor').valor_centavos.sum().sort_values(ascending=False)
    leader=f'{top.index[0]}: {100*int(top.iloc[0])/total:.2f}% do valor de despesa válido' if total and len(top) else 'Sem fornecedor elegível'
    ref=date.fromisoformat(cfg['referencia'])
    upcoming=sum(1 for r in expense.to_dict('records') if r['vigencia_valida'] and 0<=(date.fromisoformat(r['fim'])-ref).days<=90)
    bad=int((df.qualidade!='').sum())
    text=f"# Descobertas do recorte\n\nÓrgão: {cfg['orgao_nome']}. Publicações: {cfg['inicio']} a {cfg['fim']}. Referência de vencimentos: {cfg['referencia']}.\n\n1. **Concentração:** {leader}. Apoia priorização de acompanhamento. Não demonstra irregularidade ou dependência sem analisar objetos e mercado.\n2. **Vencimentos:** {upcoming} registros de despesa com valor válido e vigência consistente terminam em até 90 dias. Apoia uma lista de revisão; não confirma situação ativa ou ausência de prorrogação.\n3. **Qualidade:** {bad} de {len(df)} registros apresentam ao menos um alerta. Apoia conferência na fonte antes de decisões.\n\nValor global informado na coleta não é gasto pago nem orçamento anual. O recorte inclui contratos/empenhos publicados no período, inclusive assinados em outros anos. Não representa toda a carteira vigente. Retificações podem alterar resultados. Contagens são de registros PNCP únicos, não necessariamente instrumentos jurídicos distintos.\n"
    (ROOT/'ANALISE.md').write_text(text,encoding='utf-8')
def build(cfg,offline=False):
    records,hashes=collect(cfg,offline)
    if not records: raise ValueError('Recorte vazio')
    df,duplicates=normalize(records,cfg); result=ROOT/'results'; result.mkdir(exist_ok=True)
    df.to_csv(result/'contratos.csv',index=False,encoding='utf-8-sig')
    with sqlite3.connect(ROOT/'data/contratos.sqlite') as db:
        df.to_sql('contratos',db,if_exists='replace',index=False); db.execute('CREATE UNIQUE INDEX contrato_id ON contratos(id)')
        db.executescript((ROOT/'sql/analysis.sql').read_text(encoding='utf-8-sig'))
        for name in ('mensal','fornecedores','qualidade'):
            pd.read_sql_query(f'SELECT * FROM vw_{name}',db).to_csv(result/f'{name}.csv',index=False,encoding='utf-8-sig')
    meta=dict(config=cfg,coletado_em=datetime.now(timezone.utc).isoformat(),recebidos=len(records),unicos=len(df),duplicados=duplicates,paginas_sha256=hashes,endpoint=API)
    (ROOT/'data/manifest.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
    (ROOT/'docs/data.js').write_text('window.RADAR='+json.dumps(dict(meta=meta,contratos=json.loads(df.to_json(orient='records',force_ascii=False))),ensure_ascii=False)+';',encoding='utf-8')
    findings(df,cfg); logging.info('Concluído: %s registros únicos',len(df))
if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--offline',action='store_true'); p.add_argument('--referencia'); a=p.parse_args()
    logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)s %(message)s',handlers=[logging.StreamHandler(),logging.FileHandler(ROOT/'pipeline.log',encoding='utf-8')])
    cfg=json.loads((ROOT/'config.json').read_text(encoding='utf-8-sig'))
    if a.referencia: cfg['referencia']=date.fromisoformat(a.referencia).isoformat()
    try: build(cfg,a.offline)
    except Exception:
        logging.exception('Pipeline interrompido; exportações podem ser da execução anterior'); raise
