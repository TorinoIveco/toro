"""Analytics de produtos (Tela 6) — sobre itens de NF (pandas puro, testável)."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

ROTULO_NULO = "(não informado)"


@dataclass
class KpisProdutos:
    """KPIs de topo da Tela de Produtos."""

    receita: float
    unidades: float
    modelos: int
    produtos: int
    ticket_unidade: float


def kpis_produtos(df: pd.DataFrame) -> KpisProdutos:
    """Calcula os KPIs principais de faturamento por produto."""
    if df.empty:
        return KpisProdutos(0.0, 0.0, 0, 0, 0.0)
    receita = float(pd.to_numeric(df["valor_total"], errors="coerce").sum())
    unidades = float(pd.to_numeric(df["quantidade"], errors="coerce").sum())
    modelos = int(df["modelo"].nunique(dropna=True))
    produtos = int(df["produto"].nunique(dropna=True))
    ticket = round(receita / unidades, 2) if unidades else 0.0
    return KpisProdutos(receita, unidades, modelos, produtos, ticket)


def por_dimensao(df: pd.DataFrame, coluna: str, top: int | None = None) -> pd.DataFrame:
    """Agrega unidades, receita e ticket médio por uma dimensão (gama, modelo, cidade...).

    Ordena por receita desc. Rotula nulos. `top` limita o nº de linhas.
    """
    if df.empty or coluna not in df.columns:
        return pd.DataFrame(columns=[coluna, "unidades", "receita", "ticket_medio"])
    g = df.copy()
    g[coluna] = g[coluna].fillna(ROTULO_NULO).replace("", ROTULO_NULO)
    g["quantidade"] = pd.to_numeric(g["quantidade"], errors="coerce")
    g["valor_total"] = pd.to_numeric(g["valor_total"], errors="coerce")
    agg = (
        g.groupby(coluna)
        .agg(unidades=("quantidade", "sum"), receita=("valor_total", "sum"))
        .reset_index()
    )
    agg["ticket_medio"] = (agg["receita"] / agg["unidades"].where(agg["unidades"] != 0)).round(2)
    agg = agg.sort_values("receita", ascending=False).reset_index(drop=True)
    return agg.head(top) if top else agg


def matriz_gama_cidade(df: pd.DataFrame, top_cidades: int = 10) -> pd.DataFrame:
    """Unidades por gama × cidade (para 'mais vendidos por cidade')."""
    if df.empty:
        return pd.DataFrame()
    g = df.copy()
    g["cidade"] = g["cidade"].fillna(ROTULO_NULO)
    g["quantidade"] = pd.to_numeric(g["quantidade"], errors="coerce")
    top = g.groupby("cidade")["quantidade"].sum().nlargest(top_cidades).index
    g = g[g["cidade"].isin(top)]
    return g.pivot_table(
        index="cidade", columns="gama", values="quantidade", aggfunc="sum", fill_value=0
    )
