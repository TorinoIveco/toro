"""Login simples para a persona única (Gerente de Marketing)."""

from __future__ import annotations

import streamlit as st

from toro_insights.config.settings import get_settings


def require_login() -> None:
    """Bloqueia o app até autenticação. Usa credenciais do .env.

    Implementação proporcional ao porte (persona única, app interno). Para
    múltiplos usuários/perfis, migrar para um provedor de identidade.
    """
    if st.session_state.get("autenticado"):
        return

    settings = get_settings()
    st.title("🚛 TORO Insights")
    st.caption("Inteligência comercial e de marketing — acesso restrito")

    with st.form("login"):
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        ok = st.form_submit_button("Entrar", width="stretch")

    if ok:
        if usuario == settings.app_usuario and senha == settings.app_senha:
            st.session_state["autenticado"] = True
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos.")
    st.stop()


def botao_sair() -> None:
    """Renderiza um botão de logout na sidebar."""
    if st.sidebar.button("Sair", width="stretch"):
        st.session_state.clear()
        st.rerun()
