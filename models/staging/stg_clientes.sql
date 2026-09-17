-- Silver: uma linha por cliente_pedido_id, preservando a chave da pessoa.
-- A traducao das duas chaves esta documentada porque e a fonte mais comum de
-- erro de contagem de clientes neste dataset.

with origem as (
    select * from {{ source('bronze', 'clientes') }}
),

final as (
    select
        customer_id                                 as cliente_pedido_id,
        customer_unique_id                          as cliente_id,
        lpad(cast(customer_zip_code_prefix as varchar), 5, '0') as cep_prefixo,
        lower(trim(customer_city))                  as cidade,
        upper(trim(customer_state))                 as uf
    from origem
)

select * from final
