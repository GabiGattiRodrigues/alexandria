"""
Resumo executavel do ultimo build.

Le os artefatos que o proprio dbt gera (`target/run_results.json` e
`target/manifest.json`) e escreve `site/resultados.json` com o placar dos
testes: status, contagem por tipo, por camada e por severidade, mais o tempo de
execucao. A pagina do case consome esse arquivo para desenhar os graficos.

O ponto e que nenhum numero da pagina e digitado a mao: se um teste for
removido ou quebrar, o grafico muda no proximo build.

Uso:
    python scripts/resumo_testes.py
    python scripts/resumo_testes.py --saida site/resultados.json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

# Pasta do modelo testado -> camada exibida na pagina.
CAMADA_POR_PASTA = {
    "staging": "silver",
    "intermediate": "silver",
    "marts": "gold",
}

# Nomes tecnicos dos testes genericos -> rotulo legivel.
ROTULO_TESTE = {
    "not_null": "not_null",
    "unique": "unique",
    "accepted_values": "accepted_values",
    "relationships": "relationships",
    "accepted_range": "accepted_range",
    "expression_is_true": "expression_is_true",
}


def camada_do_no(no: dict, manifest: dict) -> str:
    """Descobre a camada a partir do primeiro nó testado pelo teste."""
    depends = no.get("depends_on", {}).get("nodes", [])
    for dep in depends:
        if dep.startswith("source."):
            return "bronze"
        alvo = manifest["nodes"].get(dep)
        if not alvo:
            continue
        caminho = alvo.get("path", "")
        for pasta, camada in CAMADA_POR_PASTA.items():
            if caminho.startswith(pasta + "/") or f"/{pasta}/" in caminho:
                return camada
    return "outros"


def resumir(alvo: Path) -> dict:
    caminho_run = alvo / "run_results.json"
    caminho_manifest = alvo / "manifest.json"

    if not caminho_run.exists() or not caminho_manifest.exists():
        sys.exit(
            f"Artefatos nao encontrados em {alvo}.\n"
            "Rode `dbt build` antes deste script."
        )

    run = json.loads(caminho_run.read_text(encoding="utf-8"))
    manifest = json.loads(caminho_manifest.read_text(encoding="utf-8"))

    por_tipo = Counter()
    por_camada = Counter()
    status = Counter()
    modelos = Counter()
    duracao_testes = 0.0
    falhas = []

    for resultado in run["results"]:
        unique_id = resultado["unique_id"]
        no = manifest["nodes"].get(unique_id)
        if not no:
            continue

        if no["resource_type"] == "model":
            modelos[no["config"]["materialized"]] += 1
            continue

        if no["resource_type"] != "test":
            continue

        meta = no.get("test_metadata") or {}
        nome = ROTULO_TESTE.get(meta.get("name", ""), meta.get("name") or "singular")
        por_tipo[nome] += 1
        por_camada[camada_do_no(no, manifest)] += 1
        status[resultado["status"]] += 1
        duracao_testes += float(resultado.get("execution_time") or 0)

        if resultado["status"] not in ("pass", "success"):
            falhas.append({
                "teste": no["name"],
                "status": resultado["status"],
                "mensagem": resultado.get("message"),
            })

    total_testes = sum(por_tipo.values())
    aprovados = status.get("pass", 0) + status.get("success", 0)

    # Cobertura: modelos com pelo menos um teste de grao (unique) declarado.
    modelos_todos = [
        n for n in manifest["nodes"].values() if n["resource_type"] == "model"
    ]
    testes_todos = [
        n for n in manifest["nodes"].values() if n["resource_type"] == "test"
    ]
    com_unique = set()
    for t in testes_todos:
        if (t.get("test_metadata") or {}).get("name") == "unique":
            for dep in t.get("depends_on", {}).get("nodes", []):
                com_unique.add(dep)
    colunas_documentadas = sum(len(n.get("columns") or {}) for n in modelos_todos)

    return {
        "gerado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "dbt_versao": run.get("metadata", {}).get("dbt_version"),
        "build": {
            "status": "aprovado" if not falhas else "reprovado",
            "testes_total": total_testes,
            "testes_aprovados": aprovados,
            "testes_reprovados": total_testes - aprovados,
            "duracao_testes_s": round(duracao_testes, 2),
            "duracao_total_s": round(float(run.get("elapsed_time") or 0), 2),
        },
        "por_tipo": dict(por_tipo.most_common()),
        "por_camada": {
            camada: por_camada.get(camada, 0)
            for camada in ("bronze", "silver", "gold", "outros")
            if por_camada.get(camada, 0)
        },
        "modelos": {
            "total": len(modelos_todos),
            "por_materializacao": dict(
                Counter(n["config"]["materialized"] for n in modelos_todos)
            ),
            "com_teste_de_grao": len(com_unique & {n["unique_id"] for n in modelos_todos}),
            "colunas_documentadas": colunas_documentadas,
        },
        "fontes": len(manifest.get("sources", {})),
        "falhas": falhas,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Resume o ultimo build do dbt.")
    parser.add_argument("--alvo", default="target", type=Path, help="pasta target do dbt")
    parser.add_argument("--saida", default="site/resultados.json", type=Path)
    args = parser.parse_args()

    resumo = resumir(args.alvo)
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    args.saida.write_text(
        json.dumps(resumo, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    b = resumo["build"]
    print(f"Build {b['status']}: {b['testes_aprovados']}/{b['testes_total']} testes")
    print(f"Resumo escrito em {args.saida}")
    if resumo["falhas"]:
        for f in resumo["falhas"]:
            print(f"  [falhou] {f['teste']}")


if __name__ == "__main__":
    main()
