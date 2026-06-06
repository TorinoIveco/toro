"""Tela 4 — Inteligência Geográfica (conversão por cidade e estado)."""

from __future__ import annotations

import plotly.express as px
import streamlit as st

from toro_insights.analytics import kpis as K
from toro_insights.presentation.ui import cabecalho, filtros_sidebar, fmt_int, fmt_pct, get_dados

df_total = get_dados()
df = filtros_sidebar(df_total)

cabecalho("🗺️ Inteligência Geográfica", "Leads e conversão por cidade e estado.")

if df.empty:
    st.warning("Nenhum dado para os filtros selecionados.")
    st.stop()

# ---------------------------------------------------------------- KPIs
c1, c2, c3 = st.columns(3)
c1.metric("Estados atendidos", fmt_int(df["uf"].nunique()))
c2.metric("Cidades atendidas", fmt_int(df["cidade"].nunique()))
melhor_uf = K.desempenho_por(df, "uf", min_leads=10)
if not melhor_uf.empty:
    c3.metric("UF que mais converte", melhor_uf.iloc[0]["uf"], fmt_pct(melhor_uf.iloc[0]["conversao_pct"]))

st.divider()

# ---------------------------------------------------------------- Estados
st.subheader("Desempenho por Estado")
uf = K.desempenho_por(df, "uf").sort_values("leads", ascending=False)
col_a, col_b = st.columns(2)
with col_a:
    fig = px.bar(
        uf, x="uf", y=["leads", "vendas"], barmode="group",
        labels={"value": "Quantidade", "uf": "UF", "variable": ""},
        color_discrete_map={"leads": "#94a3b8", "vendas": "#16a34a"},
    )
    fig.update_layout(height=400, margin=dict(l=10, r=10))
    st.plotly_chart(fig, width="stretch")
with col_b:
    fig = px.bar(
        uf.sort_values("conversao_pct"), x="conversao_pct", y="uf", orientation="h",
        text="conversao_pct", labels={"conversao_pct": "Conversão (%)", "uf": ""},
        color="conversao_pct", color_continuous_scale="Blues",
    )
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig.update_layout(height=400, coloraxis_showscale=False, margin=dict(l=10, r=10))
    st.plotly_chart(fig, width="stretch")

# ---------------------------------------------------- Top 10 cidades (leads)
st.subheader("Top 10 Cidades por Volume de Leads")
cid_vol = K.desempenho_por(df, "cidade").sort_values("leads", ascending=False).head(10)
fig = px.treemap(
    cid_vol, path=["cidade"], values="leads", color="conversao_pct",
    color_continuous_scale="RdYlGn", hover_data=["vendas", "conversao_pct"],
)
fig.update_layout(height=450, margin=dict(l=10, r=10))
st.plotly_chart(fig, width="stretch")
st.caption("Tamanho = volume de leads · cor = conversão (vermelho→verde).")

# ------------------------------------------------- Top 10 cidades (conversão)
st.subheader("Top 10 Cidades por Conversão (mín. 5 leads)")
cid_conv = K.desempenho_por(df, "cidade", min_leads=5).head(10)
if cid_conv.empty:
    st.info("Sem cidades com volume mínimo.")
else:
    fig = px.bar(
        cid_conv.sort_values("conversao_pct"),
        x="conversao_pct", y="cidade", orientation="h",
        text="conversao_pct", hover_data=["leads", "vendas"],
        labels={"conversao_pct": "Conversão (%)", "cidade": ""},
        color="conversao_pct", color_continuous_scale="Greens",
    )
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig.update_layout(height=420, coloraxis_showscale=False, margin=dict(l=10, r=10))
    st.plotly_chart(fig, width="stretch")
