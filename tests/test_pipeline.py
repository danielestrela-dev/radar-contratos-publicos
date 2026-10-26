import importlib.util, unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('build',Path(__file__).resolve().parents[1]/'scripts/build.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
CFG=dict(orgao_cnpj='123',inicio='20250101',fim='20251231')
def record(**kwargs):
    r=dict(numeroControlePNCP='123-2-1/2025',orgaoEntidade={'cnpj':'123'},dataPublicacaoPncp='2025-01-10',dataVigenciaInicio='2025-01-01',dataVigenciaFim='2025-12-31',valorGlobal=10.15,receita=False,tipoPessoa='PJ',niFornecedor='456',nomeRazaoSocialFornecedor='Empresa',dataAtualizacao='2025-01-10')
    r.update(kwargs);return r
class PipelineTests(unittest.TestCase):
    def test_money(self):
        self.assertEqual(b.cents('10.155'),1016)
        for v in (None,'NaN','Infinity','x',True): self.assertIsNone(b.cents(v))
    def test_latest_and_duplicate(self):
        df,n=b.normalize([record(),record(valorGlobal=20,dataAtualizacao='2025-02-01')],CFG)
        self.assertEqual(n,1);self.assertEqual(len(df),1);self.assertEqual(df.iloc[0].valor_centavos,2000)
    def test_personal_data(self):
        df,_=b.normalize([record(tipoPessoa='PF',niFornecedor='12345678901',nomeRazaoSocialFornecedor='Nome privado')],CFG)
        self.assertNotIn('12345678901',df.to_json());self.assertNotIn('Nome privado',df.to_json())
    def test_bad_values_and_dates(self):
        df,_=b.normalize([record(valorGlobal=-1,dataVigenciaFim='2024-01-01',receita=None,niFornecedor=None)],CFG)
        self.assertEqual(df.iloc[0].vigencia_valida,0)
        self.assertEqual(set(df.iloc[0].qualidade.split(';')),{'valor_invalido','vigencia_invertida','natureza_ausente','fornecedor_ausente'})
    def test_missing_dates_and_money(self):
        df,_=b.normalize([record(valorGlobal=None,dataVigenciaInicio=None)],CFG)
        self.assertTrue(df.valor_centavos.isna().all());self.assertIn('vigencia_ausente',df.iloc[0].qualidade)
    def test_scope_rejected(self):
        for r in (record(orgaoEntidade={'cnpj':'999'}),record(dataPublicacaoPncp='2024-01-01'),record(numeroControlePNCP=None)):
            with self.assertRaises(ValueError): b.normalize([r],CFG)
    def test_receita_preserved(self):
        df,_=b.normalize([record(receita=True)],CFG);self.assertEqual(df.iloc[0].natureza,'receita')
if __name__=='__main__': unittest.main()
