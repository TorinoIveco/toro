"""Ferramentas (function calling) do assistente — SOMENTE dados agregados (LGPD).

Cada função é exposta ao modelo Gemini; ele decide quando chamá-las para buscar
recortes específicos dos dados. Nunca retornam dados pessoais.
"""

from __future__ import annotations

import json

import pandas as pd

from toro_insights.analytics import kpis as K
from toro_insights.analytics import produtos as P
from toro_insights.analytics.loader import carregar_base, carregar_produtos
from toro_insights.ml.score import carregar_modelo

_DIMS_LEAD = {"campanha", "cidade", "uf", "concessionaria", "vendedor",
              "necessidade", "status_relacionamento"}
_DIMS_PROD = {"gama", "modelo", "produto"}


def _records(df: pd.DataFrame, n: int = 20) -> list[dict]:
    """Converte um DataFrame em registros JSON-serializáveis (tipos nativos)."""
    return json.loads(json.dumps(df.head(n).to_dict(orient="records"), default=str))


def consultar_kpis_gerais() -> dict:
    """Retorna os KPIs gerais: total de leads, vendas, taxa de conversão, receita e ticket médio."""
    k = K.kpis_gerais(carregar_base())
    return {
        "leads": k.leads, "vendas": k.vendas, "conversao_pct": k.conversao_pct,
        "receita": k.receita, "ticket_medio": k.ticket_medio,
    }


def consultar_desempenho_por_dimensao(dimensao: str, min_leads: int = 5) -> list[dict]:
    """Desempenho (leads, vendas, conversão %, receita) agrupado por uma dimensão de lead.

    Args:
        dimensao: uma de campanha, cidade, uf, concessionaria, vendedor, necessidade,
            status_relacionamento.
        min_leads: volume mínimo de leads para incluir o grupo.
    """
    if dimensao not in _DIMS_LEAD:
        return [{"erro": f"dimensão inválida. Use uma de: {sorted(_DIMS_LEAD)}"}]
    return _records(K.desempenho_por(carregar_base(), dimensao, min_leads=min_leads))


def consultar_funil() -> dict:
    """Retorna o desfecho do funil: total, ganhos, perdas, em andamento e taxas (%)."""
    d = K.funil_desfecho(carregar_base())
    return {
        "total": d.total, "ganhos": d.ganhos, "perdas": d.perdas,
        "em_andamento": d.em_andamento, "taxa_ganho_pct": d.taxa_ganho,
        "taxa_perda_pct": d.taxa_perda,
    }


def consultar_produtos_por_dimensao(dimensao: str) -> list[dict]:
    """Faturamento e unidades por produto agrupados por uma dimensão.

    Args:
        dimensao: uma de gama, modelo, produto.
    """
    if dimensao not in _DIMS_PROD:
        return [{"erro": f"dimensão inválida. Use uma de: {sorted(_DIMS_PROD)}"}]
    return _records(P.por_dimensao(carregar_produtos(), dimensao))


def consultar_lead_scoring() -> dict:
    """Retorna as métricas e a importância das variáveis do modelo de lead scoring (se treinado)."""
    bundle = carregar_modelo()
    if bundle is None:
        return {"erro": "modelo de lead scoring ainda não treinado"}
    return {"metricas": bundle["metricas"], "importancia": bundle["importancia"]}


#: Lista de ferramentas registradas no agente.
FERRAMENTAS = [
    consultar_kpis_gerais,
    consultar_desempenho_por_dimensao,
    consultar_funil,
    consultar_produtos_por_dimensao,
    consultar_lead_scoring,
]
