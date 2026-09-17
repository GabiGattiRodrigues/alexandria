-- Gold: segmentacao RFV. Os quintis sao calculados sobre a base inteira na
-- data de corte, e os nomes dos segmentos sao fixos aqui — nao no BI — para
-- que "Campeao" signifique a mesma coisa em qualquer lugar que o numero apareca.

with clientes as (
    select * from {{ ref('dim_clientes') }}
),

quintis as (
    select
        *,
        -- Recencia invertida: quanto menor o intervalo, maior a nota.
        6 - ntile(5) over (order by recencia_dias)      as r,
        ntile(5) over (order by qtd_pedidos, receita_total) as f,
        ntile(5) over (order by receita_total)          as v
    from clientes
),

classificado as (
    select
        *,
        cast(r as varchar) || cast(f as varchar) || cast(v as varchar) as rfv,
        round((r + f + v) / 3.0, 2)                                    as score_rfv
    from quintis
)

select
    *,
    case
        when r >= 4 and f >= 4 and v >= 4 then 'Campeao'
        when r >= 4 and f >= 3            then 'Leal'
        when r >= 4 and f <= 2            then 'Novo'
        when r = 3  and f >= 3            then 'Promissor'
        when r <= 2 and f >= 4 and v >= 4 then 'Em risco alto valor'
        when r <= 2 and f >= 3            then 'Em risco'
        when r <= 2 and f <= 2            then 'Hibernando'
        else 'Atencao'
    end as segmento_rfv
from classificado
