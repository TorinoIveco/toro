"""Importa o relatório de NF (itens) e agrega o Valor Faturado nas vendas.

Uso:
    python scripts/run_nf.py "/caminho/Leads Qualificados.xlsx"
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from toro_insights.etl import nf_pipeline  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Integração de NF — TORO Insights")
    parser.add_argument("arquivo", help="Relatório de faturamento (Excel) com colunas de NF")
    args = parser.parse_args()

    res = nf_pipeline.executar(args.arquivo)
    print("\n=== INTEGRAÇÃO DE NF ===")
    print(f"carga_id...................: {res.carga_id}")
    print(f"itens de NF carregados.....: {res.itens}")
    print(f"oportunidades com receita..: {res.oportunidades_atualizadas}")
    print(f"NFs órfãs (sem lead).......: {res.orfas}")
    print(f"itens em quarentena........: {res.quarentena}")


if __name__ == "__main__":
    main()
