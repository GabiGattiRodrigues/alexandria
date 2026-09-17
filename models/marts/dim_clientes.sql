-- Gold: uma linha por pessoa (cliente_id), nao por pedido.
-- Esta e a tabela que responde "quantos clientes temos" — a contagem por
-- cliente_pedido_id, que a origem chama de customer_id, sempre superestima.

with pedidos as (
    select * from {{ ref('fct_pedidos') }}
),

por_cliente as (
    select
        cliente_id,
        min(data_compra)                                        as primeira_compra,
        max(data_compra)                                        as ultima_compra,
        count(distinct pedido_id)                               as qtd_pedidos,
        count(distinct case when foi_entregue then pedido_id end) as qtd_pedidos_entregues,
        sum(receita_bruta)                                      as receita_total,
        avg(receita_bruta)                                      as ticket_medio,
        avg(nota_avaliacao)                                     as nota_media,
        max_by(cliente_uf, data_compra)                         as uf,
        max_by(cliente_cidade, data_compra)                     as cidade,
        max_by(meio_pagamento_principal, data_compra)           as meio_pagamento_recente
    from pedidos
    where cliente_id is not null
    group by 1
)

select
    *,
    date_diff('day', ultima_compra, date '{{ var("data_corte") }}')  as recencia_dias,
    date_diff('day', primeira_compra, ultima_compra)                 as tempo_de_vida_dias,
    qtd_pedidos > 1                                                  as e_recorrente,
    date_diff('day', ultima_compra, date '{{ var("data_corte") }}')
        <= {{ var('janela_ativo_dias') }}                            as esta_ativo
from por_cliente
