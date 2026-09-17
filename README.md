# Alexandria

[![dbt build e documentação](https://github.com/GabiGattiRodrigues/alexandria/actions/workflows/dbt.yml/badge.svg)](https://github.com/GabiGattiRodrigues/alexandria/actions/workflows/dbt.yml)
[![Abrir no Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/GabiGattiRodrigues/alexandria/blob/main/notebooks/alexandria_no_colab.ipynb)

**Modelagem em camadas, governança e observabilidade de dados com dbt + DuckDB.**

Alexandria é a camada de dados por trás do
[Dashboard Inteligente](https://dashboardinteligente.streamlit.app). O problema
que ele resolve não é técnico, é de confiança: em quase toda empresa que usa
dados, a mesma métrica aparece com valores diferentes em duas telas, e a
discussão da reunião vira sobre qual número está certo em vez de sobre a
decisão.

A resposta aqui é estrutural. Cada métrica tem **uma** definição, escrita em um
lugar só, materializada em uma camada testada, e consumida de lá por todo mundo
— o gráfico e o agente conversacional inclusive. Se os dois divergirem, o build
quebra antes de chegar na tela.

---

## O que tem dentro

| Camada | O que faz | Materialização |
|---|---|---|
| **Bronze** | Cópia fiel dos CSVs da origem, sem nenhuma regra de negócio. Auditável. | Tabelas carregadas por script |
| **Silver** (`staging` + `intermediate`) | Tipagem, limpeza, deduplicação e padronização de nomes. Uma regra, um lugar. | Views e modelos ephemeral |
| **Gold** (`marts`) | Fatos, dimensões e agregados no vocabulário do negócio. É o que o produto consome. | Tabelas |

**Modelos gold:** `fct_pedidos`, `fct_pedido_itens`, `dim_clientes`,
`dim_produtos`, `agg_kpis_diarios`, `agg_clientes_rfv`.

**Dashboard de observabilidade:** o projeto mede a própria qualidade. O
[dashboard](https://gabigattirodrigues.github.io/alexandria/qualidade.html)
mostra o resultado de cada teste, a cobertura de governança modelo a modelo, o
perfil das tabelas (nulos, cardinalidade, candidatas a chave) e a evolução build
a build. Tudo sai dos metadados que o dbt gera sozinho a cada execução — nenhum
número é digitado à mão. Há uma versão estática, publicada pela esteira, e uma
interativa em Streamlit (`app/dashboard_qualidade.py`).

**75 checagens de qualidade** rodam a cada build: unicidade, integridade
referencial, domínios de valores, faixas numéricas, regras de negócio e três
testes de reconciliação entre camadas — que comparam a receita e a contagem de
pedidos da gold contra a silver e barram qualquer join que duplique linha.

---

## Decisões que valem explicar

**A camada bronze não tem modelo dbt.** Ela é carregada por script e declarada
como `source`. Transformar dado cru dentro do dbt apaga a fronteira entre "o que
chegou" e "o que eu fiz com ele", que é justamente a fronteira que torna um
problema auditável.

**Recência é medida contra uma data de corte, não contra `current_date`.** O
dataset é histórico e fechado em agosto de 2018. Ancorar em "hoje" faria a base
inteira parecer inativa e o projeto deixaria de ser reproduzível daqui a alguns
anos.

**Pedidos cancelados entram na contagem de pedidos.** Se saíssem, o denominador
de todas as taxas mudaria de significado conforme o filtro aplicado — e é assim
que dois relatórios passam a discordar sem que ninguém perceba.

**A segmentação RFV vive no modelo, não no BI.** Regra de negócio replicada em
cada ferramenta é a forma mais rápida de "Campeão" significar uma coisa no
relatório de CRM e outra no de marketing.

**`try_cast` em vez de `cast` na fronteira bronze → silver.** Uma data
malformada entra como nulo e é acusada pelo teste da camada, em vez de derrubar
o build inteiro e deixar o dashboard sem atualizar.

A racional completa de cada métrica está em
[`docs/dicionario_kpis.md`](docs/dicionario_kpis.md).

---

## Como verificar que isto roda mesmo

Três caminhos, do mais rápido ao mais completo. Nenhum deles depende de você
acreditar no que está escrito aqui.

**1. O selo do GitHub Actions (10 segundos).** O selo no topo deste arquivo é
servido pelo GitHub, não por mim. O projeto é reconstruído do zero a cada push:
se um teste quebrar, ele fica vermelho sozinho.

**2. Rodar no navegador (2 minutos).** O
[notebook no Colab](https://colab.research.google.com/github/GabiGattiRodrigues/alexandria/blob/main/notebooks/alexandria_no_colab.ipynb)
clona o repositório, constrói as três camadas e executa os 75 testes na máquina
do Google, sem instalar nada. No final ele duplica uma linha na bronze de
propósito, para você ver o teste de reconciliação falhar.

**3. Rodar na sua máquina (5 minutos).** No Windows, dois cliques em
`rodar.bat` — ele instala, constrói, testa e diz no fim se está liberado para
commitar. No macOS e no Linux, `./rodar.sh`. Ou os comandos abaixo, um a um.
O passo a passo completo está em [`PRIMEIROS-PASSOS.md`](PRIMEIROS-PASSOS.md).

O placar de cada execução fica em `site/resultados.json`, gerado por
`scripts/resumo_testes.py` a partir de `target/run_results.json` — o artefato
que o próprio dbt escreve. É esse arquivo que alimenta os gráficos da página do
case, então nenhum número publicado é digitado à mão.

---

## Como rodar

Não precisa de nuvem, conta, servidor nem cartão de crédito. O banco é um
arquivo local.

```bash
git clone https://github.com/GabiGattiRodrigues/alexandria.git
cd alexandria

pip install -r requirements.txt
dbt deps

# Opção A: amostra sintética, sem baixar nada
python scripts/gerar_amostra.py --destino data/sample --pedidos 4000
python scripts/carregar_bronze.py --origem data/sample

# Opção B: dataset real da Olist
#   baixe em kaggle.com/datasets/olistbr/brazilian-ecommerce
#   e descompacte os CSVs em data/raw/
python scripts/carregar_bronze.py --origem data/raw

dbt build --profiles-dir .
dbt docs generate --profiles-dir .

# metadados de qualidade e dashboard estatico
python scripts/resumo_testes.py
python scripts/coletar_qualidade.py
python scripts/gerar_dashboard.py

# dashboard interativo (opcional)
streamlit run app/dashboard_qualidade.py
```

No Windows, `rodar.bat` faz tudo isso com dois cliques.

`dbt docs serve` abre o catálogo com o **grafo de linhagem clicável**: dá para
partir de qualquer KPI e navegar até a coluna do CSV de origem que o alimenta.

---

## Esteira automatizada

O workflow em `.github/workflows/dbt.yml` roda a cada push: reconstrói o projeto
do zero, executa as 75 checagens, publica a documentação no GitHub Pages e
escreve o placar em `resultados.json`, ao lado da documentação. Um teste que
falha marca o commit como quebrado — mesma lógica de um pipeline de produção,
sem custo de infraestrutura.

---

## Stack

dbt Core · DuckDB · Python · Streamlit · GitHub Actions · GitHub Pages

Dados: [Brazilian E-Commerce Public Dataset by
Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) (licença
CC BY-NC-SA 4.0). Os CSVs não são versionados neste repositório.

---

Feito por [Gabriela Gatti
Rodrigues](https://www.linkedin.com/in/gabriela-gatti-rodrigues) ·
[portfólio](https://gabigattirodrigues.github.io)
