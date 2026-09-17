{% docs pedido_id %}
Identificador unico do pedido. Chave primaria em `stg_pedidos` e em
`fct_pedidos`, e a chave de junção usada em toda a camada gold.
{% enddocs %}

{% docs cliente_pedido_id %}
Chave que a origem chama de `customer_id`. **Nao identifica a pessoa**: a Olist
gera uma chave nova a cada pedido. Serve so para ligar o pedido ao cadastro.
Contar clientes por este campo e o erro mais comum com esta base.
{% enddocs %}

{% docs cliente_id %}
Identificador da pessoa (`customer_unique_id` na origem). E a chave correta
para contar clientes, medir recorrencia e calcular CLV.
{% enddocs %}

{% docs receita_bruta %}
Valor do item somado ao frete rateado (`price + freight_value`).

Decisao consciente do projeto: receita inclui frete, porque e o valor que entra
na plataforma. Quem precisa da receita sem frete usa `valor_itens`. Nenhum
relatorio deve recalcular receita por conta propria — se precisar de outro
corte, ele nasce aqui.
{% enddocs %}

{% docs recencia_dias %}
Dias entre a ultima compra do cliente e a data de corte do projeto
(variavel `data_corte`, hoje 2018-08-31).

Usa a data de corte e nao `current_date` de proposito: o dataset e historico e
fechado, entao ancorar em "hoje" faria toda a base parecer inativa e quebraria
a comparacao daqui a alguns anos.
{% enddocs %}

{% docs kpi_pedidos %}
Contagem de pedidos distintos com data de compra no periodo, **independente do
status**. Cancelados entram nesta contagem e sao acompanhados separadamente em
`taxa_cancelamento` — assim a base de comparacao nunca muda de significado no
meio de uma analise.
{% enddocs %}

{% docs kpi_ticket_medio %}
Receita bruta dividida por pedidos distintos do periodo.

O denominador e o pedido, nao o cliente nem o item. Ticket por cliente e uma
metrica diferente e vive em `dim_clientes.ticket_medio`.
{% enddocs %}

{% docs kpi_taxa_cancelamento %}
Pedidos com status `canceled` sobre o total de pedidos do periodo, sempre pela
data de compra do pedido — e nao pela data em que o cancelamento aconteceu.
{% enddocs %}

{% docs segmento_rfv %}
Rotulo de negocio derivado dos quintis de recencia, frequencia e valor.

Segmentos possiveis: Campeao, Leal, Novo, Promissor, Em risco alto valor,
Em risco, Hibernando e Atencao. As regras estao em `agg_clientes_rfv` e sao a
unica definicao valida — nenhuma ferramenta de BI deve reimplementar esta
classificacao.
{% enddocs %}
