"""Tela 5 — Lead Scoring (probabilidade de conversão via XGBoost)."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from toro_insights.ml import score as S
from toro_insights.presentation.ui import cabecalho, fmt_int, get_dados

cabecalho(
    "🎯 Lead Scoring",
    "Probabilidade de conversão (Ganho e Entregue) prevista por XGBoost.",
)

bundle = S.carregar_modelo()
if bundle is None:
    st.warning(
        "Modelo ainda não treinado. Rode:\n\n"
        "`python scripts/train_model.py`\n\n"
        "(o treino exige a base completa de leads — vendas e não-vendas)."
    )
    st.stop()

# ----------------------------------------------------------- Métricas do modelo
st.subheader("Desempenho do modelo")
m = bundle["metricas"]
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("ROC AUC", m["roc_auc"])
c2.metric("Accuracy", m["accuracy"])
c3.metric("Precision", m["precision"])
c4.metric("Recall", m["recall"])
c5.metric("F1", m["f1"])
st.caption(
    f"Treinado em {bundle['treinado_em']} · {fmt_int(bundle['n_treino'])} treino / "
    f"{fmt_int(bundle['n_teste'])} teste."
)

st.divider()

col_a, col_b = st.columns(2)

# --------------------------------------------------- Importância das variáveis
with col_a:
    st.subheader("Importância das variáveis")
    imp = pd.DataFrame(
        {"variavel": list(bundle["importancia"]), "importancia": list(bundle["importancia"].values())}
    )
    fig = px.bar(
        imp.sort_values("importancia"), x="importancia", y="variavel", orientation="h",
        labels={"importancia": "Importância", "variavel": ""},
        color="importancia", color_continuous_scale="Purples",
    )
    fig.update_layout(height=400, coloraxis_showscale=False, margin=dict(l=10, r=10))
    st.plotly_chart(fig, width="stretch")

# ------------------------------------------------------- Scoring dos leads
df = get_dados()
try:
    scored = S.pontuar(df, bundle)
except Exception as exc:  # noqa: BLE001
    st.error(
        "Não foi possível pontuar os leads com o modelo salvo. Isso normalmente "
        "ocorre quando a versão do XGBoost no servidor difere da que treinou o "
        "modelo. Retreine o modelo na aba **⚙️ Atualizar Dados → Modelo**."
    )
    st.caption(f"Detalhe técnico: {type(exc).__name__}: {exc}")
    st.stop()

with col_b:
    st.subheader("Distribuição por faixa")
    dist = (
        scored["faixa"].value_counts().rename_axis("faixa").reset_index(name="leads")
    )
    fig = px.bar(
        dist, x="leads", y="faixa", orientation="h", text="leads",
        labels={"leads": "Leads", "faixa": ""},
    )
    fig.update_layout(height=400, margin=dict(l=10, r=10))
    st.plotly_chart(fig, width="stretch")

st.divider()
st.subheader("Leads priorizados")

faixas_sel = st.multiselect(
    "Filtrar por faixa", sorted(scored["faixa"].unique()), default=[]
)
vis = scored if not faixas_sel else scored[scored["faixa"].isin(faixas_sel)]
colunas = [
    "probabilidade", "faixa", "campanha", "necessidade", "cidade", "uf",
    "concessionaria", "vendedor",
]
colunas = [c for c in colunas if c in vis.columns]
vis = vis.sort_values("probabilidade", ascending=False)[colunas]
st.dataframe(vis, width="stretch", hide_index=True)
st.caption(
    "Faixas: 🔥 Muito Quente ≥75% · 🌡️ Quente ≥50% · 🌤️ Morno ≥25% · ❄️ Frio <25%."
)
