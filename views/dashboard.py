"""Tela 1 — Dashboard Executivo (visão geral de leads, vendas e conversão)."""

from __future__ import annotations

import plotly.express as px
import streamlit as st

from toro_insights.analytics import kpis as K
from toro_insights.presentation.ui import (
    cabecalho,
    filtros_sidebar,
    fmt_int,
    fmt_pct,
    fmt_reais,
    get_dados,
)

df_total = get_dados()
df = filtros_sidebar(df_total)

cabecalho(
    "📊 Dashboard Executivo",
    "Visão geral de leads, vendas e conversão (regra: venda = 'Ganho e Entregue').",
)

if df.empty:
    st.warning("Nenhum dado para os filtros selecionados.")
    st.stop()

# ---------------------------------------------------------------- KPIs
kpi = K.kpis_gerais(df)
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total de Leads", fmt_int(kpi.leads))
c2.metric("Total de Vendas", fmt_int(kpi.vendas))
c3.metric("Taxa de Conversão", fmt_pct(kpi.conversao_pct))
c4.metric("Receita Faturada", fmt_reais(kpi.receita) if kpi.receita else "—")
c5.metric("Ticket Médio", fmt_reais(kpi.ticket_medio) if kpi.ticket_medio else "—")
if not kpi.receita:
    st.caption("ℹ️ Receita/Ticket aguardam a integração do Valor Faturado das NFs (RN-13).")

st.divider()

# ---------------------------------------------------- Conversão por Campanha
st.subheader("Conversão por Campanha")
camp = K.conversao_por(df, "campanha", min_leads=10).head(15)
if camp.empty:
    st.info("Sem campanhas com volume mínimo (≥10 leads) nos filtros atuais.")
else:
    fig = px.bar(
        camp.sort_values("conversao_pct"),
        x="conversao_pct", y="campanha", orientation="h",
        text="conversao_pct", hover_data=["leads", "vendas"],
        labels={"conversao_pct": "Conversão (%)", "campanha": ""},
        color="conversao_pct", color_continuous_scale="Greens",
    )
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig.update_layout(height=500, coloraxis_showscale=False, margin=dict(l=10, r=10))
    st.plotly_chart(fig, width="stretch")
    st.caption("Apenas campanhas com ≥10 leads. Passe o mouse para ver leads e vendas.")

col_a, col_b = st.columns(2)

# ------------------------------------------------------ Conversão por Cidade
with col_a:
    st.subheader("Conversão por Cidade (Top 10)")
    cid = K.conversao_por(df, "cidade", min_leads=5).head(10)
    if cid.empty:
        st.info("Sem cidades com volume mínimo.")
    else:
        fig = px.bar(
            cid.sort_values("conversao_pct"),
            x="conversao_pct", y="cidade", orientation="h",
            text="conversao_pct", hover_data=["leads", "vendas"],
            labels={"conversao_pct": "Conversão (%)", "cidade": ""},
            color="conversao_pct", color_continuous_scale="Blues",
        )
        fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig.update_layout(height=420, coloraxis_showscale=False, margin=dict(l=10, r=10))
        st.plotly_chart(fig, width="stretch")

# ------------------------------------------------------- Volume por Estado
with col_b:
    st.subheader("Leads e Vendas por Estado")
    uf = K.conversao_por(df, "uf").sort_values("leads", ascending=False)
    if uf.empty:
        st.info("Sem dados por estado.")
    else:
        fig = px.bar(
            uf, x="uf", y=["leads", "vendas"], barmode="group",
            labels={"value": "Quantidade", "uf": "UF", "variable": ""},
            color_discrete_map={"leads": "#94a3b8", "vendas": "#16a34a"},
        )
        fig.update_layout(height=420, margin=dict(l=10, r=10))
        st.plotly_chart(fig, width="stretch")

# --------------------------------------------------------- Evolução por Ano
st.subheader("Evolução por Ano")
ano = K.evolucao_anual(df)
if ano.empty:
    st.info("Sem dados anuais.")
else:
    fig = px.bar(
        ano, x="ano", y=["leads", "vendas"], barmode="group",
        labels={"value": "Quantidade", "ano": "Ano", "variable": ""},
        color_discrete_map={"leads": "#94a3b8", "vendas": "#16a34a"},
    )
    fig.update_layout(height=350, margin=dict(l=10, r=10))
    st.plotly_chart(fig, width="stretch")
    if len(ano) == 1:
        st.caption("ℹ️ A base atual contém apenas um ano; a evolução fica mais rica com históricos.")
