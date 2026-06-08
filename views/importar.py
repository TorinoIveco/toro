"""Tela de administração — importar/atualizar a base a partir das planilhas."""

from __future__ import annotations

import os
import tempfile

import streamlit as st

from toro_insights.analytics import kpis as K
from toro_insights.etl import nf_pipeline, pipeline
from toro_insights.etl.template import XLSX_MIME, template_leads, template_nf
from toro_insights.presentation.ui import cabecalho, fmt_int, fmt_reais, get_dados, limpar_cache

cabecalho(
    "⚙️ Atualizar Dados",
    "Importe as planilhas do Dynamics (leads) e do ERP (faturamento) e atualize a base.",
)


def _salvar_temp(uploaded) -> str:
    """Grava o arquivo enviado num caminho temporário e retorna o path."""
    sufixo = os.path.splitext(uploaded.name)[1] or ".xlsx"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=sufixo)
    tmp.write(uploaded.getbuffer())
    tmp.close()
    return tmp.name


# ----------------------------------------------------------- Estado atual
try:
    base = get_dados()
    k = K.kpis_gerais(base)
    c1, c2, c3 = st.columns(3)
    c1.metric("Leads na base", fmt_int(k.leads))
    c2.metric("Vendas", fmt_int(k.vendas))
    c3.metric("Receita", fmt_reais(k.receita) if k.receita else "—")
except Exception as exc:  # noqa: BLE001
    st.error(f"Não foi possível ler a base atual: {exc}")

st.divider()

aba_leads, aba_nf, aba_modelo = st.tabs(
    ["📥 Leads (base principal)", "💰 Faturamento (NF)", "🧠 Modelo (treino)"]
)

# ------------------------------------------------------------- Leads
with aba_leads:
    st.markdown(
        "Carregue o export **consolidado** do Dynamics (*Leads Qualificados*, todos os status). "
        "⚠️ Esta carga **substitui toda a base de leads** (snapshot)."
    )
    st.download_button(
        "📄 Baixar planilha-modelo (Leads)",
        data=template_leads(),
        file_name="modelo_leads.xlsx",
        mime=XLSX_MIME,
        help="Planilha vazia com todas as colunas esperadas, na aba 'Leads Qualificados'. "
        "Preencha e suba abaixo.",
    )
    up = st.file_uploader("Planilha de Leads (.xlsx)", type=["xlsx"], key="up_leads")
    confirma = st.checkbox("Confirmo que este arquivo substitui a base atual de leads.")
    if up and st.button("Carregar leads", type="primary", disabled=not confirma):
        caminho = _salvar_temp(up)
        try:
            with st.spinner("Processando leads (extração → validação → carga)..."):
                res = pipeline.executar(caminho, forcar=True)
            limpar_cache()
            st.success(f"Carga {res.carga_id} concluída: {fmt_int(res.linhas_carregadas)} leads.")
            d1, d2, d3 = st.columns(3)
            d1.metric("Linhas carregadas", fmt_int(res.linhas_carregadas))
            d2.metric("Em quarentena", fmt_int(res.linhas_quarentena))
            d3.metric("Fases novas", fmt_int(len(res.fases_novas)))
            if res.fases_novas:
                st.warning(f"Fases não mapeadas (classificar depois): {res.fases_novas}")
            st.info("Após carregar os leads, atualize também o **Faturamento (NF)** na aba ao lado.")
        except Exception as exc:  # noqa: BLE001
            st.error(f"Falha na carga: {exc}")
        finally:
            os.unlink(caminho)

# ------------------------------------------------------------- NF
with aba_nf:
    st.markdown(
        "Carregue o relatório de **faturamento (itens de NF)** do ERP. "
        "Casa a receita às vendas por GUID e atualiza `valor_faturado`."
    )
    st.download_button(
        "📄 Baixar planilha-modelo (NF)",
        data=template_nf(),
        file_name="modelo_faturamento.xlsx",
        mime=XLSX_MIME,
        help="Planilha vazia com as colunas de faturamento (1 linha por item de NF). "
        "A coluna 'Oportunidade' deve ter o mesmo GUID do lead.",
    )
    up_nf = st.file_uploader("Planilha de NF (.xlsx)", type=["xlsx"], key="up_nf")
    if up_nf and st.button("Importar faturamento", type="primary"):
        caminho = _salvar_temp(up_nf)
        try:
            with st.spinner("Processando NF e agregando receita..."):
                res = nf_pipeline.executar(caminho)
            limpar_cache()
            st.success(f"NF carga {res.carga_id}: {fmt_int(res.itens)} itens importados.")
            d1, d2, d3 = st.columns(3)
            d1.metric("Vendas com receita", fmt_int(res.oportunidades_atualizadas))
            d2.metric("NFs órfãs", fmt_int(res.orfas))
            d3.metric("Em quarentena", fmt_int(res.quarentena))
            if res.orfas:
                st.warning(
                    f"{res.orfas} NF(s) sem lead correspondente — confira se a base de "
                    "leads está atualizada."
                )
        except Exception as exc:  # noqa: BLE001
            st.error(f"Falha na importação de NF: {exc}")
        finally:
            os.unlink(caminho)

# ------------------------------------------------------------- Modelo
with aba_modelo:
    st.markdown(
        "Retreina o modelo de **Lead Scoring** (XGBoost) com a base atual. "
        "Requer base com vendas **e** não-vendas."
    )
    if st.button("Treinar modelo agora", type="primary"):
        try:
            from toro_insights.ml.train import treinar

            with st.spinner("Treinando XGBoost..."):
                res = treinar()
            st.success("Modelo treinado e salvo.")
            cols = st.columns(len(res.metricas))
            for col, (nome, val) in zip(cols, res.metricas.items()):
                col.metric(nome, val)
        except ValueError as exc:
            st.warning(str(exc))
        except Exception as exc:  # noqa: BLE001
            st.error(f"Falha no treino: {exc}")
