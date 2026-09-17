#!/usr/bin/env bash
# Equivalente do rodar.bat para macOS e Linux: verificacao local antes do commit.
set -uo pipefail
cd "$(dirname "$0")"

echo "=================================================="
echo "  ALEXANDRIA - verificacao local antes do commit"
echo "=================================================="

[ -d .venv ] || python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate

pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
dbt deps

if [ -f data/raw/olist_orders_dataset.csv ]; then
  ORIGEM=data/raw
  echo "Usando o dataset real da Olist."
else
  echo "Dataset real nao encontrado. Gerando amostra sintetica."
  python scripts/gerar_amostra.py --destino data/sample --pedidos 4000
  ORIGEM=data/sample
fi

python scripts/carregar_bronze.py --origem "$ORIGEM"

if ! dbt build --profiles-dir .; then
  echo
  echo "=================================================="
  echo "  ALGUM TESTE FALHOU - NAO SUBA AINDA"
  echo "=================================================="
  echo "O detalhe esta acima e em target/run_results.json."
  exit 1
fi

dbt docs generate --profiles-dir .
python scripts/resumo_testes.py

cat <<'FIM'

==================================================
  TUDO PASSOU. LIBERADO PARA SUBIR PRO GITHUB.
==================================================

O que rodou aqui e o mesmo que o GitHub Actions repete no push.

Para subir:
    git add .
    git commit -m "Alexandria: camadas, testes e documentacao"
    git push

FIM

read -r -p "Abrir a documentacao com o grafo de linhagem? [s/N] " resposta
case "$resposta" in
  [sS]*) dbt docs serve --profiles-dir . ;;
  *) echo "Ok. Rode 'dbt docs serve --profiles-dir .' quando quiser." ;;
esac
