'use strict';
const source=window.RADAR, $=id=>document.getElementById(id), money=n=>new Intl.NumberFormat('pt-BR',{style:'currency',currency:'BRL',maximumFractionDigits:0}).format(n/100), number=n=>new Intl.NumberFormat('pt-BR').format(n);
const escape=s=>String(s??'—').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let filtered=[],page=0; const size=12;
$('reference').value=source.meta.config.referencia;
for(let m=1;m<=12;m++){const v=`2025-${String(m).padStart(2,'0')}`;const o=new Option(new Date(v+'-15T12:00:00').toLocaleDateString('pt-BR',{month:'long'}),v);$('month').add(o)}
$('stamp').textContent=`COLETA ${new Date(source.meta.coletado_em).toLocaleString('pt-BR',{timeZone:'America/Bahia'})} · ${number(source.meta.unicos)} REGISTROS · PNCP`;
function days(end){return Math.round((Date.parse(end+'T00:00:00Z')-Date.parse($('reference').value+'T00:00:00Z'))/86400000)}
function render(){
 const term=$('search').value.toLocaleLowerCase('pt-BR');
 filtered=source.contratos.filter(r=>(!$('month').value||r.mes===$('month').value)&&(!$('nature').value||r.natureza===$('nature').value)&&(!term||`${r.fornecedor} ${r.fornecedor_id}`.toLocaleLowerCase('pt-BR').includes(term)));
 const valid=filtered.filter(r=>r.valor_centavos!==null&&r.valor_centavos>=0),total=valid.reduce((s,r)=>s+r.valor_centavos,0),bad=filtered.filter(r=>r.qualidade).length;
 const buckets=[0,0,0];for(const r of valid){if(!r.vigencia_valida)continue;const d=days(r.fim);if(d>=0&&d<=90)buckets[d<=30?0:d<=60?1:2]++}
 $('scope').textContent=`${number(filtered.length)} registros no recorte · ${number(filtered.length-valid.length)} com valor excluído das somas · filtros aplicados a todos os indicadores`;
 $('cards').innerHTML=[['Valor global válido',money(total),'Valor informado na coleta'],['Registros PNCP',number(filtered.length),'Chaves únicas no recorte'],['Vencem em até 90 dias',number(buckets.reduce((a,b)=>a+b,0)),'Valor válido e vigência consistente'],['Com alertas de qualidade',number(bad),filtered.length?`${(100*bad/filtered.length).toFixed(1)}% do recorte`:'Sem registros']].map(([label,val,note])=>`<div class="card"><span class="label">${label}</span><strong>${val}</strong><small>${note}</small></div>`).join('');
 const months=Array(12).fill(0);valid.forEach(r=>months[+r.mes.slice(5)-1]+=r.valor_centavos);const max=Math.max(1,...months);
 $('monthly').innerHTML=months.map((v,i)=>`<div class="month" title="${escape(money(v))}"><div class="bar" style="height:${180*v/max}px"></div><span>${['JAN','FEV','MAR','ABR','MAI','JUN','JUL','AGO','SET','OUT','NOV','DEZ'][i]}</span></div>`).join('');
 const suppliers=new Map();for(const r of valid){if(r.fornecedor_id==='NAO_PJ_OU_AUSENTE')continue;const current=suppliers.get(r.fornecedor_id)||{name:r.fornecedor,value:0};current.value+=r.valor_centavos;suppliers.set(r.fornecedor_id,current)}
 $('suppliers').innerHTML=[...suppliers.values()].sort((a,b)=>b.value-a.value).slice(0,6).map(r=>`<div class="supplier"><div class="supplier-head"><span title="${escape(r.name)}">${escape(r.name)}</span><b>${total?(100*r.value/total).toFixed(1):'0.0'}%</b></div><div class="track"><i style="width:${total?100*r.value/total:0}%"></i></div></div>`).join('')||'<p class="muted">Sem fornecedores PJ no recorte.</p>';
 $('expiry').innerHTML=buckets.map((v,i)=>`<div><strong>${number(v)}</strong><small>${['0–30 dias','31–60 dias','61–90 dias'][i]}</small></div>`).join('');
 const labels={valor_invalido:'Valor ausente ou negativo',vigencia_ausente:'Vigência ausente',vigencia_invertida:'Vigência invertida',fornecedor_ausente:'Identificador ausente',natureza_ausente:'Natureza não informada'};
 $('quality').innerHTML=Object.entries(labels).map(([k,label])=>`<div class="quality-row"><span>${label}</span><strong>${number(filtered.filter(r=>r.qualidade.split(';').includes(k)).length)}</strong></div>`).join('');
 filtered.sort((a,b)=>b.publicacao.localeCompare(a.publicacao)||a.id.localeCompare(b.id));page=0;renderTable();
}
function renderTable(){const pages=Math.max(1,Math.ceil(filtered.length/size));page=Math.max(0,Math.min(page,pages-1));$('table').innerHTML=filtered.slice(page*size,(page+1)*size).map(r=>`<tr><td>${escape(r.publicacao)}<small>${escape(r.id)}</small></td><td>${escape(r.fornecedor)}</td><td>${r.valor_centavos===null?'—':money(r.valor_centavos)}</td><td>${escape(r.fim)}</td><td><span class="badge ${r.qualidade?'warn':''}">${r.qualidade?'Revisar':'Sem alerta'}</span></td></tr>`).join('')||'<tr><td colspan="5">Nenhum registro encontrado.</td></tr>';$('tableCount').textContent=`${number(filtered.length)} registros · ordenados por publicação mais recente`;$('page').textContent=`${page+1} / ${pages}`;$('prev').disabled=page===0;$('next').disabled=page>=pages-1}
for(const id of ['month','nature','search','reference'])$(id).addEventListener(id==='search'?'input':'change',render);
$('prev').onclick=()=>{page--;renderTable()};$('next').onclick=()=>{page++;renderTable()};$('reset').onclick=()=>{$('month').value='';$('nature').value='despesa';$('search').value='';$('reference').value=source.meta.config.referencia;render()};
$('download').onclick=()=>{const keys=['id','publicacao','fornecedor_id','fornecedor','valor_centavos','inicio','fim','natureza','qualidade'];const cell=v=>'"'+String(v??'').replace(/^[=+@-]/,"'$&").replace(/"/g,'""')+'"';const csv='\ufeff'+[keys,...filtered.map(r=>keys.map(k=>r[k]))].map(r=>r.map(cell).join(';')).join('\r\n');const url=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'}));const a=document.createElement('a');a.href=url;a.download='radar-recorte.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)};
render();

