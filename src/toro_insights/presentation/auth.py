"""Login e perfis de acesso (RBAC simples).

Perfis:
- ``gerente``: acesso total (inclui a tela "Atualizar Dados").
- ``assistente``: acesso restrito (sem a tela "Atualizar Dados").

A lógica de autenticação (``autenticar``) é pura/testável, separada da UI.
"""

from __future__ import annotations

import streamlit as st

from toro_insights.config.settings import Settings, get_settings

PERFIL_GERENTE = "gerente"
PERFIL_ASSISTENTE = "assistente"


def autenticar(usuario: str, senha: str, settings: Settings) -> str | None:
    """Valida credenciais e retorna o perfil (``gerente``/``assistente``) ou None.

    Comparações exatas; o perfil assistente só existe se configurado no ambiente.
    """
    if usuario == settings.app_usuario and senha == settings.app_senha:
        return PERFIL_GERENTE
    if (
        settings.app_assistente_usuario
        and usuario == settings.app_assistente_usuario
        and senha == settings.app_assistente_senha
    ):
        return PERFIL_ASSISTENTE
    return None


def require_login() -> None:
    """Bloqueia o app até autenticação. Guarda o perfil em ``session_state``."""
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
        perfil = autenticar(usuario, senha, settings)
        if perfil:
            st.session_state["autenticado"] = True
            st.session_state["perfil"] = perfil
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos.")
    st.stop()


def perfil_atual() -> str:
    """Perfil do usuário logado (default ``gerente`` por retrocompatibilidade)."""
    return st.session_state.get("perfil", PERFIL_GERENTE)


def eh_gerente() -> bool:
    """True se o usuário logado tem perfil de gerente (acesso total)."""
    return perfil_atual() == PERFIL_GERENTE


def botao_sair() -> None:
    """Mostra o usuário/perfil logado e um botão de logout na sidebar."""
    perfil = perfil_atual()
    rotulo = "👑 Gerente" if perfil == PERFIL_GERENTE else "🙋 Assistente"
    st.sidebar.caption(f"Perfil: {rotulo}")
    if st.sidebar.button("Sair", width="stretch"):
        st.session_state.clear()
        st.rerun()
