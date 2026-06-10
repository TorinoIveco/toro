"""Tela 6 — Análise de Produtos (faturamento por gama, modelo, produto e cidade)."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from toro_insights.analytics import produtos as P
from toro_insights.presentation.ui import cabecalho, fmt_int, fmt_reais, get_produtos

df = get_produtos()

cabecalho(
    "📦 Análise de Produtos",
    "Faturamento e volume por gama, modelo, produto e região (base: itens de NF).",
)

if df.empty:
    st.warning("Sem dados de faturamento. Rode a integração de NF (run_nf.py).")
    st.stop()

# ---------------------------------------------------------------- Filtros
st.sidebar.header("Filtros")


def _multi(label: str, coluna: str) -> None:
    global df
    if coluna not in df.columns:
        return
    opcoes = sorted(x for x in df[coluna].dropna().unique())
    sel = st.sidebar.multiselect(label, opcoes)
    if sel:
        df = df[df[coluna].isin(sel)]


# Filtro por Ano (derivado da data de emissão da NF).
if "data_emissao" in df.columns:
    _anos = pd.to_datetime(df["data_emissao"], errors="coerce").dt.year.dropna()
    anos = sorted((int(a) for a in _anos.unique()), reverse=True)
    if anos:
        sel_anos = st.sidebar.multiselect("Ano", anos)
        if sel_anos:
            df = df[pd.to_datetime(df["data_emissao"], errors="coerce").dt.year.isin(sel_anos)]

_multi("Gama", "gama")
_multi("Estado (UF)", "uf")
_multi("Concessionária", "concessionaria")

if df.empty:
    st.warning("Nenhum produto para os filtros selecionados.")
    st.stop()

# ---------------------------------------------------------------- KPIs
k = P.kpis_produtos(df)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Receita", fmt_reais(k.receita))
c2.metric("Unidades Vendidas", fmt_int(k.unidades))
c3.metric("Modelos Distintos", fmt_int(k.modelos))
c4.metric("Ticket por Unidade", fmt_reais(k.ticket_unidade))

st.divider()

# ----------------------------------------------------- Gama (receita + unidades)
col_a, col_b = st.columns(2)
gama = P.por_dimensao(df, "gama")
with col_a:
    st.subheader("Receita por Gama")
    fig = px.pie(gama, names="gama", values="receita", hole=0.45)
    fig.update_layout(height=380, margin=dict(l=10, r=10))
    st.plotly_chart(fig, width="stretch")
with col_b:
    st.subheader("Unidades por Gama")
    fig = px.bar(
        gama.sort_values("unidades"), x="unidades", y="gama", orientation="h",
        text="unidades", labels={"unidades": "Unidades", "gama": ""},
        color="gama",
    )
    fig.update_layout(height=380, showlegend=False, margin=dict(l=10, r=10))
    st.plotly_chart(fig, width="stretch")

# ------------------------------------------------------- Top modelos / produtos
col_c, col_d = st.columns(2)
with col_c:
    st.subheader("Top 10 Modelos por Receita")
    mod = P.por_dimensao(df, "modelo", top=10)
    fig = px.bar(
        mod.sort_values("receita"), x="receita", y="modelo", orientation="h",
        hover_data=["unidades"], labels={"receita": "Receita (R$)", "modelo": ""},
        color="receita", color_continuous_scale="Greens",
    )
    fig.update_layout(height=420, coloraxis_showscale=False, margin=dict(l=10, r=10))
    st.plotly_chart(fig, width="stretch")
with col_d:
    st.subheader("Top 10 Produtos por Unidades")
    prod = P.por_dimensao(df, "produto", top=10)
    fig = px.bar(
        prod.sort_values("unidades"), x="unidades", y="produto", orientation="h",
        text="unidades", hover_data=["receita"], labels={"unidades": "Unidades", "produto": ""},
        color="unidades", color_continuous_scale="Blues",
    )
    fig.update_layout(height=420, coloraxis_showscale=False, margin=dict(l=10, r=10))
    st.plotly_chart(fig, width="stretch")

# ----------------------------------------------------- Mais vendidos por cidade
st.subheader("Mais Vendidos por Cidade (unidades por gama)")
matriz = P.matriz_gama_cidade(df, top_cidades=10)
if matriz.empty:
    st.info("Sem dados por cidade.")
else:
    dados = matriz.reset_index().melt(id_vars="cidade", var_name="gama", value_name="unidades")
    fig = px.bar(
        dados, x="unidades", y="cidade", color="gama", orientation="h",
        labels={"unidades": "Unidades", "cidade": ""},
    )
    fig.update_layout(height=450, barmode="stack", margin=dict(l=10, r=10))
    st.plotly_chart(fig, width="stretch")

# ----------------------------------------------------------------- Detalhe
with st.expander("📋 Tabela detalhada por produto"):
    tabela = P.por_dimensao(df, "produto")
    st.dataframe(tabela, width="stretch", hide_index=True)
