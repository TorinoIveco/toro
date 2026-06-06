"""Carregamento de dados para a camada de apresentação."""

from __future__ import annotations

import pandas as pd

from toro_insights.analytics.kpis import base_analitica
from toro_insights.infrastructure.db.engine import get_engine
from toro_insights.infrastructure.db.repository import CrmLeadRepository


def carregar_base() -> pd.DataFrame:
    """Lê crm_leads e devolve a base analítica (exclui 'Descartar', RN-05)."""
    repo = CrmLeadRepository(get_engine())
    df = repo.buscar_leads()
    return base_analitica(df)


def carregar_produtos() -> pd.DataFrame:
    """Itens de NF enriquecidos com geografia/loja para a Tela de Produtos."""
    repo = CrmLeadRepository(get_engine())
    return repo.buscar_nf_enriquecido()
