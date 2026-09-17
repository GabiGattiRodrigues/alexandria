-- Gold: produto com os numeros de desempenho ja anexados, para que analises de
-- catalogo nao precisem refazer o join com a fato toda vez.

with produtos as (
    select * from {{ ref('stg_produtos') }}
),

desempenho as (
    select
        produto_id,
        count(*)                        as qtd_itens_vendidos,
        count(distinct pedido_id)       as qtd_pedidos,
        sum(receita_bruta)              as receita_total,
        avg(valor_item)                 as preco_medio,
        min(data_compra)                as primeira_venda,
        max(data_compra)                as ultima_venda
    from {{ ref('fct_pedido_itens') }}
    group by 1
)

select
    p.produto_id,
    p.categoria,
    p.categoria_en,
    p.peso_g,
    p.qtd_fotos,
    p.volume_cm3,
    coalesce(d.qtd_itens_vendidos, 0)   as qtd_itens_vendidos,
    coalesce(d.qtd_pedidos, 0)          as qtd_pedidos,
    coalesce(d.receita_total, 0)        as receita_total,
    d.preco_medio,
    d.primeira_venda,
    d.ultima_venda,
    coalesce(d.qtd_itens_vendidos, 0) = 0 as nunca_vendido
from produtos p
left join desempenho d on p.produto_id = d.produto_id
