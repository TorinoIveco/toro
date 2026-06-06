"""Inicializa o banco: aplica o DDL canônico (schema + tabelas + seed das fases).

Uso:
    python scripts/init_db.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from toro_insights.config.settings import get_settings  # noqa: E402
from toro_insights.infrastructure.db.engine import get_engine  # noqa: E402
from toro_insights.infrastructure.db.repository import CrmLeadRepository  # noqa: E402
from toro_insights.utils.logging import setup_logging  # noqa: E402


def main() -> None:
    log = setup_logging()
    settings = get_settings()
    ddl = settings.ddl_path.read_text(encoding="utf-8")
    repo = CrmLeadRepository(get_engine())
    log.info(f"Aplicando DDL: {settings.ddl_path}")
    repo.aplicar_ddl(ddl)
    mapa = repo.carregar_mapa_fases()
    log.success(f"Banco inicializado. dim_fase_negocio: {len(mapa)} fases.")


if __name__ == "__main__":
    main()
