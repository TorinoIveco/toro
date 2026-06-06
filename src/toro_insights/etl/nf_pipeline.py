"""Pipeline de integração de NF — itens de faturamento + agregação de receita."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

from loguru import logger

from toro_insights.etl import load, nf_extract
from toro_insights.infrastructure.db.engine import get_engine
from toro_insights.infrastructure.db.repository import CrmLeadRepository
from toro_insights.utils.logging import setup_logging


@dataclass
class ResultadoNF:
    """Resumo da carga de NF."""

    carga_id: int | None
    itens: int
    oportunidades_atualizadas: int
    orfas: int
    quarentena: int


def executar(caminho: Path | str, snapshot: date | None = None) -> ResultadoNF:
    """Carrega itens de NF e agrega o Valor Faturado em crm_leads (RN-13)."""
    setup_logging()
    caminho = Path(caminho)
    snapshot = snapshot or date.today()
    repo = CrmLeadRepository(get_engine())

    df_raw = nf_extract.extrair_nf(caminho)
    df_ok, df_quar = nf_extract.validar_nf(df_raw)
    load.salvar_quarentena(df_quar, f"nf_{caminho.stem}")

    carga_id = repo.iniciar_carga(caminho.name, snapshot, hash_arquivo="nf")
    df_ok["carga_id"] = carga_id
    try:
        n = repo.truncar_e_carregar_nf(df_ok)
        atualizadas = repo.agregar_valor_faturado()
        orfas = repo.contar_nf_orfas()
        repo.finalizar_carga(carga_id, n, "concluida")
        logger.success(
            f"NF carga {carga_id}: {n} itens; {atualizadas} oportunidades com receita; "
            f"{orfas} órfãs."
        )
    except Exception:
        repo.finalizar_carga(carga_id, 0, "falha")
        logger.exception("Falha na carga de NF; transação revertida.")
        raise

    return ResultadoNF(carga_id, n, atualizadas, orfas, len(df_quar))
