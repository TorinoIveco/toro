"""TORO Insights — entrada da aplicação (login + navegação multipágina).

Execute com:
    streamlit run streamlit_app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Garante que o pacote toro_insights (em src/) seja encontrado
# independente de como o app for executado (local, Streamlit Cloud, etc.).
_src = Path(__file__).resolve().parent / "src"
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

import streamlit as st

from toro_insights.presentation.auth import botao_sair, require_login

st.set_page_config(page_title="TORO Insights", page_icon="🚛", layout="wide")

require_login()
botao_sair()

navegacao = st.navigation(
    [
        st.Page("views/dashboard.py", title="Dashboard Executivo", icon="📊", default=True),
        st.Page("views/funil.py", title="Funil Comercial", icon="🫙"),
        st.Page("views/campanhas.py", title="Análise de Campanhas", icon="📣"),
        st.Page("views/geografia.py", title="Inteligência Geográfica", icon="🗺️"),
        st.Page("views/scoring.py", title="Lead Scoring", icon="🎯"),
        st.Page("views/produtos.py", title="Análise de Produtos", icon="📦"),
        st.Page("views/assistente.py", title="Assistente IA", icon="🤖"),
        st.Page("views/importar.py", title="Atualizar Dados", icon="⚙️"),
    ]
)
navegacao.run()
