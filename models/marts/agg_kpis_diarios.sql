-- Gold: a serie diaria que alimenta os cards e os graficos do dashboard.
-- Existe para garantir a regra que da nome ao projeto: o numero que o agente
-- responde e o numero que o grafico mostra, porque os dois leem esta tabela.

with pedidos as (
    select * from {{ ref('fct_pedidos') }}
)

select
    data_compra                                                     as data,
    date_trunc('month', data_compra)                                as mes,

    count(distinct pedido_id)                                       as pedidos,
    count(distinct case when foi_entregue then pedido_id end)       as pedidos_entregues,
    count(distinct case when foi_cancelado then pedido_id end)      as pedidos_cancelados,
    count(distinct cliente_id)                                      as clientes,

    sum(receita_bruta)                                              as receita_bruta,
    sum(valor_itens)                                                as receita_itens,
    sum(valor_frete)                                                as receita_frete,
    sum(receita_bruta) / nullif(count(distinct pedido_id), 0)       as ticket_medio,
    sum(qtd_itens)                                                  as itens,

    avg(nota_avaliacao)                                             as nota_media,
    count(case when detrator then 1 end)
        / nullif(count(nota_avaliacao), 0)                          as taxa_detratores,
    avg(dias_ate_entrega)                                           as prazo_medio_entrega_dias,
    count(case when entrega_atrasada then 1 end)
        / nullif(count(distinct case when foi_entregue then pedido_id end), 0) as taxa_atraso,
    count(distinct case when foi_cancelado then pedido_id end)
        / nullif(count(distinct pedido_id), 0)                      as taxa_cancelamento

from pedidos
group by 1, 2
