"""Executa o pipeline ETL para um arquivo Excel do Dynamics.

Uso:
    python scripts/run_etl.py "/caminho/Leads Qualificados.xlsx"
    python scripts/run_etl.py arquivo.xlsx --forcar --snapshot 2026-06-01
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from toro_insights.etl import pipeline  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="ETL TORO Insights")
    parser.add_argument("arquivo", help="Caminho do Excel exportado do Dynamics")
    parser.add_argument("--snapshot", help="Data do snapshot (YYYY-MM-DD)", default=None)
    parser.add_argument("--forcar", action="store_true", help="Recarrega mesmo se hash existir")
    args = parser.parse_args()

    snap = date.fromisoformat(args.snapshot) if args.snapshot else None
    res = pipeline.executar(args.arquivo, snapshot=snap, forcar=args.forcar)

    print("\n=== RESULTADO DA CARGA ===")
    print(f"carga_id............: {res.carga_id}")
    print(f"linhas carregadas...: {res.linhas_carregadas}")
    print(f"linhas em quarentena: {res.linhas_quarentena}")
    print(f"fases novas.........: {res.fases_novas or 'nenhuma'}")
    print(f"quarentena..........: {res.quarentena_path or 'n/a'}")


if __name__ == "__main__":
    main()
