"""Testes da camada de analytics (KPIs)."""

from __future__ import annotations

import pandas as pd

from toro_insights.analytics import kpis as K


def _df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"oportunidade_id": "1", "target_ml": 1, "bucket_funil": "Ganho",
             "ordem_funil": 7, "campanha": "A", "cidade": "X", "uf": "MT",
             "ano": 2025, "valor_faturado": 100.0},
            {"oportunidade_id": "2", "target_ml": 0, "bucket_funil": "Perda",
             "ordem_funil": 99, "campanha": "A", "cidade": "X", "uf": "MT",
             "ano": 2025, "valor_faturado": None},
            {"oportunidade_id": "3", "target_ml": 0, "bucket_funil": "Descartar",
             "ordem_funil": 0, "campanha": "B", "cidade": "Y", "uf": "MS",
             "ano": 2025, "valor_faturado": None},
            {"oportunidade_id": "4", "target_ml": 1, "bucket_funil": "Ganho",
             "ordem_funil": 7, "campanha": "B", "cidade": None, "uf": "MS",
             "ano": 2024, "valor_faturado": 50.0},
        ]
    )


def test_base_analitica_remove_descartar():
    assert len(K.base_analitica(_df())) == 3


def test_kpis_gerais():
    base = K.base_analitica(_df())
    k = K.kpis_gerais(base)
    assert k.leads == 3
    assert k.vendas == 2
    assert k.conversao_pct == round(100 * 2 / 3, 2)
    assert k.receita == 150.0
    assert k.ticket_medio == 75.0


def test_conversao_por_campanha_ordenada():
    base = K.base_analitica(_df())
    out = K.conversao_por(base, "campanha")
    assert list(out["campanha"]) == ["B", "A"]  # B=100%, A=50%
    assert out.iloc[0]["conversao_pct"] == 100.0


def test_conversao_por_cidade_rotula_nulo():
    base = K.base_analitica(_df())
    out = K.conversao_por(base, "cidade")
    assert K.ROTULO_NULO in set(out["cidade"])


def test_desempenho_por_inclui_receita():
    base = K.base_analitica(_df())
    out = K.desempenho_por(base, "campanha")
    assert {"leads", "vendas", "conversao_pct", "receita", "ticket_medio"} <= set(out.columns)
    # campanha B: 1 venda (R$50) + 0; campanha A: 1 venda (R$100)
    receita_total = out["receita"].fillna(0).sum()
    assert receita_total == 150.0


def test_insights_campanhas_gera_textos():
    base = K.base_analitica(_df())
    msgs = K.insights_campanhas(base, min_leads=1)
    assert len(msgs) >= 2
    assert any("conversão" in m for m in msgs)


def test_funil_desfecho():
    base = K.base_analitica(_df())
    d = K.funil_desfecho(base)
    assert d.total == 3 and d.ganhos == 2
