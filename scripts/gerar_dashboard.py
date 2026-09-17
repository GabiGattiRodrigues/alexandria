"""
Gera a versao estatica do dashboard de qualidade.

Pega o modelo em site/_modelo_qualidade.html e injeta dentro dele o conteudo de
site/qualidade.json, produzindo site/qualidade.html.

Injetar em vez de buscar com fetch e proposital: assim a pagina funciona igual
publicada no GitHub Pages e aberta direto do disco com dois cliques, sem
servidor e sem esbarrar em CORS.

Uso:
    python scripts/gerar_dashboard.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ABRE = "/*__DADOS__*/"
FECHA = "/*__FIM__*/"


def gerar(modelo: Path, dados: Path, saida: Path) -> int:
    if not modelo.exists():
        sys.exit(f"Modelo nao encontrado: {modelo}")
    if not dados.exists():
        sys.exit(
            f"Dados nao encontrados: {dados}\n"
            "Rode `python scripts/coletar_qualidade.py` antes."
        )

    html = modelo.read_text(encoding="utf-8")
    pacote = json.loads(dados.read_text(encoding="utf-8"))

    inicio = html.find(ABRE)
    fim = html.find(FECHA)
    if inicio == -1 or fim == -1:
        sys.exit(f"Marcadores {ABRE} ... {FECHA} nao encontrados no modelo.")

    # `</script>` dentro de uma string JSON encerraria a tag no navegador.
    json_seguro = json.dumps(pacote, ensure_ascii=False).replace("</", "<\\/")

    html = html[:inicio] + json_seguro + html[fim + len(FECHA):]
    saida.write_text(html, encoding="utf-8")
    return len(html.encode("utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Gera o dashboard estatico de qualidade.")
    parser.add_argument("--modelo", default="site/_modelo_qualidade.html", type=Path)
    parser.add_argument("--dados", default="site/qualidade.json", type=Path)
    parser.add_argument("--saida", default="site/qualidade.html", type=Path)
    args = parser.parse_args()

    tamanho = gerar(args.modelo, args.dados, args.saida)
    print(f"Dashboard escrito em {args.saida} ({tamanho // 1024} KB)")


if __name__ == "__main__":
    main()
