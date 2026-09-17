-- Silver: um item de pedido por linha. Preco e frete ja somados em
-- receita_bruta para que "receita" tenha uma definicao so no projeto inteiro.

with origem as (
    select * from {{ source('bronze', 'pedido_itens') }}
),

final as (
    select
        order_id                                as pedido_id,
        cast(order_item_id as integer)          as item_sequencial,
        product_id                              as produto_id,
        seller_id                               as vendedor_id,
        try_cast(nullif(cast(shipping_limit_date as varchar), '') as timestamp) as limite_postagem_em,
        cast(price as decimal(12, 2))           as valor_item,
        cast(freight_value as decimal(12, 2))   as valor_frete,
        cast(price as decimal(12, 2))
            + cast(freight_value as decimal(12, 2)) as receita_bruta
    from origem
)

select * from final
