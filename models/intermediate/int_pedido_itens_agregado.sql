-- Consolida os itens no nivel do pedido. Ephemeral: existe para nao repetir
-- este group by em cada mart e nao vira tabela no banco.

with itens as (
    select * from {{ ref('stg_pedido_itens') }}
)

select
    pedido_id,
    count(*)                            as qtd_itens,
    count(distinct produto_id)          as qtd_produtos_distintos,
    count(distinct vendedor_id)         as qtd_vendedores,
    sum(valor_item)                     as valor_itens,
    sum(valor_frete)                    as valor_frete,
    sum(receita_bruta)                  as receita_bruta,
    max(valor_item)                     as valor_item_maximo
from itens
group by 1
