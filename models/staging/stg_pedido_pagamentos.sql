-- Silver: uma linha por parcela de pagamento.

with origem as (
    select * from {{ source('bronze', 'pedido_pagamentos') }}
),

final as (
    select
        order_id                                    as pedido_id,
        cast(payment_sequential as integer)         as pagamento_sequencial,
        lower(trim(payment_type))                   as meio_pagamento,
        cast(payment_installments as integer)       as qtd_parcelas,
        cast(payment_value as decimal(12, 2))       as valor_pago
    from origem
)

select * from final
