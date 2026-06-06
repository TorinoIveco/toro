"""Constrói o digest de dados (sem PII) injetado no system prompt do assistente."""

from __future__ import annotations

import pandas as pd

from toro_insights.analytics import kpis as K
from toro_insights.analytics import produtos as P
from toro_insights.analytics.loader import carregar_base, carregar_produtos
from toro_insights.ml.score import carregar_modelo


def _tabela(df: pd.DataFrame, colunas: list[str], n: int = 6) -> str:
    if df.empty:
        return "  (sem dados)"
    cols = [c for c in colunas if c in df.columns]
    linhas = [" | ".join(str(r[c]) for c in cols) for _, r in df.head(n).iterrows()]
    return "\n".join("  - " + ln for ln in linhas)


def construir_digest() -> str:
    """Resumo compacto e PII-free do estado atual dos dados."""
    df = carregar_base()
    prod = carregar_produtos()
    k = K.kpis_gerais(df)
    d = K.funil_desfecho(df)

    partes = [
        "### KPIs gerais",
        f"- Leads: {k.leads} | Vendas: {k.vendas} | Conversão: {k.conversao_pct}% "
        f"| Receita: R$ {k.receita:.0f} | Ticket médio: R$ {k.ticket_medio:.0f}",
        f"- Funil: ganhos {d.ganhos}, perdas {d.perdas}, em andamento {d.em_andamento} "
        f"(taxa de perda {d.taxa_perda}%)",
        "",
        "### Campanhas (campanha | leads | vendas | conv% | receita) — top conversão (≥10 leads)",
        _tabela(
            K.desempenho_por(df, "campanha", min_leads=10),
            ["campanha", "leads", "vendas", "conversao_pct", "receita"], 8,
        ),
        "",
        "### Estados (uf | leads | vendas | conv% | receita)",
        _tabela(K.desempenho_por(df, "uf"), ["uf", "leads", "vendas", "conversao_pct", "receita"]),
        "",
        "### Cidades — top conversão (≥5 leads)",
        _tabela(
            K.desempenho_por(df, "cidade", min_leads=5),
            ["cidade", "leads", "vendas", "conversao_pct"], 8,
        ),
        "",
        "### Produtos por gama (gama | unidades | receita)",
        _tabela(P.por_dimensao(prod, "gama"), ["gama", "unidades", "receita"]),
        "",
        "### Modelos mais faturados (modelo | unidades | receita)",
        _tabela(P.por_dimensao(prod, "modelo", top=8), ["modelo", "unidades", "receita"]),
    ]

    bundle = carregar_modelo()
    if bundle is not None:
        top_imp = list(bundle["importancia"].items())[:5]
        partes += [
            "",
            "### Lead scoring (XGBoost)",
            f"- Métricas: {bundle['metricas']}",
            f"- Variáveis mais importantes: {top_imp}",
        ]

    return "\n".join(partes)
