"""Utilidades de UI compartilhadas entre as telas (formatação, filtros, dados)."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from toro_insights.analytics.loader import carregar_base, carregar_produtos


@st.cache_data(ttl=600, show_spinner="Carregando dados...")
def get_dados() -> pd.DataFrame:
    """Base analítica com cache (10 min). Use `limpar_cache()` após nova carga."""
    return carregar_base()


@st.cache_data(ttl=600, show_spinner="Carregando produtos...")
def get_produtos() -> pd.DataFrame:
    """Itens de NF enriquecidos com cache (10 min)."""
    return carregar_produtos()


def limpar_cache() -> None:
    """Invalida o cache de dados (chamar após um novo ETL)."""
    get_dados.clear()
    get_produtos.clear()


def fmt_int(v: float | int) -> str:
    """Inteiro no padrão pt-BR (1.595)."""
    return f"{int(v):,}".replace(",", ".")


def fmt_pct(v: float) -> str:
    """Percentual pt-BR (6,3%)."""
    return f"{v:.1f}%".replace(".", ",")


def fmt_reais(v: float) -> str:
    """Moeda pt-BR (R$ 1.234,56)."""
    s = f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"


def filtros_sidebar(df: pd.DataFrame) -> pd.DataFrame:
    """Renderiza filtros globais na sidebar e devolve o DataFrame filtrado."""
    st.sidebar.header("Filtros")
    out = df.copy()

    def _multi(label: str, coluna: str) -> None:
        nonlocal out
        if coluna not in out.columns:
            return
        opcoes = sorted(x for x in out[coluna].dropna().unique())
        sel = st.sidebar.multiselect(label, opcoes)
        if sel:
            out = out[out[coluna].isin(sel)]

    _multi("Ano", "ano")
    _multi("Estado (UF)", "uf")
    _multi("Concessionária", "concessionaria")
    _multi("Campanha", "campanha")
    return out


def cabecalho(titulo: str, subtitulo: str = "") -> None:
    """Cabeçalho padronizado de tela."""
    st.title(titulo)
    if subtitulo:
        st.caption(subtitulo)
