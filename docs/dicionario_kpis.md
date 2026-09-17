# Dicionário oficial de KPIs

Este arquivo é a definição de referência das métricas do projeto. Se um número
aparece em um relatório, um dashboard ou na resposta de um agente, ele tem que
corresponder ao que está escrito aqui — e a fonte tem que ser a tabela citada
na linha "Onde vive".

Quando alguém pedir uma métrica nova, ela entra primeiro aqui, depois no modelo
dbt, e só então na ferramenta de visualização. A ordem importa: é o que impede
que a mesma palavra queira dizer duas coisas diferentes em duas telas.

---

## Receita bruta

**Definição.** Soma de `price + freight_value` de todos os itens do pedido.

**Onde vive.** `gold.fct_pedidos.receita_bruta`, agregada em
`gold.agg_kpis_diarios.receita_bruta`.

**Decisões conscientes.**

- Frete entra na receita, porque é dinheiro que entra na plataforma. Quem
  precisa da receita sem frete usa `valor_itens`, que existe na mesma tabela.
- Pedidos cancelados entram na receita bruta. Receita líquida de cancelamento
  seria outra métrica, com outro nome — não a mesma com outro filtro.
- A receita é reconhecida na **data da compra**, não na data de entrega nem na
  data de pagamento.

**O que não é.** Não é `payment_value`. Os dois convivem na fato porque divergem
na origem por vouchers e arredondamento, e essa divergência é informação, não
erro a ser escondido.

---

## Pedidos

**Definição.** Contagem de `pedido_id` distintos com data de compra no período,
independente do status.

**Onde vive.** `gold.agg_kpis_diarios.pedidos`.

**Decisões conscientes.** Cancelados entram. Se saíssem, o denominador de todas
as taxas mudaria de significado conforme o filtro aplicado — e é exatamente
assim que dois relatórios passam a discordar. O cancelamento é acompanhado em
métrica própria.

---

## Ticket médio

**Definição.** `receita_bruta / pedidos` no período.

**Onde vive.** `gold.agg_kpis_diarios.ticket_medio`.

**Decisões conscientes.** O denominador é o pedido. Ticket médio **por cliente**
é outra métrica e vive em `gold.dim_clientes.ticket_medio`. As duas nunca devem
aparecer com o mesmo rótulo na mesma tela.

---

## Clientes

**Definição.** Contagem de `cliente_id` distintos.

**Onde vive.** `gold.dim_clientes`, agregada em `gold.agg_kpis_diarios.clientes`.

**Decisões conscientes.** `cliente_id` é o `customer_unique_id` da origem, que
identifica a pessoa. A Olist também traz `customer_id`, que é uma chave nova a
cada pedido — contar por ela infla a base e é o erro mais comum com este
dataset. A camada silver renomeia os dois campos justamente para tornar a
confusão impossível.

---

## Taxa de cancelamento

**Definição.** Pedidos com status `canceled` sobre o total de pedidos do
período.

**Onde vive.** `gold.agg_kpis_diarios.taxa_cancelamento`.

**Decisões conscientes.** O pedido é contado pela data da compra, não pela data
em que o cancelamento aconteceu. Isso mantém a métrica comparável com as demais
do mesmo dia, ao custo de a taxa de um dia recente ainda poder subir.

---

## Taxa de atraso

**Definição.** Pedidos entregues depois da data estimada sobre o total de
pedidos entregues no período.

**Onde vive.** `gold.agg_kpis_diarios.taxa_atraso`.

**Decisões conscientes.** O denominador são os pedidos **entregues**, não todos
os pedidos: um pedido ainda em trânsito não tem atraso conhecido, e incluí-lo
diluiria a métrica.

---

## Nota média e detratores

**Definição.** Média simples de `review_score`, e a proporção de avaliações com
nota 1 ou 2.

**Onde vive.** `gold.agg_kpis_diarios.nota_media` e `taxa_detratores`.

**Decisões conscientes.** A origem traz mais de uma avaliação para o mesmo
pedido. A camada silver mantém apenas a mais recente, uma vez só, em
`stg_pedido_avaliacoes` — nenhum relatório deduplica por conta própria.

---

## Recência

**Definição.** Dias entre a última compra do cliente e a data de corte do
projeto (`2018-08-31`, configurável em `dbt_project.yml`).

**Onde vive.** `gold.dim_clientes.recencia_dias`.

**Decisões conscientes.** Ancorada na data de corte e não em `current_date`. O
dataset é histórico e fechado: medir contra "hoje" faria a base inteira parecer
inativa e quebraria a reprodutibilidade do projeto ao longo do tempo.

---

## Segmento RFV

**Definição.** Rótulo derivado dos quintis de recência, frequência e valor,
calculados sobre a base inteira na data de corte.

**Onde vive.** `gold.agg_clientes_rfv.segmento_rfv`.

**Regras.**

| Segmento | Condição |
|---|---|
| Campeão | R ≥ 4, F ≥ 4 e V ≥ 4 |
| Leal | R ≥ 4 e F ≥ 3 |
| Novo | R ≥ 4 e F ≤ 2 |
| Promissor | R = 3 e F ≥ 3 |
| Em risco alto valor | R ≤ 2, F ≥ 4 e V ≥ 4 |
| Em risco | R ≤ 2 e F ≥ 3 |
| Hibernando | R ≤ 2 e F ≤ 2 |
| Atenção | demais combinações |

**Decisões conscientes.** As regras vivem no modelo, não na ferramenta de BI.
Segmentação replicada em cada dashboard é a forma mais rápida de "Campeão"
significar uma coisa no relatório de CRM e outra no de marketing.

A recência é invertida na hora do quintil (`6 - ntile(5)`), para que 5 seja
sempre "melhor" nas três dimensões e o score possa ser lido sem tabela auxiliar.
