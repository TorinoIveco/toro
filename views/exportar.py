"""Tela — Exportar contatos para o Brevo (e-mail marketing).

Gera a lista server-side a partir do CRM, priorizada pelo Lead Scoring
(potencial de conversão). Nenhum dado pessoal sai para terceiros.
"""

from __future__ import annotations

import streamlit as st

from toro_insights.export import brevo
from toro_insights.ml import score as S
from toro_insights.presentation.ui import cabecalho, fmt_int, get_dados

cabecalho(
    "📧 Exportar Contatos (Brevo)",
    "Gera a lista de e-mail marketing direto do CRM, priorizada por potencial. "
    "Os dados não passam por nenhum serviço externo.",
)

df = get_dados()
if df.empty:
    st.warning("Base vazia. Carregue os leads em **⚙️ Atualizar Dados**.")
    st.stop()

# ----------------------------------------------------- Potencial (Lead Scoring)
bundle = S.carregar_modelo()
tem_score = False
if bundle is not None:
    try:
        df = S.pontuar(df, bundle)
        df = df.sort_values("probabilidade", ascending=False)
        tem_score = True
    except Exception:  # noqa: BLE001
        st.info("Modelo de scoring indisponível — exportando sem priorização por potencial.")

# --------------------------------------------------------------------- Filtros
st.subheader("Segmentação")
c1, c2 = st.columns(2)

with c1:
    if tem_score:
        prob_min = st.slider(
            "Potencial mínimo (probabilidade de conversão %)",
            min_value=0, max_value=100, value=0, step=5,
            help="0 inclui todos; aumente para focar nos leads mais quentes.",
        )
    else:
        prob_min = 0
    excluir_clientes = st.checkbox(
        "Excluir quem já comprou (Ganho e Entregue)", value=True
    )

with c2:
    def _multi(label: str, coluna: str) -> list:
        if coluna not in df.columns:
            return []
        opcoes = sorted(str(x) for x in df[coluna].dropna().unique())
        return st.multiselect(label, opcoes)

    ano_sel = _multi("Ano", "ano")
    uf_sel = _multi("Estado (UF)", "uf")
    campanha_sel = _multi("Campanha", "campanha")
    produto_sel = _multi("Produto de Interesse", "produto_interesse")
    modelo_sel = _multi("Modelo de Interesse", "modelo_interesse")

# ---------------------------------------------------------------- Aplica filtros
sel = df.copy()
if tem_score and prob_min > 0:
    sel = sel[sel["probabilidade"] >= prob_min]
if excluir_clientes and "venda_concretizada" in sel.columns:
    sel = sel[~sel["venda_concretizada"].fillna(False).astype(bool)]
if ano_sel:
    sel = sel[sel["ano"].astype(str).isin(ano_sel)]
if uf_sel:
    sel = sel[sel["uf"].astype(str).isin(uf_sel)]
if campanha_sel:
    sel = sel[sel["campanha"].astype(str).isin(campanha_sel)]
if produto_sel:
    sel = sel[sel["produto_interesse"].astype(str).isin(produto_sel)]
if modelo_sel:
    sel = sel[sel["modelo_interesse"].astype(str).isin(modelo_sel)]

# ---------------------------------------------------------- Monta planilha Brevo
planilha = brevo.montar_planilha_brevo(sel)

st.divider()
st.subheader("Resultado")
m1, m2, m3 = st.columns(3)
m1.metric("Leads no filtro", fmt_int(len(sel)))
m2.metric("Contatos exportáveis", fmt_int(len(planilha)), help="Com e-mail válido, sem duplicar e-mail.")
com_tel = int((planilha["WHATSAPP"] != "").sum()) if not planilha.empty else 0
m3.metric("Com telefone", fmt_int(com_tel))

if planilha.empty:
    st.warning("Nenhum contato com e-mail válido no filtro atual. Ajuste a segmentação.")
    st.stop()

st.caption("Prévia (10 primeiras linhas) — o arquivo completo é gerado no download.")
st.dataframe(planilha.head(10), width="stretch", hide_index=True)

col_a, col_b = st.columns(2)
col_a.download_button(
    "⬇️ Baixar CSV (Brevo)",
    data=brevo.gerar_csv(planilha),
    file_name="contatos_brevo.csv",
    mime="text/csv",
    type="primary",
    width="stretch",
)
col_b.download_button(
    "⬇️ Baixar XLSX",
    data=brevo.gerar_xlsx(planilha),
    file_name="contatos_brevo.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    width="stretch",
)

st.info(
    "⚖️ **LGPD:** use estes contatos apenas para a finalidade de relacionamento/marketing "
    "da concessionária, com base legal adequada. Garanta o **descadastro (opt-out)** em todo "
    "envio (o Brevo inclui automaticamente) e não reutilize a lista para outros fins."
)
