"""Testes da transformação (exigem pandas)."""

from __future__ import annotations

import pandas as pd

from toro_insights.etl import transform


def _mapa_fases() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"fase_original": "Ganho e Entregue", "bucket_funil": "Ganho", "ordem_funil": 7,
             "is_ganho": True, "is_perda": False, "is_descartar": False},
            {"fase_original": "Perdida", "bucket_funil": "Perda", "ordem_funil": 99,
             "is_ganho": False, "is_perda": True, "is_descartar": False},
        ]
    )


def _df_valido() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "oportunidade_id": "93b910b1-8f01-eb11-a813-000d3a888c2d",
                "data_criacao": pd.Timestamp("2020-09-28 09:37:04"),
                "data_modificacao": pd.Timestamp("2024-09-16 13:04:55"),
                "data_associacao_vendedor": pd.Timestamp("2020-09-29 15:14:12"),
                "data_primeiro_atendimento": pd.Timestamp("2020-09-30 10:00:00"),
                "data_prevista_faturamento": None,
                "documento": "079.456.789-55",
                "fase_negocio": "Ganho e Entregue",
                "cidade": "primavera do leste", "uf": "mt",
                "campanha": "Novo Iveco Daily", "concessionaria": "TORINO",
                "vendedor": None, "necessidade": None, "status_relacionamento": "Com Relacionamento",
                "razao_status": "Ganho(a)", "celular": None, "email": None, "cliente_nome": "FULANO",
                "tempo_atendimento_horas": 100,
            }
        ]
    )


def test_target_e_bucket():
    out = transform.transformar(_df_valido(), _mapa_fases(), salt="t")
    row = out.iloc[0]
    assert row["venda_concretizada"] is True or row["venda_concretizada"] == True  # noqa: E712
    assert row["target_ml"] == 1
    assert row["bucket_funil"] == "Ganho"
    assert row["ano"] == 2020
    assert row["cidade"] == "PRIMAVERA DO LESTE"
    assert row["uf"] == "MT"


def test_documento_hash_e_durencoes():
    out = transform.transformar(_df_valido(), _mapa_fases(), salt="t")
    row = out.iloc[0]
    assert row["documento_hash"] is not None
    assert row["dias_no_funil"] > 0
    assert row["flag_data_inconsistente"] in (True, False)


def test_df_vazio_retorna_colunas():
    out = transform.transformar(pd.DataFrame(), _mapa_fases(), salt="t")
    assert out.empty
    assert "target_ml" in out.columns


def test_produto_e_modelo_de_interesse():
    df = _df_valido()
    df["produto_interesse"] = "  Caminhão  "
    df["modelo_interesse"] = "S-Way"
    out = transform.transformar(df, _mapa_fases(), salt="t")
    row = out.iloc[0]
    assert row["produto_interesse"] == "Caminhão"  # strip aplicado
    assert row["modelo_interesse"] == "S-Way"


def test_retrocompat_sem_colunas_de_interesse():
    # Planilha antiga (sem as colunas novas) não deve quebrar; colunas viram NA.
    out = transform.transformar(_df_valido(), _mapa_fases(), salt="t")
    assert "produto_interesse" in out.columns
    assert "modelo_interesse" in out.columns
    assert pd.isna(out.iloc[0]["produto_interesse"])
