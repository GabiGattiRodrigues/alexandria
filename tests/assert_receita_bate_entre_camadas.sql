-- Teste de reconciliacao entre camadas.
--
-- A receita total da fato de pedidos tem que ser igual a soma dos itens na
-- silver. Se um join da gold duplicar linha, este teste quebra antes de o
-- numero chegar no dashboard. Tolerancia de um centavo para arredondamento.

with fato as (
    select sum(receita_bruta) as total from {{ ref('fct_pedidos') }}
),

silver as (
    select sum(receita_bruta) as total from {{ ref('stg_pedido_itens') }}
)

select
    fato.total  as total_gold,
    silver.total as total_silver,
    abs(fato.total - silver.total) as diferenca
from fato
cross join silver
where abs(fato.total - silver.total) > 0.01
