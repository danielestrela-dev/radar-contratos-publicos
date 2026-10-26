-- Uma linha por chave PNCP; dinheiro em centavos inteiros.
DROP VIEW IF EXISTS vw_mensal;
CREATE VIEW vw_mensal AS SELECT mes, COUNT(*) AS registros, SUM(valor_centavos) AS valor_centavos
FROM contratos WHERE natureza='despesa' AND valor_centavos>=0 GROUP BY mes ORDER BY mes;
DROP VIEW IF EXISTS vw_fornecedores;
CREATE VIEW vw_fornecedores AS
WITH elegiveis AS (SELECT * FROM contratos WHERE natureza='despesa' AND valor_centavos>=0),
totais AS (SELECT fornecedor_id,MAX(fornecedor) AS fornecedor,COUNT(*) AS registros,SUM(valor_centavos) AS valor_centavos
FROM elegiveis WHERE fornecedor_id<>'NAO_PJ_OU_AUSENTE' GROUP BY fornecedor_id)
SELECT *,ROUND(100.0*valor_centavos/NULLIF((SELECT SUM(valor_centavos) FROM elegiveis),0),2) AS participacao_pct,
DENSE_RANK() OVER(ORDER BY valor_centavos DESC) AS posicao FROM totais ORDER BY valor_centavos DESC;
DROP VIEW IF EXISTS vw_qualidade;
CREATE VIEW vw_qualidade AS SELECT CASE WHEN qualidade='' THEN 'sem_alerta' ELSE qualidade END AS alertas,
COUNT(*) AS registros FROM contratos GROUP BY qualidade;
