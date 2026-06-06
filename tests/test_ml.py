"""Testes do lead scoring (partes puras, sem treino)."""

from __future__ import annotations

import pandas as pd

from toro_insights.ml import score as S
from toro_insights.ml.features import FEATURES_CAT, FEATURES_NUM, construir_features


def test_classificar_faixas():
    assert S.classificar(0.90) == "🔥 Muito Quente"
    assert S.classificar(0.60) == "🌡️ Quente"
    assert S.classificar(0.30) == "🌤️ Morno"
    assert S.classificar(0.05) == "❄️ Frio"


def test_construir_features_tipos_e_colunas():
    df = pd.DataFrame(
        [{"campanha": "A", "concessionaria": "X", "uf": "MT", "cidade": "C",
          "necessidade": "N", "status_relacionamento": "Novo", "tipo_pessoa": "PF",
          "vendedor": "V", "tempo_resposta_horas": 10.0,
          "data_criacao": pd.Timestamp("2025-03-15")}]
    )
    X = construir_features(df)
    assert list(X.columns) == FEATURES_CAT + FEATURES_NUM
    assert str(X["campanha"].dtype) == "category"
    assert X["mes_criacao"].iloc[0] == 3


def test_features_proibidas_nao_entram():
    from toro_insights.ml.features import FEATURES_PROIBIDAS
    for proibida in ("valor_faturado", "fase_negocio", "razao_status"):
        assert proibida in FEATURES_PROIBIDAS
        assert proibida not in FEATURES_CAT + FEATURES_NUM
