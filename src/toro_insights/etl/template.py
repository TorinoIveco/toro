"""Geração das planilhas-modelo (templates) para upload de Leads e NF.

Os cabeçalhos são derivados das MESMAS constantes que o extract usa para ler
(``COLUMN_MAP`` / ``NF_COLUMN_MAP``), garantindo que o modelo baixado nunca
fique dessincronizado do parser.
"""

from __future__ import annotations

from io import BytesIO

import pandas as pd

from toro_insights.domain.constants import COLUMN_MAP, NF_COLUMN_MAP, SHEET_LEADS

#: MIME type de arquivos .xlsx (para o botão de download do Streamlit).
XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _montar_xlsx(cabecalhos: list[str], sheet_name: str) -> bytes:
    """Gera um .xlsx em memória contendo apenas a linha de cabeçalho."""
    df = pd.DataFrame(columns=cabecalhos)
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name=sheet_name[:31], index=False)
        # Ajusta a largura das colunas ao tamanho do cabeçalho (legibilidade).
        worksheet = writer.sheets[sheet_name[:31]]
        for i, col in enumerate(cabecalhos):
            worksheet.set_column(i, i, max(14, min(len(col) + 2, 50)))
    buffer.seek(0)
    return buffer.getvalue()


def template_leads() -> bytes:
    """Planilha-modelo da base de Leads (aba 'Leads Qualificados')."""
    return _montar_xlsx(list(COLUMN_MAP.keys()), SHEET_LEADS)


def template_nf() -> bytes:
    """Planilha-modelo do relatório de Faturamento (itens de NF)."""
    return _montar_xlsx(list(NF_COLUMN_MAP.keys()), "Faturamento")
