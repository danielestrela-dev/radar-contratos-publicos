# Montagem no Power BI Desktop

Esta pasta contém material de importação, não um arquivo PBIX pronto. O painel funcional entregue está em `docs/index.html`. As medidas abaixo precisam ser criadas e conferidas no Power BI Desktop antes da publicação.

1. Obter dados → Consulta em branco → Editor Avançado. Cole `contratos.pq`, ajuste `Caminho` para o CSV em `results/` e nomeie a consulta **Contratos**. Fornecedor_id deve permanecer texto.
2. Crie as medidas de `medidas.dax` individualmente. Crie **Referencia** como tabela calculada desconectada, sem relacionamento. Selecione 26/10/2026 em um segmentador de seleção única.
3. Aplique `natureza = despesa` como filtro da página. Não aplique filtro de qualidade global: isso alteraria a contagem de registros e alertas.
4. Monte cartões: Registros PNCP, Valor global valido, Vencem ate 90 dias e Percentual com alertas.
5. Colunas: `mes` no eixo, Valor global valido no valor. Classifique mes crescente.
6. Ranking: fornecedor no eixo, Valor global valido no valor; filtre tipo_pessoa = PJ e fornecedor_id diferente de NAO_PJ_OU_AUSENTE apenas nesse visual. Use top 10. Adicione Participacao fornecedor ao tooltip; o denominador inclui o valor válido de não-PJ.
7. Tabela de revisão: id, fornecedor, publicacao, fim, valor_centavos e qualidade. Não apresente centavos como reais: use medida de valor ou uma coluna dividida por 100.
8. Segmentadores: mes e fornecedor. Tema sugerido: fundo #0C151B, cartões #14212A, destaque #A8E6BF, texto #EDF4F3.
9. Confira os totais contra o painel HTML no mesmo filtro e data de referência. Salve o PBIX localmente.

Os vencimentos dependem das datas informadas, sem garantir situação ativa. Valor global não é pagamento. Consulte `METRICAS.md` antes de interpretar.
