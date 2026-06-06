"""Extract + validação do relatório de faturamento (itens de NF)."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
from loguru import logger
from pydantic import ValidationError

from toro_insights.domain.constants import NF_COLUMN_MAP
from toro_insights.schemas.nf_item import NfItemRaw


def _norm(s: str) -> str:
    """Normaliza cabeçalho: trim + colapsa espaços múltiplos (ex.: 'Valor  Un.')."""
    return re.sub(r"\s+", " ", str(s).strip())


def extrair_nf(caminho: Path | str) -> pd.DataFrame:
    """Lê o relatório de NF e mantém apenas as colunas de faturamento mapeadas."""
    caminho = Path(caminho)
    logger.info(f"Extraindo NF: {caminho.name}")
    df = pd.read_excel(caminho, sheet_name=0)

    # Casamento tolerante a espaços nos cabeçalhos.
    norm_para_dest = {_norm(orig): dest for orig, dest in NF_COLUMN_MAP.items()}
    presentes = {col: norm_para_dest[_norm(col)] for col in df.columns if _norm(col) in norm_para_dest}

    ausentes = set(NF_COLUMN_MAP.values()) - set(presentes.values())
    if ausentes:
        logger.warning(f"Colunas de NF ausentes: {sorted(ausentes)}")

    df = df[list(presentes)].rename(columns=presentes)
    logger.info(f"Extraídos {len(df)} itens de NF.")
    return df


def validar_nf(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Valida cada item com Pydantic. Retorna (válidos, quarentena)."""
    if "data_emissao" in df.columns:
        df["data_emissao"] = pd.to_datetime(df["data_emissao"], dayfirst=True, errors="coerce")

    validos: list[dict] = []
    invalidos: list[dict] = []
    for raw in df.to_dict(orient="records"):
        limpo = {k: (None if pd.isna(v) else v) for k, v in raw.items()}
        try:
            item = NfItemRaw(**limpo)
            d = item.model_dump()
            d["oportunidade_id"] = str(d["oportunidade_id"])
            d["data_emissao"] = (
                d["data_emissao"].date() if d["data_emissao"] is not None else None
            )
            validos.append(d)
        except ValidationError as exc:
            invalidos.append({**raw, "_erro": "; ".join(e["msg"] for e in exc.errors())})

    logger.info(f"NF — validação: {len(validos)} itens, {len(invalidos)} em quarentena.")
    df_ok = pd.DataFrame(validos) if validos else pd.DataFrame(columns=list(NF_COLUMN_MAP.values()))
    return df_ok, pd.DataFrame(invalidos)
