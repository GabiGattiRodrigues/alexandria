-- Silver: uma avaliacao por pedido.
-- A origem repete review_id e pode ter mais de uma avaliacao para o mesmo
-- pedido. A deduplicacao acontece aqui, mantendo a avaliacao mais recente,
-- para que nenhum mart precise reinventar esse criterio.

with origem as (
    select * from {{ source('bronze', 'pedido_avaliacoes') }}
),

tipado as (
    select
        review_id                                       as avaliacao_id,
        order_id                                        as pedido_id,
        cast(review_score as integer)                   as nota,
        try_cast(nullif(cast(review_creation_date as varchar), '') as timestamp) as avaliada_em,
        try_cast(nullif(cast(review_answer_timestamp as varchar), '') as timestamp) as respondida_em
    from origem
),

deduplicado as (
    select
        *,
        row_number() over (
            partition by pedido_id
            order by avaliada_em desc, avaliacao_id
        ) as _ordem
    from tipado
)

select
    avaliacao_id,
    pedido_id,
    nota,
    avaliada_em,
    respondida_em,
    nota >= 4                       as promotor,
    nota <= 2                       as detrator
from deduplicado
where _ordem = 1
