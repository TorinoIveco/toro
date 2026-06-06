"""Testes da analytics de produtos (Tela 6)."""

from __future__ import annotations

import pandas as pd

from toro_insights.analytics import produtos as P


def _df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"produto": "S-Way 540", "gama": "Pesado", "modelo": "S-Way",
             "quantidade": 2, "valor_total": 1480000.0, "cidade": "RONDONÓPOLIS"},
            {"produto": "Tector 240", "gama": "Médio", "modelo": "Tector",
             "quantidade": 1, "valor_total": 350000.0, "cidade": "CUIABÁ"},
            {"produto": "S-Way 540", "gama": "Pesado", "modelo": "S-Way",
             "quantidade": 1, "valor_total": 740000.0, "cidade": "RONDONÓPOLIS"},
        ]
    )


def test_kpis_produtos():
    k = P.kpis_produtos(_df())
    assert k.unidades == 4
    assert k.receita == 2570000.0
    assert k.modelos == 2
    assert k.produtos == 2
    assert k.ticket_unidade == round(2570000.0 / 4, 2)


def test_por_dimensao_gama_ordenada_por_receita():
    out = P.por_dimensao(_df(), "gama")
    assert list(out["gama"]) == ["Pesado", "Médio"]
    assert out.iloc[0]["receita"] == 2220000.0
    assert out.iloc[0]["unidades"] == 3


def test_por_dimensao_top():
    out = P.por_dimensao(_df(), "produto", top=1)
    assert len(out) == 1
    assert out.iloc[0]["produto"] == "S-Way 540"


def test_matriz_gama_cidade():
    m = P.matriz_gama_cidade(_df())
    assert m.loc["RONDONÓPOLIS", "Pesado"] == 3
    assert m.loc["CUIABÁ", "Médio"] == 1


def test_vazio():
    k = P.kpis_produtos(pd.DataFrame())
    assert k.receita == 0.0 and k.unidades == 0.0
