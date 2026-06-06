"""Tela 3 — Análise de Campanhas (leads, vendas, conversão, ranking e insights)."""

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

cabecalho("📣 Análise de Campanhas", "Desempenho, ranking e insights por campanha.")

if df.empty:
    st.warning("Nenhum dado para os filtros selecionados.")
    st.stop()

min_leads = st.sidebar.slider("Mínimo de leads p/ ranking", 1, 50, 10)
desemp = K.desempenho_por(df, "campanha", min_leads=min_leads)

# ---------------------------------------------------------------- Insights
st.subheader("💡 Insights automáticos")
for msg in K.insights_campanhas(df, min_leads=min_leads):
    st.markdown(f"- {msg}")

st.divider()

if desemp.empty:
    st.info("Sem campanhas com o volume mínimo selecionado.")
    st.stop()

# ---------------------------------------------------------------- Ranking
c1, c2 = st.columns(2)
melhor = desemp.iloc[0]
pior = desemp.iloc[-1]
c1.metric("🏆 Melhor campanha", melhor["campanha"], fmt_pct(melhor["conversao_pct"]))
c2.metric("🔻 Pior campanha", pior["campanha"], fmt_pct(pior["conversao_pct"]))

# --------------------------------------------------- Conversão por campanha
st.subheader("Conversão por Campanha")
fig = px.bar(
    desemp.sort_values("conversao_pct"),
    x="conversao_pct", y="campanha", orientation="h",
    text="conversao_pct", hover_data=["leads", "vendas", "receita"],
    labels={"conversao_pct": "Conversão (%)", "campanha": ""},
    color="conversao_pct", color_continuous_scale="Greens",
)
fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
fig.update_layout(height=520, coloraxis_showscale=False, margin=dict(l=10, r=10))
st.plotly_chart(fig, width="stretch")

# --------------------------------------------------- Volume vs conversão
st.subheader("Volume × Conversão (bolha = receita)")
fig = px.scatter(
    desemp, x="leads", y="conversao_pct", size="receita", color="campanha",
    hover_name="campanha", labels={"leads": "Leads", "conversao_pct": "Conversão (%)"},
    size_max=50,
)
fig.update_layout(height=460, showlegend=False, margin=dict(l=10, r=10))
st.plotly_chart(fig, width="stretch")

# ----------------------------------------------------------------- Tabela
with st.expander("📋 Tabela completa por campanha"):
    t = desemp.copy()
    t["receita"] = t["receita"].fillna(0).map(fmt_reais)
    t["conversao_pct"] = t["conversao_pct"].map(lambda v: fmt_pct(v))
    st.dataframe(t, width="stretch", hide_index=True)
