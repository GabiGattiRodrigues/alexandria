"""
Alexandria — Observabilidade de Dados

Dashboard de qualidade da própria camada de dados. Lê o arquivo que
scripts/coletar_qualidade.py escreve a partir dos metadados do dbt e das
queries de perfil no DuckDB.

Não recalcula nada: se um número aqui divergir do que o dbt reportou, o erro
está no coletor, não no dashboard. É a mesma regra que o projeto aplica às
métricas de negócio, aplicada a ele mesmo.

Rodar local:
    streamlit run app/dashboard_qualidade.py
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

RAIZ = Path(__file__).resolve().parent.parent
ARQUIVO = RAIZ / "site" / "qualidade.json"

# Paleta validada para daltonismo e contraste — a mesma da página do case.
BRONZE, PRATA, OURO = "#9C5A2B", "#2F7FB5", "#A37C12"
AZUL, VERDE, VERMELHO = "#1857B0", "#1B7A47", "#B3261E"
CINZA = "#7F92A6"
CORES_CAMADA = {"bronze": BRONZE, "silver": PRATA, "gold": OURO, "outros": CINZA}

st.set_page_config(
    page_title="Alexandria · Observabilidade de Dados",
    page_icon="🏛️",
    layout="wide",
)


# ---------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def carregar(caminho: Path, assinatura: float) -> dict:
    """Lê o pacote de qualidade. `assinatura` invalida o cache quando o arquivo muda."""
    return json.loads(caminho.read_text(encoding="utf-8"))


def formatar_data(iso: str) -> str:
    try:
        return datetime.fromisoformat(iso).strftime("%d/%m/%Y às %H:%M")
    except (ValueError, TypeError):
        return iso or "—"


def barra(df: pd.DataFrame, x: str, y: str, cor, titulo_x: str, altura: int | None = None):
    """Barras horizontais com rótulo direto — o padrão usado no projeto inteiro."""
    # A altura acompanha a quantidade de barras; sem isso o Altair começa a
    # esconder rótulo do eixo, e um gráfico de qualidade com metade das
    # categorias sem nome não serve para nada.
    altura = altura or max(140, 30 * len(df))
    base = alt.Chart(df).encode(
        y=alt.Y(f"{y}:N", sort="-x", title=None,
                axis=alt.Axis(labelFontSize=12, labelLimit=220, labelOverlap=False)),
        x=alt.X(f"{x}:Q", title=titulo_x, axis=alt.Axis(grid=True, tickMinStep=1)),
        tooltip=list(df.columns),
    )
    marcas = base.mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4, height=15)
    marcas = marcas.encode(color=cor) if cor is not None else marcas.encode(
        color=alt.value(AZUL)
    )
    rotulos = base.mark_text(align="left", dx=5, fontSize=11).encode(text=f"{x}:Q")
    return (marcas + rotulos).properties(height=altura)


# ---------------------------------------------------------------------------

if not ARQUIVO.exists():
    st.error(
        "`site/qualidade.json` não encontrado.\n\n"
        "Rode o projeto primeiro:\n\n"
        "```\ndbt build --profiles-dir .\npython scripts/coletar_qualidade.py\n```"
    )
    st.stop()

dados = carregar(ARQUIVO, ARQUIVO.stat().st_mtime)
build = dados["build"]
cob = dados["resumo_cobertura"]
aprovado = build["status"] == "aprovado"

st.title("Observabilidade de Dados")
st.caption(
    "Alexandria · a camada de dados por trás do Dashboard Inteligente. "
    "Tudo nesta tela vem dos metadados que o dbt gera a cada execução — "
    "nenhum número é digitado à mão."
)

# --- placar -----------------------------------------------------------------
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric(
    "Último build",
    "aprovado" if aprovado else "reprovado",
    delta=None if aprovado else f"-{build['testes_reprovados']} testes",
    delta_color="normal" if aprovado else "inverse",
)
col2.metric("Testes", f"{build['testes_aprovados']}/{build['testes_total']}")
col3.metric(
    "Colunas documentadas",
    f"{cob['colunas_documentadas']}/{cob['colunas_declaradas']}",
)
col4.metric(
    "Modelos com teste de grão",
    f"{cob['modelos_com_teste_de_grao']}/{cob['modelos']}",
)
col5.metric("Duração", f"{build['duracao_total_s']}s")

st.caption(
    f"dbt {dados.get('dbt_versao', '—')} · coletado em {formatar_data(dados['gerado_em'])} · "
    f"{dados['fontes']} tabelas de origem"
)

if not aprovado:
    st.error(
        f"{build['testes_reprovados']} teste(s) reprovado(s) no último build. "
        "O detalhe está na aba Testes."
    )

st.divider()

abas = st.tabs(["Testes", "Cobertura", "Perfil dos dados", "Histórico"])

# --- 1. testes --------------------------------------------------------------
with abas[0]:
    testes = pd.DataFrame(dados["testes"])

    esq, dir_ = st.columns(2)
    with esq:
        st.subheader("Por camada")
        st.caption("A cobertura cresce em direção ao consumo — é onde o erro custa caro.")
        por_camada = (
            testes.groupby("camada").size().reset_index(name="testes")
            .sort_values("testes", ascending=False)
        )
        st.altair_chart(
            barra(
                por_camada, "testes", "camada",
                alt.Color("camada:N",
                          scale=alt.Scale(domain=list(CORES_CAMADA), range=list(CORES_CAMADA.values())),
                          legend=None),
                "testes",
            ),
            use_container_width=True,
        )

    with dir_:
        st.subheader("Por tipo")
        st.caption("Dos genéricos do dbt aos escritos à mão em SQL.")
        por_tipo = (
            testes.groupby("tipo").size().reset_index(name="testes")
            .sort_values("testes", ascending=False)
        )
        st.altair_chart(
            barra(por_tipo, "testes", "tipo", None, "testes"),
            use_container_width=True,
        )

    st.subheader("Cada teste, um por linha")
    filtro_camada = st.multiselect(
        "Camada", sorted(testes["camada"].unique()), default=list(sorted(testes["camada"].unique()))
    )
    so_falhas = st.toggle("Mostrar apenas os que não passaram", value=False)

    visao = testes[testes["camada"].isin(filtro_camada)]
    if so_falhas:
        visao = visao[visao["status"] != "pass"]

    if visao.empty:
        st.success("Nenhum teste reprovado com os filtros aplicados.")
    else:
        st.dataframe(
            visao.rename(columns={
                "nome": "teste", "alvo": "modelo", "violacoes": "linhas violadas",
                "duracao_s": "duração (s)", "severidade": "severidade",
            }),
            use_container_width=True, hide_index=True,
            column_config={
                "status": st.column_config.TextColumn(width="small"),
                "linhas violadas": st.column_config.NumberColumn(format="%d"),
            },
        )

# --- 2. cobertura -----------------------------------------------------------
with abas[1]:
    st.subheader("Onde estão os buracos")
    st.caption(
        "Um modelo sem teste de grão é um modelo em que ninguém provou "
        "o que é uma linha. É a primeira coisa que um head de dados procura."
    )

    cobertura = pd.DataFrame(dados["cobertura"])
    cobertura["doc_pct"] = (
        100 * cobertura["colunas_documentadas"] / cobertura["colunas_declaradas"].replace(0, pd.NA)
    ).round(0)

    sem_grao = cobertura[~cobertura["tem_teste_de_grao"]]
    sem_teste = cobertura[cobertura["testes"] == 0]

    c1, c2, c3 = st.columns(3)
    c1.metric("Modelos descritos", f"{cob['modelos_descritos']}/{cob['modelos']}")
    c2.metric("Sem teste de grão", len(sem_grao))
    c3.metric("Sem nenhum teste", len(sem_teste))

    if len(sem_grao):
        st.info(
            "Os modelos sem teste de grão são os `ephemeral` e as views intermediárias: "
            "eles não existem como tabela no banco, e o que produzem é validado em "
            "`fct_pedidos`, onde o resultado passa a existir. É uma escolha, não um esquecimento."
        )

    st.altair_chart(
        barra(
            cobertura.sort_values("testes", ascending=False),
            "testes", "nome",
            alt.Color("camada:N",
                      scale=alt.Scale(domain=list(CORES_CAMADA), range=list(CORES_CAMADA.values())),
                      legend=alt.Legend(title="camada", orient="top")),
            "testes por modelo",
            altura=max(200, 30 * len(cobertura)),
        ),
        use_container_width=True,
    )

    st.dataframe(
        cobertura[[
            "nome", "camada", "materializacao", "testes", "tem_teste_de_grao",
            "colunas_declaradas", "colunas_documentadas", "colunas_testadas",
        ]].rename(columns={
            "nome": "modelo", "materializacao": "materialização",
            "tem_teste_de_grao": "teste de grão",
            "colunas_declaradas": "colunas", "colunas_documentadas": "documentadas",
            "colunas_testadas": "testadas",
        }),
        use_container_width=True, hide_index=True,
    )

# --- 3. perfil --------------------------------------------------------------
with abas[2]:
    perfil = dados.get("perfil") or []
    if not perfil:
        st.warning(
            "Perfil não coletado. Ele precisa do arquivo `.duckdb`, que não é "
            "versionado. Rode `python scripts/coletar_qualidade.py` depois do build."
        )
    else:
        st.subheader("Volumetria")
        st.caption("A bronze fica de fora: medir qualidade nela seria medir o fornecedor.")

        volumes = pd.DataFrame([
            {"tabela": t["tabela"], "camada": t["camada"], "linhas": t["linhas"],
             "colunas": len(t["colunas"])}
            for t in perfil
        ]).sort_values("linhas", ascending=False)

        st.altair_chart(
            barra(
                volumes, "linhas", "tabela",
                alt.Color("camada:N",
                          scale=alt.Scale(domain=list(CORES_CAMADA), range=list(CORES_CAMADA.values())),
                          legend=alt.Legend(title="camada", orient="top")),
                "linhas",
                altura=max(200, 30 * len(volumes)),
            ),
            use_container_width=True,
        )

        st.subheader("Coluna a coluna")
        escolha = st.selectbox(
            "Tabela", volumes["tabela"].tolist(),
            index=volumes["tabela"].tolist().index("fct_pedidos")
            if "fct_pedidos" in volumes["tabela"].tolist() else 0,
        )
        tabela = next(t for t in perfil if t["tabela"] == escolha)

        colunas = pd.DataFrame(tabela["colunas"])
        st.caption(
            f"`{tabela['schema']}.{tabela['tabela']}` · {tabela['linhas']:,} linhas · "
            f"{len(colunas)} colunas".replace(",", ".")
        )

        chaves = colunas[colunas["chave_candidata"]]["coluna"].tolist()
        if chaves:
            st.success(
                "Candidatas a chave (sem nulos, um valor distinto por linha): "
                + ", ".join(f"`{c}`" for c in chaves)
            )

        com_nulos = colunas[colunas["nulos"] > 0]
        if not com_nulos.empty:
            st.altair_chart(
                barra(
                    com_nulos.sort_values("nulos_pct", ascending=False),
                    "nulos_pct", "coluna", alt.value(BRONZE), "% de nulos",
                    altura=max(140, 30 * len(com_nulos)),
                ),
                use_container_width=True,
            )
        else:
            st.success("Nenhuma coluna com nulos nesta tabela.")

        st.dataframe(
            colunas.rename(columns={
                "coluna": "coluna", "tipo": "tipo", "nulos": "nulos",
                "nulos_pct": "% nulos", "distintos": "distintos",
                "distintos_pct": "% distintos", "chave_candidata": "chave?",
            }),
            use_container_width=True, hide_index=True,
        )

# --- 4. histórico -----------------------------------------------------------
with abas[3]:
    historico = pd.DataFrame(dados.get("historico") or [])
    if historico.empty or len(historico) < 2:
        st.info(
            "O histórico acumula uma linha por build, em `site/historico.jsonl`. "
            f"Por enquanto há {len(historico)} execução(ões) registrada(s) — "
            "a tendência aparece a partir da segunda."
        )
        if not historico.empty:
            st.dataframe(historico, use_container_width=True, hide_index=True)
    else:
        historico["quando"] = pd.to_datetime(historico["gerado_em"], format="mixed", utc=True)
        historico["build"] = range(1, len(historico) + 1)

        st.subheader("Taxa de aprovação por build")
        linha = alt.Chart(historico).mark_line(point=True, strokeWidth=2, color=VERDE).encode(
            x=alt.X("build:Q", title="build", axis=alt.Axis(tickMinStep=1)),
            y=alt.Y("aprovacao_pct:Q", title="% de testes aprovados",
                    scale=alt.Scale(domain=[0, 105])),
            tooltip=["build", "quando", "aprovacao_pct", "testes_total", "status"],
        ).properties(height=240)
        st.altair_chart(linha, use_container_width=True)

        st.subheader("Cobertura de documentação e volume de testes")
        esq, dir_ = st.columns(2)
        with esq:
            st.altair_chart(
                alt.Chart(historico).mark_line(point=True, strokeWidth=2, color=AZUL).encode(
                    x=alt.X("build:Q", title="build", axis=alt.Axis(tickMinStep=1)),
                    y=alt.Y("cobertura_doc_pct:Q", title="% de colunas documentadas",
                            scale=alt.Scale(domain=[0, 105])),
                    tooltip=["build", "cobertura_doc_pct"],
                ).properties(height=220),
                use_container_width=True,
            )
        with dir_:
            st.altair_chart(
                alt.Chart(historico).mark_line(point=True, strokeWidth=2, color=OURO).encode(
                    x=alt.X("build:Q", title="build", axis=alt.Axis(tickMinStep=1)),
                    y=alt.Y("testes_total:Q", title="testes executados"),
                    tooltip=["build", "testes_total"],
                ).properties(height=220),
                use_container_width=True,
            )

        st.dataframe(
            historico[[
                "build", "gerado_em", "status", "testes_aprovados", "testes_total",
                "aprovacao_pct", "cobertura_doc_pct", "duracao_s",
            ]].rename(columns={
                "gerado_em": "quando", "aprovacao_pct": "% aprovação",
                "cobertura_doc_pct": "% documentado", "duracao_s": "duração (s)",
            }).iloc[::-1],
            use_container_width=True, hide_index=True,
        )

st.divider()
st.caption(
    "[Repositório](https://github.com/GabiGattiRodrigues/alexandria) · "
    "[Documentação e linhagem](https://gabigattirodrigues.github.io/alexandria/docs/) · "
    "[Dashboard Inteligente](https://dashboardinteligente.streamlit.app) · "
    "Gabriela Gatti Rodrigues"
)
