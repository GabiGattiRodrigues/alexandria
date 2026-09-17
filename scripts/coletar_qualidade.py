"""
Coleta de observabilidade de dados.

Junta em um unico arquivo tudo o que o dashboard de qualidade precisa:

  1. resultado dos testes  -> target/run_results.json
  2. cobertura de governanca -> target/manifest.json (teste e descricao por
     modelo e por coluna)
  3. perfil dos dados      -> queries no proprio DuckDB (nulos, cardinalidade,
     duplicidade, volumetria)
  4. historico por build   -> site/historico.jsonl, uma linha por execucao

Os tres primeiros sao metadados que o dbt ja produz de graca a cada execucao —
dado sobre o dado. O quarto e o unico que precisa ser acumulado, por isso vive
em um arquivo append-only versionado junto do projeto.

O dashboard em Streamlit e a pagina estatica leem os dois arquivos gerados
aqui. Uma coleta, duas superficies: a mesma regra que o projeto aplica as
metricas de negocio, aplicada a si mesmo.

Uso:
    python scripts/coletar_qualidade.py
    python scripts/coletar_qualidade.py --banco alexandria.duckdb --sem-perfil
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent))
from resumo_testes import camada_do_no, resumir  # noqa: E402

# Quantos builds o historico guarda. O suficiente para mostrar tendencia sem
# o arquivo crescer para sempre.
HISTORICO_MAXIMO = 120

# Camadas perfiladas. A bronze fica de fora de proposito: ela e copia da
# origem, e medir qualidade nela seria medir o fornecedor, nao o projeto.
CAMADAS_PERFILADAS = ("silver", "gold")


# ---------------------------------------------------------------------------
# 1 e 2. Testes e cobertura, a partir dos artefatos do dbt
# ---------------------------------------------------------------------------

def _pasta_para_camada(caminho: str) -> str:
    if caminho.startswith("marts/"):
        return "gold"
    if caminho.startswith(("staging/", "intermediate/")):
        return "silver"
    return "outros"


def detalhar_testes(run: dict, manifest: dict) -> list[dict]:
    """Uma linha por teste executado, com o alvo e o resultado."""
    linhas = []
    for resultado in run["results"]:
        no = manifest["nodes"].get(resultado["unique_id"])
        if not no or no["resource_type"] != "test":
            continue

        meta = no.get("test_metadata") or {}
        kwargs = meta.get("kwargs") or {}
        alvo = kwargs.get("model") or ""
        alvo = alvo.replace("{{ get_where_subquery(ref('", "").replace("')) }}", "")
        alvo = alvo.replace("{{ get_where_subquery(source('", "").replace("', '", ".")

        linhas.append({
            "nome": no["name"],
            "tipo": meta.get("name") or "singular",
            "camada": camada_do_no(no, manifest),
            "alvo": alvo or "—",
            "coluna": kwargs.get("column_name") or "",
            "severidade": (no.get("config") or {}).get("severity", "error"),
            "status": resultado["status"],
            "violacoes": resultado.get("failures") or 0,
            "duracao_s": round(float(resultado.get("execution_time") or 0), 3),
        })
    return sorted(linhas, key=lambda linha: (linha["status"] == "pass", linha["camada"], linha["nome"]))


def detalhar_cobertura(manifest: dict) -> list[dict]:
    """Uma linha por modelo, dizendo o que esta coberto e o que nao esta."""
    testes = [n for n in manifest["nodes"].values() if n["resource_type"] == "test"]

    testes_por_no: dict[str, list[dict]] = {}
    for t in testes:
        for dep in t.get("depends_on", {}).get("nodes", []):
            testes_por_no.setdefault(dep, []).append(t)

    linhas = []
    for no in manifest["nodes"].values():
        if no["resource_type"] != "model":
            continue

        colunas = no.get("columns") or {}
        meus_testes = testes_por_no.get(no["unique_id"], [])

        colunas_testadas = {
            (t.get("test_metadata") or {}).get("kwargs", {}).get("column_name")
            for t in meus_testes
        }
        colunas_testadas.discard(None)

        # Grao provado por unicidade de uma coluna OU de uma combinacao delas —
        # em tabela de grao composto, exigir `unique` numa coluna so seria errado.
        TESTES_DE_GRAO = {"unique", "unique_combination_of_columns"}
        tem_grao = any(
            (t.get("test_metadata") or {}).get("name") in TESTES_DE_GRAO for t in meus_testes
        )

        linhas.append({
            "nome": no["name"],
            "camada": _pasta_para_camada(no.get("path", "")),
            "materializacao": no["config"]["materialized"],
            "descrito": bool((no.get("description") or "").strip()),
            "colunas_declaradas": len(colunas),
            "colunas_documentadas": sum(
                1 for c in colunas.values() if (c.get("description") or "").strip()
            ),
            "colunas_testadas": len(colunas_testadas),
            "testes": len(meus_testes),
            "tem_teste_de_grao": tem_grao,
        })
    return sorted(linhas, key=lambda linha: (linha["camada"], linha["nome"]))


# ---------------------------------------------------------------------------
# 3. Perfil dos dados, direto do DuckDB
# ---------------------------------------------------------------------------

def _relacao(no: dict) -> tuple[str, str]:
    schema = no["config"].get("schema") or no.get("schema") or "main"
    return schema, (no["config"].get("alias") or no["name"])


def perfilar(banco: Path, manifest: dict) -> list[dict]:
    """Nulos, cardinalidade e volumetria coluna a coluna."""
    if not banco.exists():
        print(f"  [aviso] banco {banco} nao encontrado; perfil ignorado.")
        return []

    con = duckdb.connect(str(banco), read_only=True)
    tabelas = []

    modelos = [
        n for n in manifest["nodes"].values()
        if n["resource_type"] == "model"
        and n["config"]["materialized"] != "ephemeral"
        and _pasta_para_camada(n.get("path", "")) in CAMADAS_PERFILADAS
    ]

    for no in sorted(modelos, key=lambda n: n["name"]):
        schema, nome = _relacao(no)
        alvo = f'"{schema}"."{nome}"'

        try:
            colunas = con.execute(
                "select column_name, data_type from information_schema.columns "
                "where table_schema = ? and table_name = ? order by ordinal_position",
                [schema, nome],
            ).fetchall()
            if not colunas:
                continue

            linhas_total = con.execute(f"select count(*) from {alvo}").fetchone()[0]
        except duckdb.Error as erro:
            print(f"  [aviso] {alvo}: {erro}")
            continue

        if not linhas_total:
            tabelas.append({
                "tabela": nome, "camada": _pasta_para_camada(no.get("path", "")),
                "schema": schema, "linhas": 0, "colunas": [],
            })
            continue

        # Uma unica varredura por tabela: nulos e distintos de todas as colunas.
        partes = []
        for coluna, _tipo in colunas:
            c = f'"{coluna}"'
            partes.append(f"count(*) - count({c})")
            # count(distinct) exato, e nao approx_count_distinct: um dashboard
            # de qualidade que arredonda cardinalidade nao serve para decidir
            # se uma coluna e chave.
            partes.append(f"count(distinct {c})")

        valores = con.execute(f"select {', '.join(partes)} from {alvo}").fetchone()

        detalhe = []
        for i, (coluna, tipo) in enumerate(colunas):
            nulos = int(valores[i * 2] or 0)
            distintos = int(valores[i * 2 + 1] or 0)
            detalhe.append({
                "coluna": coluna,
                "tipo": tipo,
                "nulos": nulos,
                "nulos_pct": round(100 * nulos / linhas_total, 2),
                "distintos": distintos,
                "distintos_pct": round(100 * distintos / linhas_total, 2),
                # Candidata a chave: nenhum nulo e um valor distinto por linha.
                "chave_candidata": nulos == 0 and distintos == linhas_total,
            })

        tabelas.append({
            "tabela": nome,
            "camada": _pasta_para_camada(no.get("path", "")),
            "schema": schema,
            "linhas": linhas_total,
            "colunas": detalhe,
        })

    con.close()
    return tabelas


# ---------------------------------------------------------------------------
# 4. Historico
# ---------------------------------------------------------------------------

def registrar_historico(caminho: Path, resumo: dict, cobertura: list[dict]) -> list[dict]:
    """Acrescenta o build atual e devolve os ultimos HISTORICO_MAXIMO."""
    colunas = sum(c["colunas_declaradas"] for c in cobertura) or 1
    documentadas = sum(c["colunas_documentadas"] for c in cobertura)

    linha = {
        "gerado_em": resumo["gerado_em"],
        "status": resumo["build"]["status"],
        "testes_total": resumo["build"]["testes_total"],
        "testes_aprovados": resumo["build"]["testes_aprovados"],
        "aprovacao_pct": round(
            100 * resumo["build"]["testes_aprovados"] / max(resumo["build"]["testes_total"], 1), 1
        ),
        "cobertura_doc_pct": round(100 * documentadas / colunas, 1),
        "duracao_s": resumo["build"]["duracao_total_s"],
    }

    caminho.parent.mkdir(parents=True, exist_ok=True)
    anteriores = []
    if caminho.exists():
        for texto in caminho.read_text(encoding="utf-8").splitlines():
            texto = texto.strip()
            if not texto:
                continue
            try:
                anteriores.append(json.loads(texto))
            except json.JSONDecodeError:
                continue

    # Nao duplica se o script rodar duas vezes sobre o mesmo build.
    if not anteriores or anteriores[-1].get("gerado_em") != linha["gerado_em"]:
        anteriores.append(linha)

    anteriores = anteriores[-HISTORICO_MAXIMO:]
    caminho.write_text(
        "\n".join(json.dumps(item, ensure_ascii=False) for item in anteriores) + "\n",
        encoding="utf-8",
    )
    return anteriores


# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Coleta os metadados de qualidade.")
    parser.add_argument("--alvo", default="target", type=Path)
    parser.add_argument("--banco", default="alexandria.duckdb", type=Path)
    parser.add_argument("--saida", default="site/qualidade.json", type=Path)
    parser.add_argument("--historico", default="site/historico.jsonl", type=Path)
    parser.add_argument("--sem-perfil", action="store_true", help="pula as queries no banco")
    args = parser.parse_args()

    manifest = json.loads((args.alvo / "manifest.json").read_text(encoding="utf-8"))
    run = json.loads((args.alvo / "run_results.json").read_text(encoding="utf-8"))

    print("Coletando qualidade...")
    resumo = resumir(args.alvo)
    testes = detalhar_testes(run, manifest)
    cobertura = detalhar_cobertura(manifest)
    perfil = [] if args.sem_perfil else perfilar(args.banco, manifest)
    historico = registrar_historico(args.historico, resumo, cobertura)

    colunas_total = sum(c["colunas_declaradas"] for c in cobertura)
    pacote = {
        "gerado_em": resumo["gerado_em"],
        "dbt_versao": resumo["dbt_versao"],
        "build": resumo["build"],
        "por_tipo": resumo["por_tipo"],
        "por_camada": resumo["por_camada"],
        "fontes": resumo["fontes"],
        "testes": testes,
        "cobertura": cobertura,
        "resumo_cobertura": {
            "colunas_fisicas": sum(len(t["colunas"]) for t in perfil),
            "modelos": len(cobertura),
            "modelos_descritos": sum(1 for c in cobertura if c["descrito"]),
            "modelos_com_teste_de_grao": sum(1 for c in cobertura if c["tem_teste_de_grao"]),
            "modelos_sem_teste": sum(1 for c in cobertura if c["testes"] == 0),
            "colunas_declaradas": colunas_total,
            "colunas_documentadas": sum(c["colunas_documentadas"] for c in cobertura),
            "colunas_testadas": sum(c["colunas_testadas"] for c in cobertura),
        },
        "perfil": perfil,
        "historico": historico,
    }

    args.saida.parent.mkdir(parents=True, exist_ok=True)
    args.saida.write_text(
        json.dumps(pacote, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    rc = pacote["resumo_cobertura"]
    b = pacote["build"]
    print(f"  testes      {b['testes_aprovados']}/{b['testes_total']} ({b['status']})")
    print(f"  modelos     {rc['modelos']}, {rc['modelos_com_teste_de_grao']} com teste de grao")
    print(f"  colunas     {rc['colunas_documentadas']}/{rc['colunas_declaradas']} documentadas")
    print(f"  perfil      {len(perfil)} tabela(s)")
    print(f"  historico   {len(historico)} build(s) em {args.historico}")
    print(f"\nEscrito em {args.saida}")

    tipos = Counter(t["status"] for t in testes)
    if tipos.get("fail") or tipos.get("error"):
        print("\nAtencao: ha testes reprovados neste build.")


if __name__ == "__main__":
    main()
