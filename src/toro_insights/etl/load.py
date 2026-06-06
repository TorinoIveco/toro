"""Load — persistência da quarentena e carga transacional em crm_leads."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd
from loguru import logger

from toro_insights.config.settings import get_settings


# Colunas com dados pessoais diretos (LGPD) — mascaradas no CSV de quarentena.
# O oportunidade_id (GUID) é preservado para rastreabilidade sem identificar o titular.
_PII_COLS = {"cliente_nome", "documento", "celular", "email"}


def salvar_quarentena(df_quarentena: pd.DataFrame, origem: str) -> Path | None:
    """Grava linhas inválidas em CSV para revisão manual. Retorna o caminho.

    PII (nome, documento, celular, e-mail) é mascarada antes de persistir,
    conforme LGPD — o revisor identifica o registro pelo oportunidade_id.
    """
    if df_quarentena.empty:
        return None
    settings = get_settings()
    settings.quarentena_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    destino = settings.quarentena_dir / f"quarentena_{Path(origem).stem}_{ts}.csv"

    # Mascara PII antes de gravar no disco (LGPD — minimização de dados em quarentena).
    df_export = df_quarentena.copy()
    for col in _PII_COLS:
        if col in df_export.columns:
            df_export[col] = "***"

    df_export.to_csv(destino, index=False, encoding="utf-8-sig")
    logger.warning(f"{len(df_quarentena)} linhas em quarentena -> {destino} (PII mascarada)")
    return destino
