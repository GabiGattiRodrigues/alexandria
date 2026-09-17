"""
Gera uma amostra sintetica com o mesmo schema do dataset da Olist.

Serve para dois casos: rodar o projeto inteiro sem precisar baixar o dataset do
Kaggle, e dar ao GitHub Actions um conjunto de dados deterministico para os
testes da CI. Os dados sao inventados e nao devem ser usados para analise.

Uso:
    python scripts/gerar_amostra.py --destino data/sample --pedidos 4000
"""

from __future__ import annotations

import argparse
import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

SEMENTE = 42

ESTADOS = ["SP", "RJ", "MG", "RS", "PR", "SC", "BA", "GO", "PE", "CE"]
CATEGORIAS = [
    "cama_mesa_banho", "beleza_saude", "esporte_lazer", "informatica_acessorios",
    "moveis_decoracao", "utilidades_domesticas", "relogios_presentes", "telefonia",
    "automotivo", "brinquedos",
]
TRADUCAO = {
    "cama_mesa_banho": "bed_bath_table", "beleza_saude": "health_beauty",
    "esporte_lazer": "sports_leisure", "informatica_acessorios": "computers_accessories",
    "moveis_decoracao": "furniture_decor", "utilidades_domesticas": "housewares",
    "relogios_presentes": "watches_gifts", "telefonia": "telephony",
    "automotivo": "auto", "brinquedos": "toys",
}
STATUS = (
    ["delivered"] * 88 + ["shipped"] * 4 + ["canceled"] * 3
    + ["invoiced"] * 2 + ["processing"] * 2 + ["unavailable"]
)
PAGAMENTOS = ["credit_card"] * 74 + ["boleto"] * 19 + ["voucher"] * 5 + ["debit_card"] * 2

INICIO = datetime(2017, 1, 1)
FIM = datetime(2018, 8, 31)


def _id(rnd: random.Random) -> str:
    return "".join(rnd.choices("0123456789abcdef", k=32))


def _escrever(destino: Path, nome: str, colunas: list[str], linhas: list[list]) -> None:
    caminho = destino / nome
    with caminho.open("w", newline="", encoding="utf-8") as f:
        escritor = csv.writer(f)
        escritor.writerow(colunas)
        escritor.writerows(linhas)
    print(f"  [ok]  {nome:<45} {len(linhas):>7,} linhas")


def gerar(destino: Path, n_pedidos: int) -> None:
    rnd = random.Random(SEMENTE)
    destino.mkdir(parents=True, exist_ok=True)

    n_clientes = max(1, int(n_pedidos * 0.85))
    n_produtos = max(1, int(n_pedidos * 0.25))
    n_vendedores = max(1, int(n_pedidos * 0.05))

    # --- clientes -----------------------------------------------------------
    clientes = []
    for _ in range(n_clientes):
        uf = rnd.choice(ESTADOS)
        clientes.append([
            _id(rnd), _id(rnd), f"{rnd.randint(1000, 99999):05d}",
            f"cidade_{uf.lower()}_{rnd.randint(1, 40)}", uf,
        ])
    _escrever(destino, "olist_customers_dataset.csv", [
        "customer_id", "customer_unique_id", "customer_zip_code_prefix",
        "customer_city", "customer_state",
    ], clientes)

    # --- vendedores ---------------------------------------------------------
    vendedores = []
    for _ in range(n_vendedores):
        uf = rnd.choice(ESTADOS)
        vendedores.append([
            _id(rnd), f"{rnd.randint(1000, 99999):05d}",
            f"cidade_{uf.lower()}_{rnd.randint(1, 40)}", uf,
        ])
    _escrever(destino, "olist_sellers_dataset.csv",
              ["seller_id", "seller_zip_code_prefix", "seller_city", "seller_state"],
              vendedores)

    # --- produtos -----------------------------------------------------------
    produtos = []
    for _ in range(n_produtos):
        produtos.append([
            _id(rnd), rnd.choice(CATEGORIAS), rnd.randint(20, 60), rnd.randint(100, 3000),
            rnd.randint(1, 6), rnd.randint(100, 20000), rnd.randint(10, 100),
            rnd.randint(5, 60), rnd.randint(5, 60),
        ])
    _escrever(destino, "olist_products_dataset.csv", [
        "product_id", "product_category_name", "product_name_lenght",
        "product_description_lenght", "product_photos_qty", "product_weight_g",
        "product_length_cm", "product_height_cm", "product_width_cm",
    ], produtos)

    _escrever(destino, "product_category_name_translation.csv",
              ["product_category_name", "product_category_name_english"],
              [[pt, en] for pt, en in TRADUCAO.items()])

    # --- pedidos, itens, pagamentos e avaliacoes ----------------------------
    pedidos, itens, pagamentos, avaliacoes = [], [], [], []
    intervalo = int((FIM - INICIO).total_seconds())

    for _ in range(n_pedidos):
        pedido_id = _id(rnd)
        cliente = rnd.choice(clientes)[0]
        status = rnd.choice(STATUS)
        compra = INICIO + timedelta(seconds=rnd.randint(0, intervalo))
        aprovado = compra + timedelta(hours=rnd.randint(1, 48))
        transportadora = aprovado + timedelta(days=rnd.randint(1, 6))
        estimada = compra + timedelta(days=rnd.randint(8, 35))
        entregue = transportadora + timedelta(days=rnd.randint(1, 25))

        fmt = "%Y-%m-%d %H:%M:%S"
        pedidos.append([
            pedido_id, cliente, status, compra.strftime(fmt),
            aprovado.strftime(fmt) if status != "unavailable" else "",
            transportadora.strftime(fmt) if status in ("delivered", "shipped") else "",
            entregue.strftime(fmt) if status == "delivered" else "",
            estimada.strftime(fmt),
        ])

        for i in range(1, rnd.choices([1, 2, 3, 4], weights=[80, 13, 5, 2])[0] + 1):
            preco = round(rnd.lognormvariate(4.1, 0.8), 2)
            itens.append([
                pedido_id, i, rnd.choice(produtos)[0], rnd.choice(vendedores)[0],
                (transportadora).strftime(fmt), preco,
                round(preco * rnd.uniform(0.05, 0.35), 2),
            ])

        total = round(sum(float(it[5]) + float(it[6]) for it in itens if it[0] == pedido_id), 2)
        tipo = rnd.choice(PAGAMENTOS)
        pagamentos.append([
            pedido_id, 1, tipo,
            rnd.choice([1, 1, 1, 2, 3, 4, 6, 10]) if tipo == "credit_card" else 1,
            total,
        ])

        if status == "delivered" and rnd.random() < 0.85:
            criada = entregue + timedelta(days=1)
            avaliacoes.append([
                _id(rnd), pedido_id,
                rnd.choices([5, 4, 3, 2, 1], weights=[57, 19, 8, 3, 13])[0], "", "",
                criada.strftime("%Y-%m-%d 00:00:00"),
                (criada + timedelta(days=rnd.randint(1, 5))).strftime(fmt),
            ])

    _escrever(destino, "olist_orders_dataset.csv", [
        "order_id", "customer_id", "order_status", "order_purchase_timestamp",
        "order_approved_at", "order_delivered_carrier_date",
        "order_delivered_customer_date", "order_estimated_delivery_date",
    ], pedidos)

    _escrever(destino, "olist_order_items_dataset.csv", [
        "order_id", "order_item_id", "product_id", "seller_id",
        "shipping_limit_date", "price", "freight_value",
    ], itens)

    _escrever(destino, "olist_order_payments_dataset.csv", [
        "order_id", "payment_sequential", "payment_type",
        "payment_installments", "payment_value",
    ], pagamentos)

    _escrever(destino, "olist_order_reviews_dataset.csv", [
        "review_id", "order_id", "review_score", "review_comment_title",
        "review_comment_message", "review_creation_date", "review_answer_timestamp",
    ], avaliacoes)

    # Geolocalizacao entra so com os prefixos usados, para manter o arquivo leve.
    geo = []
    for prefixo in {c[2] for c in clientes} | {v[1] for v in vendedores}:
        geo.append([
            prefixo, round(rnd.uniform(-33.0, -2.0), 6), round(rnd.uniform(-70.0, -35.0), 6),
            f"cidade_{rnd.randint(1, 40)}", rnd.choice(ESTADOS),
        ])
    _escrever(destino, "olist_geolocation_dataset.csv", [
        "geolocation_zip_code_prefix", "geolocation_lat", "geolocation_lng",
        "geolocation_city", "geolocation_state",
    ], geo)


def main() -> None:
    parser = argparse.ArgumentParser(description="Gera amostra sintetica no schema da Olist.")
    parser.add_argument("--destino", default="data/sample", type=Path)
    parser.add_argument("--pedidos", default=4000, type=int)
    args = parser.parse_args()

    print(f"Gerando amostra sintetica em {args.destino}")
    gerar(args.destino, args.pedidos)
    print("\nPronto. Dados ficticios, use apenas para testar a esteira.")


if __name__ == "__main__":
    main()
