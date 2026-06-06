"""Scoring de leads com o modelo treinado — Fase 7."""

from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd

from toro_insights.config.settings import get_settings
from toro_insights.ml.features import construir_features

#: Faixas de classificação por probabilidade de conversão.
FAIXAS = [
    (0.75, "🔥 Muito Quente"),
    (0.50, "🌡️ Quente"),
    (0.25, "🌤️ Morno"),
    (0.00, "❄️ Frio"),
]


def carregar_modelo() -> dict | None:
    """Carrega o bundle do modelo (ou None se ainda não treinado)."""
    caminho: Path = get_settings().model_path
    if not caminho.exists():
        return None
    return joblib.load(caminho)


def classificar(prob: float) -> str:
    """Mapeia a probabilidade para uma faixa (Muito Quente ... Frio)."""
    for limite, rotulo in FAIXAS:
        if prob >= limite:
            return rotulo
    return FAIXAS[-1][1]


def pontuar(df: pd.DataFrame, bundle: dict) -> pd.DataFrame:
    """Adiciona `probabilidade` (%) e `faixa` a cada lead."""
    if df.empty:
        return df.assign(probabilidade=[], faixa=[])
    X = construir_features(df)
    proba = bundle["modelo"].predict_proba(X)[:, 1]
    out = df.copy()
    out["probabilidade"] = (proba * 100).round(1)
    out["faixa"] = [classificar(p) for p in proba]
    return out
