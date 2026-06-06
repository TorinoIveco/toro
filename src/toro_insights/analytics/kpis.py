"""Service Layer de analytics — KPIs e agregações (pandas puro, testável).

Todas as funções operam sobre um DataFrame de `crm_leads` já filtrado para a
base analítica (exclui bucket 'Descartar', RN-05). Não dependem de Streamlit.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

ROTULO_NULO = "(não informado)"


@dataclass
class KpisGerais:
    """KPIs de topo do Dashboard Executivo."""

    leads: int
    vendas: int
    conversao_pct: float
    receita: float
    ticket_medio: float


def base_analitica(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica RN-05 — remove oportunidades do bucket 'Descartar'."""
    if "bucket_funil" not in df.columns:
        return df
    return df[df["bucket_funil"].fillna("") != "Descartar"].copy()


def kpis_gerais(df: pd.DataFrame) -> KpisGerais:
    """Calcula os KPIs principais a partir da base analítica."""
    leads = len(df)
    vendas = int(df["target_ml"].sum()) if leads else 0
    conversao = round(100.0 * vendas / leads, 2) if leads else 0.0
    receita = float(pd.to_numeric(df.get("valor_faturado"), errors="coerce").sum()) if leads else 0.0
    ticket = round(receita / vendas, 2) if vendas else 0.0
    return KpisGerais(leads, vendas, conversao, receita, ticket)


def conversao_por(df: pd.DataFrame, coluna: str, min_leads: int = 1) -> pd.DataFrame:
    """Agrega leads/vendas/conversão por uma dimensão (campanha, uf, cidade...).

    Retorna DataFrame ordenado por conversão desc, com nulos rotulados.
    """
    if df.empty or coluna not in df.columns:
        return pd.DataFrame(columns=[coluna, "leads", "vendas", "conversao_pct"])
    g = df.copy()
    g[coluna] = g[coluna].fillna(ROTULO_NULO).replace("", ROTULO_NULO)
    agg = (
        g.groupby(coluna)
        .agg(leads=("oportunidade_id", "count"), vendas=("target_ml", "sum"))
        .reset_index()
    )
    agg = agg[agg["leads"] >= min_leads]
    agg["conversao_pct"] = (100.0 * agg["vendas"] / agg["leads"]).round(1)
    return agg.sort_values(["conversao_pct", "leads"], ascending=False).reset_index(drop=True)


def desempenho_por(df: pd.DataFrame, coluna: str, min_leads: int = 1) -> pd.DataFrame:
    """Agrega leads, vendas, conversão, receita e ticket por uma dimensão.

    Mais rico que `conversao_por` (inclui R$). Ordenado por conversão desc.
    """
    cols = [coluna, "leads", "vendas", "conversao_pct", "receita", "ticket_medio"]
    if df.empty or coluna not in df.columns:
        return pd.DataFrame(columns=cols)
    g = df.copy()
    g[coluna] = g[coluna].fillna(ROTULO_NULO).replace("", ROTULO_NULO)
    g["valor_faturado"] = pd.to_numeric(g.get("valor_faturado"), errors="coerce")
    agg = (
        g.groupby(coluna)
        .agg(
            leads=("oportunidade_id", "count"),
            vendas=("target_ml", "sum"),
            receita=("valor_faturado", "sum"),
        )
        .reset_index()
    )
    agg = agg[agg["leads"] >= min_leads]
    agg["conversao_pct"] = (100.0 * agg["vendas"] / agg["leads"]).round(1)
    agg["ticket_medio"] = (agg["receita"] / agg["vendas"].where(agg["vendas"] != 0)).round(2)
    return agg.sort_values(["conversao_pct", "leads"], ascending=False).reset_index(drop=True)[cols]


def insights_campanhas(df: pd.DataFrame, min_leads: int = 10) -> list[str]:
    """Gera insights textuais automáticos sobre as campanhas."""
    d = desempenho_por(df, "campanha", min_leads=min_leads)
    if d.empty:
        return ["Sem campanhas com volume mínimo para gerar insights."]
    msgs: list[str] = []
    melhor = d.iloc[0]
    msgs.append(
        f"🏆 **{melhor['campanha']}** tem a maior conversão: "
        f"**{melhor['conversao_pct']:.1f}%** ({int(melhor['vendas'])} de {int(melhor['leads'])} leads)."
    )
    pior = d.iloc[-1]
    if pior["campanha"] != melhor["campanha"]:
        msgs.append(
            f"⚠️ **{pior['campanha']}** tem a menor conversão: **{pior['conversao_pct']:.1f}%** "
            f"— candidata a revisão de verba."
        )
    mais_leads = d.sort_values("leads", ascending=False).iloc[0]
    msgs.append(
        f"📈 Maior volume: **{mais_leads['campanha']}** com {int(mais_leads['leads'])} leads "
        f"(conversão {mais_leads['conversao_pct']:.1f}%)."
    )
    if d["receita"].fillna(0).sum() > 0:
        mais_receita = d.sort_values("receita", ascending=False).iloc[0]
        msgs.append(
            f"💰 Maior receita: **{mais_receita['campanha']}** "
            f"(R$ {mais_receita['receita']:,.0f})".replace(",", ".")
        )
    return msgs


def evolucao_anual(df: pd.DataFrame) -> pd.DataFrame:
    """Leads e vendas por ano de criação (RN-12)."""
    return conversao_por(df, "ano").sort_values("ano").reset_index(drop=True)


def volume_funil(df: pd.DataFrame, somente_ativos: bool = False) -> pd.DataFrame:
    """Volume por etapa do funil, ordenado pela ordem canônica.

    Com `somente_ativos=True`, exclui Perda/Descartar (mostra só etapas em
    andamento + Ganho) — útil para o gráfico de funil.
    """
    if df.empty:
        return pd.DataFrame(columns=["bucket_funil", "ordem_funil", "leads"])
    base = df
    if somente_ativos:
        base = df[~df["bucket_funil"].isin(["Perda", "Descartar"])]
    return (
        base.groupby(["bucket_funil", "ordem_funil"])
        .agg(leads=("oportunidade_id", "count"))
        .reset_index()
        .sort_values("ordem_funil")
        .reset_index(drop=True)
    )


@dataclass
class FunilDesfecho:
    """Desfecho do funil: ganhos, perdas e em andamento."""

    total: int
    ganhos: int
    perdas: int
    em_andamento: int
    taxa_ganho: float
    taxa_perda: float


def funil_desfecho(df: pd.DataFrame) -> FunilDesfecho:
    """Classifica as oportunidades em Ganho / Perda / Em andamento e calcula taxas."""
    total = len(df)
    if total == 0:
        return FunilDesfecho(0, 0, 0, 0, 0.0, 0.0)
    ganhos = int(df["target_ml"].sum())
    if "is_perda" in df.columns:
        perdas = int(df["is_perda"].fillna(False).astype(bool).sum())
    else:
        perdas = 0
    em_andamento = total - ganhos - perdas
    return FunilDesfecho(
        total, ganhos, perdas, em_andamento,
        round(100.0 * ganhos / total, 2),
        round(100.0 * perdas / total, 2),
    )


def desfecho_distribuicao(df: pd.DataFrame) -> pd.DataFrame:
    """Distribuição Ganho/Perda/Em andamento (para gráfico de pizza)."""
    d = funil_desfecho(df)
    return pd.DataFrame(
        {
            "desfecho": ["Ganho", "Perda", "Em andamento"],
            "leads": [d.ganhos, d.perdas, d.em_andamento],
        }
    )
