-- Silver: catalogo de produtos com categoria tratada e traduzida.
-- Produto sem categoria na origem vira 'nao_informado' em vez de NULL, para
-- que ele nao suma silenciosamente de um group by.

with produtos as (
    select * from {{ source('bronze', 'produtos') }}
),

traducao as (
    select * from {{ source('bronze', 'categoria_traducao') }}
),

final as (
    select
        p.product_id                                        as produto_id,
        coalesce(nullif(trim(p.product_category_name), ''), 'nao_informado') as categoria,
        coalesce(nullif(trim(t.product_category_name_english), ''), 'not_informed') as categoria_en,
        cast(p.product_weight_g as integer)                 as peso_g,
        cast(p.product_photos_qty as integer)               as qtd_fotos,
        cast(p.product_length_cm as integer)
            * cast(p.product_height_cm as integer)
            * cast(p.product_width_cm as integer)           as volume_cm3
    from produtos p
    left join traducao t
        on p.product_category_name = t.product_category_name
)

select * from final
