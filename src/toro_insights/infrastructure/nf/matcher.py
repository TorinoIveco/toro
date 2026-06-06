"""RN-13 — casa o Valor Faturado (NF) à oportunidade por documento + data.

ATENÇÃO: o formato exato do arquivo de NF ainda é pendência (P2 do SRS). Este
módulo assume um DataFrame com colunas: `documento`, `data_nf`, `valor_faturado`.
Como CPF/CNPJ pode repetir, o casamento é fuzzy: escolhe a oportunidade com a
data mais próxima dentro da janela; casos ambíguos são sinalizados, não chutados.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd
from loguru import logger

from toro_insights.config.settings import get_settings
from toro_insights.domain import rules
from toro_insights.infrastructure.db.repository import CrmLeadRepository


@dataclass
class ResultadoNF:
    """Resumo do casamento de NFs."""

    casados: int = 0
    ambiguos: list[dict] = field(default_factory=list)
    sem_match: list[dict] = field(default_factory=list)


def casar_notas(df_nf: pd.DataFrame, repo: CrmLeadRepository) -> ResultadoNF:
    """Casa cada NF a uma oportunidade e grava `valor_faturado`."""
    settings = get_settings()
    janela = pd.Timedelta(days=settings.nf_match_janela_dias)
    salt = settings.documento_hash_salt
    resultado = ResultadoNF()

    leads = repo.buscar_leads()
    leads["data_ref"] = pd.to_datetime(leads["data_prevista_faturamento"], errors="coerce")

    df_nf = df_nf.copy()
    df_nf["doc_hash"] = df_nf["documento"].apply(lambda d: rules.hash_documento(d, salt))
    df_nf["data_nf"] = pd.to_datetime(df_nf["data_nf"], dayfirst=True, errors="coerce")

    for nf in df_nf.to_dict(orient="records"):
        candidatos = leads[leads["documento_hash"] == nf["doc_hash"]].copy()
        if candidatos.empty:
            resultado.sem_match.append(nf)
            continue

        candidatos["dist"] = (candidatos["data_ref"] - nf["data_nf"]).abs()
        dentro = candidatos[candidatos["dist"] <= janela].sort_values("dist")
        if dentro.empty:
            resultado.sem_match.append(nf)
            continue
        if len(dentro) > 1 and dentro["dist"].nsmallest(2).nunique() == 1:
            resultado.ambiguos.append(nf)  # empate de datas -> revisar manualmente
            continue

        alvo = dentro.iloc[0]
        repo.atualizar_valor_faturado(alvo["oportunidade_id"], float(nf["valor_faturado"]))
        resultado.casados += 1

    logger.info(
        f"NF: {resultado.casados} casadas, {len(resultado.ambiguos)} ambíguas, "
        f"{len(resultado.sem_match)} sem match."
    )
    return resultado
