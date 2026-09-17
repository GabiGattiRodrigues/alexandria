-- Regra de negocio: nenhum cliente pode ter compra depois da data de corte do
-- dataset. Se aparecer, houve erro de carga ou de fuso na ingestao.

select
    cliente_id,
    ultima_compra
from {{ ref('dim_clientes') }}
where ultima_compra > date '{{ var("data_corte") }}'
