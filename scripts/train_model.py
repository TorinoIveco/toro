"""Treina o modelo de lead scoring (XGBoost) e salva em models/.

Uso (contra o banco do .env):
    python scripts/train_model.py

Para treinar contra outro banco (ex.: local com base completa):
    DATABASE_URL="postgresql+psycopg://user@localhost:5432/toro_insights" python scripts/train_model.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from toro_insights.ml.train import treinar  # noqa: E402
from toro_insights.utils.logging import setup_logging  # noqa: E402


def main() -> None:
    setup_logging()
    res = treinar()
    print("\n=== TREINO CONCLUÍDO ===")
    print(f"treino/teste: {res.n_treino} / {res.n_teste}")
    print("Métricas:")
    for k, v in res.metricas.items():
        print(f"  {k:10s}: {v}")
    print("Top 5 importância de variáveis:")
    for f, v in list(res.importancia.items())[:5]:
        print(f"  {f:22s}: {v}")


if __name__ == "__main__":
    main()
