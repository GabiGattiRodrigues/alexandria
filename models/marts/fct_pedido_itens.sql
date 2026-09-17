-- Gold: grao de item. Serve as analises de produto, categoria e vendedor, que
-- nao podem ser respondidas no grao de pedido sem dupla contagem.

with itens as (
    select * from {{ ref('stg_pedido_itens') }}
),

pedidos as (
    select * from {{ ref('stg_pedidos') }}
),

produtos as (
    select * from {{ ref('stg_produtos') }}
),

vendedores as (
    select * from {{ ref('stg_vendedores') }}
)

select
    i.pedido_id,
    i.item_sequencial,
    {{ dbt_utils.generate_surrogate_key(['i.pedido_id', 'i.item_sequencial']) }} as item_id,
    i.produto_id,
    i.vendedor_id,
    pr.categoria,
    pr.categoria_en,
    v.uf                        as vendedor_uf,
    p.data_compra,
    p.mes_compra,
    p.status_pedido,
    p.foi_entregue,
    i.valor_item,
    i.valor_frete,
    i.receita_bruta
from itens i
inner join pedidos p    on i.pedido_id = p.pedido_id
left join produtos pr   on i.produto_id = pr.produto_id
left join vendedores v  on i.vendedor_id = v.vendedor_id
