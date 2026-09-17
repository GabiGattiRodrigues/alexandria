-- Consolida as parcelas no nivel do pedido, guardando o meio de pagamento
-- predominante (o de maior valor) para analise de mix.

with pagamentos as (
    select * from {{ ref('stg_pedido_pagamentos') }}
),

ranqueado as (
    select
        *,
        row_number() over (
            partition by pedido_id
            order by valor_pago desc, meio_pagamento
        ) as _ordem
    from pagamentos
)

select
    pedido_id,
    sum(valor_pago)                                             as valor_pago,
    max(qtd_parcelas)                                           as qtd_parcelas,
    count(*)                                                    as qtd_pagamentos,
    max(case when _ordem = 1 then meio_pagamento end)           as meio_pagamento_principal
from ranqueado
group by 1
