"""
Ingestao da camada bronze.

Le os CSVs do dataset publico da Olist e grava cada arquivo como uma tabela no
schema `bronze` do DuckDB, sem nenhuma transformacao: os tipos vem como o
DuckDB inferiu e os nomes de coluna continuam os da origem. Toda a limpeza
acontece depois, em dbt, para que a camada bronze continue sendo uma copia
auditavel do que chegou.

Uso:
    python scripts/carregar_bronze.py
    python scripts/carregar_bronze.py --origem data/sample --banco alexandria_ci.duckdb
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import duckdb

# Nome do arquivo na origem -> nome da tabela na bronze.
TABELAS = {
    "olist_customers_dataset.csv": "clientes",
    "olist_geolocation_dataset.csv": "geolocalizacao",
    "olist_order_items_dataset.csv": "pedido_itens",
    "olist_order_payments_dataset.csv": "pedido_pagamentos",
    "olist_order_reviews_dataset.csv": "pedido_avaliacoes",
    "olist_orders_dataset.csv": "pedidos",
    "olist_products_dataset.csv": "produtos",
    "olist_sellers_dataset.csv": "vendedores",
    "product_category_name_translation.csv": "categoria_traducao",
}


def carregar(origem: Path, banco: Path) -> int:
    if not origem.is_dir():
        sys.exit(
            f"Pasta de origem nao encontrada: {origem}\n"
            "Baixe o dataset da Olist no Kaggle e descompacte em data/raw/, "
            "ou rode scripts/gerar_amostra.py para criar dados de exemplo."
        )

    con = duckdb.connect(str(banco))
    con.execute("CREATE SCHEMA IF NOT EXISTS bronze")

    carregadas = 0
    for arquivo, tabela in TABELAS.items():
        caminho = origem / arquivo
        if not caminho.exists():
            print(f"  [pulado]  {arquivo} nao encontrado")
            continue

        con.execute(f"DROP TABLE IF EXISTS bronze.{tabela}")
        con.execute(
            f"""
            CREATE TABLE bronze.{tabela} AS
            SELECT
                *,
                '{arquivo}'          AS _arquivo_origem,
                current_localtimestamp() AS _carregado_em
            FROM read_csv_auto(?, header = true, sample_size = -1)
            """,
            [str(caminho)],
        )
        linhas = con.execute(f"SELECT count(*) FROM bronze.{tabela}").fetchone()[0]
        print(f"  [ok]      bronze.{tabela:<20} {linhas:>9,} linhas")
        carregadas += 1

    con.close()
    return carregadas


def main() -> None:
    parser = argparse.ArgumentParser(description="Carrega os CSVs da Olist na camada bronze.")
    parser.add_argument("--origem", default="data/raw", type=Path, help="pasta com os CSVs")
    parser.add_argument("--banco", default="alexandria.duckdb", type=Path, help="arquivo DuckDB")
    args = parser.parse_args()

    print(f"Carregando bronze de {args.origem} para {args.banco}")
    total = carregar(args.origem, args.banco)
    print(f"\n{total} tabela(s) carregada(s) no schema bronze.")
    if total == 0:
        sys.exit("Nenhum arquivo foi encontrado na origem.")


if __name__ == "__main__":
    main()
