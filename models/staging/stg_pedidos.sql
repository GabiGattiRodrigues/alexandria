-- Silver: um pedido por linha, com tipos corrigidos e nomes em portugues.
-- try_cast e proposital: se a origem mandar uma data malformada, a linha entra
-- com NULL e o teste da camada acusa, em vez de o build inteiro cair.
-- Regras aplicadas aqui:
--   * timestamps vazios da origem viram NULL de verdade;
--   * o prazo de entrega e a comparacao com o estimado ja saem calculados,
--     para que ninguem refaca essa conta de um jeito diferente depois.

with origem as (
    select * from {{ source('bronze', 'pedidos') }}
),

renomeado as (
    select
        order_id                                            as pedido_id,
        customer_id                                         as cliente_pedido_id,
        lower(trim(order_status))                           as status_pedido,
        try_cast(nullif(cast(order_purchase_timestamp as varchar), '') as timestamp) as comprado_em,
        try_cast(nullif(cast(order_approved_at as varchar), '') as timestamp) as aprovado_em,
        try_cast(nullif(cast(order_delivered_carrier_date as varchar), '') as timestamp) as postado_em,
        try_cast(nullif(cast(order_delivered_customer_date as varchar), '') as timestamp) as entregue_em,
        try_cast(nullif(cast(order_estimated_delivery_date as varchar), '') as timestamp) as entrega_estimada_em
    from origem
),

final as (
    select
        *,
        cast(comprado_em as date)                           as data_compra,
        date_trunc('month', comprado_em)                    as mes_compra,
        status_pedido = 'delivered'                         as foi_entregue,
        status_pedido = 'canceled'                          as foi_cancelado,
        date_diff('day', comprado_em, entregue_em)          as dias_ate_entrega,
        date_diff('day', entrega_estimada_em, entregue_em)  as dias_de_atraso
    from renomeado
)

select * from final
