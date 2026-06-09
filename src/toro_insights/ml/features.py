"""Engenharia de features para o lead scoring (RN-10: sem vazamento)."""

from __future__ import annotations

import pandas as pd

#: Features categóricas — sinais conhecidos no início do lead.
FEATURES_CAT = [
    "campanha",
    "concessionaria",
    "uf",
    "cidade",
    "necessidade",
    "produto_interesse",
    "modelo_interesse",
    "status_relacionamento",
    "tipo_pessoa",
    "vendedor",
]

#: Features numéricas.
FEATURES_NUM = ["tempo_resposta_horas", "mes_criacao"]

TARGET = "target_ml"

#: Rótulo para valores ausentes em features categóricas. Garante que uma coluna
#: totalmente vazia (ex.: produto_interesse antes de a base ter esse dado) tenha
#: ao menos 1 categoria — o XGBoost falha com categóricas de zero categorias.
ROTULO_CAT_NULO = "(sem informacao)"

#: Colunas PROIBIDAS como feature (RN-10) — dependem do desfecho da venda.
FEATURES_PROIBIDAS = [
    "valor_faturado", "data_prevista_faturamento", "razao_status",
    "fase_negocio", "bucket_funil", "ordem_funil", "venda_concretizada",
    "is_perda", "data_modificacao",
]


def construir_features(df: pd.DataFrame) -> pd.DataFrame:
    """Monta a matriz X com tipos corretos (categóricas como `category`)."""
    df = df.copy()
    df["mes_criacao"] = pd.to_datetime(df["data_criacao"], errors="coerce").dt.month
    for c in FEATURES_CAT:
        if c not in df.columns:
            df[c] = None
        # fillna com placeholder evita categóricas de zero categorias (XGBoost falha).
        df[c] = df[c].astype("string").fillna(ROTULO_CAT_NULO).astype("category")
    for c in FEATURES_NUM:
        if c not in df.columns:
            df[c] = pd.NA
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df[FEATURES_CAT + FEATURES_NUM]
