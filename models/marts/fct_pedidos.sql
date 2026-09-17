-- Gold: a tabela-fato central do projeto. Um pedido por linha, ja com valores,
-- pagamento, avaliacao e cliente resolvidos. Toda metrica de pedido do
-- Dashboard Inteligente sai daqui — e so daqui.

with pedidos as (
    select * from {{ ref('stg_pedidos') }}
),

clientes as (
    select * from {{ ref('stg_clientes') }}
),

itens as (
    select * from {{ ref('int_pedido_itens_agregado') }}
),

pagamentos as (
    select * from {{ ref('int_pedido_pagamentos_agregado') }}
),

avaliacoes as (
    select * from {{ ref('stg_pedido_avaliacoes') }}
)

select
    p.pedido_id,
    c.cliente_id,
    p.cliente_pedido_id,
    c.uf                                        as cliente_uf,
    c.cidade                                    as cliente_cidade,

    p.status_pedido,
    p.foi_entregue,
    p.foi_cancelado,
    p.data_compra,
    p.mes_compra,
    p.comprado_em,
    p.entregue_em,
    p.entrega_estimada_em,
    p.dias_ate_entrega,
    p.dias_de_atraso,
    coalesce(p.dias_de_atraso > 0, false)       as entrega_atrasada,

    coalesce(i.qtd_itens, 0)                    as qtd_itens,
    coalesce(i.qtd_produtos_distintos, 0)       as qtd_produtos_distintos,
    coalesce(i.valor_itens, 0)                  as valor_itens,
    coalesce(i.valor_frete, 0)                  as valor_frete,
    coalesce(i.receita_bruta, 0)                as receita_bruta,

    pg.valor_pago,
    pg.qtd_parcelas,
    pg.meio_pagamento_principal,

    a.nota                                      as nota_avaliacao,
    a.promotor,
    a.detrator

from pedidos p
left join clientes c    on p.cliente_pedido_id = c.cliente_pedido_id
left join itens i       on p.pedido_id = i.pedido_id
left join pagamentos pg on p.pedido_id = pg.pedido_id
left join avaliacoes a  on p.pedido_id = a.pedido_id
