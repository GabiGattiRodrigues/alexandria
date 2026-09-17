-- Silver: cadastro de vendedores do marketplace.

with origem as (
    select * from {{ source('bronze', 'vendedores') }}
),

final as (
    select
        seller_id                                   as vendedor_id,
        lpad(cast(seller_zip_code_prefix as varchar), 5, '0') as cep_prefixo,
        lower(trim(seller_city))                    as cidade,
        upper(trim(seller_state))                   as uf
    from origem
)

select * from final
