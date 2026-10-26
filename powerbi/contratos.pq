let
    // Substitua pelo caminho local do CSV exportado.
    Caminho = "C:\dados\radar-contratos-publicos\results\contratos.csv",
    Fonte = Csv.Document(File.Contents(Caminho),[Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Cabecalhos = Table.PromoteHeaders(Fonte,[PromoteAllScalars=true]),
    Tipos = Table.TransformColumnTypes(Cabecalhos,{{"id",type text},{"publicacao",type date},{"mes",type text},{"inicio",type date},{"fim",type date},{"fornecedor_id",type text},{"fornecedor",type text},{"tipo_pessoa",type text},{"valor_centavos",Int64.Type},{"natureza",type text},{"tipo",type text},{"uf",type text},{"qualidade",type text},{"vigencia_valida",Int64.Type}},"en-US")
in
    Tipos
