"""Extract — leitura do Excel exportado do Dynamics."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd
from loguru import logger

from toro_insights.domain.constants import COLUMN_MAP, SHEET_LEADS


def hash_arquivo(caminho: Path) -> str:
    """SHA-256 do arquivo para auditoria/detecção de recarga (RN-04)."""
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(8192), b""):
            h.update(bloco)
    return h.hexdigest()


def extrair(caminho: Path | str) -> pd.DataFrame:
    """Lê a aba de leads e renomeia colunas para o padrão de destino.

    Mantém apenas as colunas mapeadas em COLUMN_MAP (descarta checksum, código
    e a 2ª 'Data de Modificação' duplicada).
    """
    caminho = Path(caminho)
    logger.info(f"Extraindo Excel: {caminho.name}")

    sheets = pd.ExcelFile(caminho).sheet_names
    aba = SHEET_LEADS if SHEET_LEADS in sheets else sheets[0]
    if aba != SHEET_LEADS:
        logger.warning(f"Aba '{SHEET_LEADS}' não encontrada; usando '{aba}'.")

    df = pd.read_excel(caminho, sheet_name=aba)

    presentes = {orig: dest for orig, dest in COLUMN_MAP.items() if orig in df.columns}
    ausentes = set(COLUMN_MAP) - set(presentes)
    if ausentes:
        logger.warning(f"Colunas esperadas ausentes no arquivo: {sorted(ausentes)}")

    df = df[list(presentes)].rename(columns=presentes)
    logger.info(f"Extraídas {len(df)} linhas / {len(df.columns)} colunas mapeadas.")
    return df
