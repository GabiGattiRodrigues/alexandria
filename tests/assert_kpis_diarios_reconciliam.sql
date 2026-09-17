-- Teste que sustenta a promessa do produto: o agregado diario que o dashboard
-- le tem que reproduzir exatamente a fato que o agente consulta. Qualquer
-- divergencia aqui e a divergencia que o usuario veria na tela.

with agregado as (
    select
        sum(pedidos)        as pedidos,
        sum(receita_bruta)  as receita
    from {{ ref('agg_kpis_diarios') }}
),

fato as (
    select
        count(distinct pedido_id) as pedidos,
        sum(receita_bruta)        as receita
    from {{ ref('fct_pedidos') }}
)

select
    agregado.pedidos as pedidos_agregado,
    fato.pedidos     as pedidos_fato,
    agregado.receita as receita_agregado,
    fato.receita     as receita_fato
from agregado
cross join fato
where agregado.pedidos <> fato.pedidos
   or abs(agregado.receita - fato.receita) > 0.01
