"""Treino do modelo de lead scoring (XGBoost) — Fase 7."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

import joblib
import pandas as pd
from loguru import logger
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

from toro_insights.analytics.kpis import base_analitica
from toro_insights.config.settings import get_settings
from toro_insights.infrastructure.db.engine import get_engine
from toro_insights.infrastructure.db.repository import CrmLeadRepository
from toro_insights.ml.features import FEATURES_CAT, FEATURES_NUM, TARGET, construir_features


@dataclass
class ResultadoTreino:
    """Métricas e metadados do treino."""

    metricas: dict[str, float]
    importancia: dict[str, float]
    n_treino: int
    n_teste: int
    treinado_em: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))


def treinar() -> ResultadoTreino:
    """Treina o XGBoost sobre crm_leads e persiste o modelo (joblib)."""
    settings = get_settings()
    repo = CrmLeadRepository(get_engine())
    df = base_analitica(repo.buscar_leads())

    y = df[TARGET].astype(int)
    if y.nunique() < 2:
        raise ValueError(
            "A base tem apenas uma classe (ex.: só vendas). O treino exige "
            "vendas E não-vendas. Carregue a base completa de leads."
        )

    X = construir_features(df)
    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.25, stratify=y, random_state=42
    )

    pos = int(y_tr.sum())
    neg = int(len(y_tr) - pos)
    modelo = XGBClassifier(
        enable_categorical=True,
        tree_method="hist",
        n_estimators=300,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.9,
        colsample_bytree=0.9,
        scale_pos_weight=(neg / pos) if pos else 1.0,
        eval_metric="auc",
        random_state=42,
    )
    modelo.fit(X_tr, y_tr)

    proba = modelo.predict_proba(X_te)[:, 1]
    pred = (proba >= 0.5).astype(int)
    metricas = {
        "accuracy": round(accuracy_score(y_te, pred), 4),
        "precision": round(precision_score(y_te, pred, zero_division=0), 4),
        "recall": round(recall_score(y_te, pred, zero_division=0), 4),
        "f1": round(f1_score(y_te, pred, zero_division=0), 4),
        "roc_auc": round(roc_auc_score(y_te, proba), 4),
    }
    importancia = {
        f: round(float(v), 4)
        for f, v in sorted(
            zip(FEATURES_CAT + FEATURES_NUM, modelo.feature_importances_),
            key=lambda t: t[1], reverse=True,
        )
    }

    resultado = ResultadoTreino(metricas, importancia, len(X_tr), len(X_te))
    settings.model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "modelo": modelo,
            "features_cat": FEATURES_CAT,
            "features_num": FEATURES_NUM,
            "metricas": metricas,
            "importancia": importancia,
            "treinado_em": resultado.treinado_em,
            "n_treino": resultado.n_treino,
            "n_teste": resultado.n_teste,
        },
        settings.model_path,
    )
    logger.success(f"Modelo salvo em {settings.model_path} | métricas: {metricas}")
    return resultado
