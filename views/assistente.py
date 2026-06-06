"""Camada 6 — Assistente Inteligente (chat consultor com Gemini)."""

from __future__ import annotations

import streamlit as st

from toro_insights.assistant.agent import responder
from toro_insights.config.settings import get_settings
from toro_insights.presentation.ui import cabecalho

cabecalho(
    "🤖 Assistente Inteligente",
    "Consultor de marketing/comercial conectado aos dados reais (Gemini).",
)

if not get_settings().gemini_api_key:
    st.warning(
        "Assistente desativado: defina `GEMINI_API_KEY` no arquivo .env e reinicie o app."
    )
    st.stop()

SUGESTOES = [
    "Qual campanha devo repetir e por quê?",
    "Onde está minha maior oportunidade comercial agora?",
    "Crie uma campanha para vender mais caminhões pesados em MS.",
    "Quais cidades têm bom volume mas baixa conversão?",
]

if "chat_hist" not in st.session_state:
    st.session_state.chat_hist = []

with st.sidebar:
    st.markdown("**Sugestões:**")
    for s in SUGESTOES:
        if st.button(s, width="stretch"):
            st.session_state.pergunta_pendente = s
    if st.button("🧹 Limpar conversa", width="stretch"):
        st.session_state.chat_hist = []
        st.rerun()

# Histórico
for msg in st.session_state.chat_hist:
    with st.chat_message("user" if msg["role"] == "user" else "assistant"):
        st.markdown(msg["text"])

pergunta = st.chat_input("Pergunte ao consultor...") or st.session_state.pop("pergunta_pendente", None)

if pergunta:
    st.session_state.chat_hist.append({"role": "user", "text": pergunta})
    with st.chat_message("user"):
        st.markdown(pergunta)
    with st.chat_message("assistant"):
        with st.spinner("Analisando os dados..."):
            try:
                resposta = responder(st.session_state.chat_hist)
            except Exception as exc:  # noqa: BLE001
                resposta = f"❌ Erro ao consultar o assistente: {exc}"
        st.markdown(resposta)
    st.session_state.chat_hist.append({"role": "assistant", "text": resposta})
