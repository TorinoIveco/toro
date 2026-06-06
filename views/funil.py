"""Tela 2 — Funil Comercial (volume por etapa, desfecho, taxa de perda)."""

from __future__ import annotations

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from toro_insights.analytics import kpis as K
from toro_insights.presentation.ui import cabecalho, filtros_sidebar, fmt_int, fmt_pct, get_dados

df_total = get_dados()
df = filtros_sidebar(df_total)

cabecalho(
    "🫙 Funil Comercial",
    "Distribuição das oportunidades por etapa (foto atual — snapshot do CRM).",
)

if df.empty:
    st.warning("Nenhum dado para os filtros selecionados.")
    st.stop()

# ---------------------------------------------------------------- KPIs
d = K.funil_desfecho(df)
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Oportunidades", fmt_int(d.total))
c2.metric("Ganhos", fmt_int(d.ganhos))
c3.metric("Perdas", fmt_int(d.perdas))
c4.metric("Em andamento", fmt_int(d.em_andamento))
c5.metric("Taxa de Perda", fmt_pct(d.taxa_perda))

st.divider()

col_a, col_b = st.columns([3, 2])

# --------------------------------------------------------------- Funil
with col_a:
    st.subheader("Etapas do Funil (em andamento → ganho)")
    fun = K.volume_funil(df, somente_ativos=True)
    if fun.empty or fun["leads"].sum() == 0:
        st.info("Sem oportunidades em etapas ativas nos filtros atuais.")
    else:
        fig = go.Figure(
            go.Funnel(
                y=fun["bucket_funil"],
                x=fun["leads"],
                textinfo="value+percent initial",
                marker={"color": "#2563eb"},
            )
        )
        fig.update_layout(height=460, margin=dict(l=10, r=10))
        st.plotly_chart(fig, width="stretch")
        st.caption(
            "⚠️ Snapshot: mostra a etapa **atual** de cada oportunidade, não o fluxo "
            "histórico. Perdas/descartes ficam fora deste gráfico."
        )

# ------------------------------------------------------------- Desfecho
with col_b:
    st.subheader("Desfecho")
    dist = K.desfecho_distribuicao(df)
    fig = px.pie(
        dist, names="desfecho", values="leads", hole=0.45,
        color="desfecho",
        color_discrete_map={"Ganho": "#16a34a", "Perda": "#dc2626", "Em andamento": "#f59e0b"},
    )
    fig.update_layout(height=460, margin=dict(l=10, r=10))
    st.plotly_chart(fig, width="stretch")

# --------------------------------------------------- Detalhe por bucket
st.subheader("Volume por etapa (todas)")
todas = K.volume_funil(df)
fig = px.bar(
    todas, x="leads", y="bucket_funil", orientation="h",
    text="leads", labels={"leads": "Oportunidades", "bucket_funil": ""},
    color="bucket_funil",
)
fig.update_layout(height=400, showlegend=False, margin=dict(l=10, r=10),
                  yaxis={"categoryorder": "array", "categoryarray": list(todas["bucket_funil"])[::-1]})
st.plotly_chart(fig, width="stretch")
