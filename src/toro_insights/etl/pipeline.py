"""Pipeline ETL — orquestra extract → validate → transform → load."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

from loguru import logger

from toro_insights.config.settings import get_settings
from toro_insights.domain.constants import BUCKET_NAO_MAPEADO
from toro_insights.etl import extract, load, transform
from toro_insights.infrastructure.db.engine import get_engine
from toro_insights.infrastructure.db.repository import CrmLeadRepository
from toro_insights.utils.logging import setup_logging


@dataclass
class ResultadoCarga:
    """Resumo do resultado de uma execução do ETL."""

    carga_id: int | None
    linhas_carregadas: int
    linhas_quarentena: int
    fases_novas: list[str]
    quarentena_path: Path | None


def executar(caminho_excel: Path | str, snapshot: date | None = None,
             forcar: bool = False) -> ResultadoCarga:
    """Executa o pipeline completo para um arquivo Excel.

    Args:
        caminho_excel: arquivo exportado do Dynamics.
        snapshot: data do snapshot (default: hoje).
        forcar: se True, recarrega mesmo que o hash do arquivo já exista.
    """
    setup_logging()
    settings = get_settings()
    caminho = Path(caminho_excel)
    snapshot = snapshot or date.today()
    repo = CrmLeadRepository(get_engine())

    # 1) Extract
    df_raw = extract.extrair(caminho)
    file_hash = extract.hash_arquivo(caminho)

    if not forcar and repo.hash_ja_carregado(file_hash):
        logger.warning("Arquivo com hash idêntico já carregado. Use forcar=True para recarregar.")
        return ResultadoCarga(None, 0, 0, [], None)

    # 2) Validate
    df_ok, df_quar = transform.validar(df_raw)
    quar_path = load.salvar_quarentena(df_quar, caminho.name)

    # 3) Garante integridade referencial das fases (registra novas como 'A classificar')
    mapa = repo.carregar_mapa_fases()
    conhecidas = set(mapa["fase_original"])
    novas = sorted(
        f for f in df_ok.get("fase_negocio", []).dropna().unique() if f not in conhecidas
    ) if not df_ok.empty else []
    if novas:
        logger.warning(f"Fases não mapeadas serão marcadas como '{BUCKET_NAO_MAPEADO}': {novas}")
        repo.registrar_fases_nao_mapeadas(novas)
        mapa = repo.carregar_mapa_fases()

    # 4) Transform
    df_final = transform.transformar(df_ok, mapa, settings.documento_hash_salt)

    # 5) Load (transacional, com auditoria)
    carga_id = repo.iniciar_carga(caminho.name, snapshot, file_hash)
    try:
        df_final["carga_id"] = carga_id
        n = repo.truncar_e_carregar(df_final)
        repo.finalizar_carga(carga_id, n, "concluida")
        logger.success(f"Carga {carga_id} concluída: {n} linhas em crm_leads.")
    except Exception:
        repo.finalizar_carga(carga_id, 0, "falha")
        logger.exception("Falha na carga; base anterior preservada (transação revertida).")
        raise

    return ResultadoCarga(carga_id, n, len(df_quar), novas, quar_path)
