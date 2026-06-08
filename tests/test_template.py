"""Testes das planilhas-modelo (templates) de upload."""

from __future__ import annotations

import io

import pandas as pd

from toro_insights.domain.constants import COLUMN_MAP, NF_COLUMN_MAP, SHEET_LEADS
from toro_insights.etl.extract import extrair
from toro_insights.etl.template import template_leads, template_nf


def test_template_leads_tem_todas_as_colunas_do_parser():
    df = pd.read_excel(io.BytesIO(template_leads()), sheet_name=SHEET_LEADS)
    assert set(df.columns) == set(COLUMN_MAP.keys())
    assert len(df) == 0  # só o cabeçalho


def test_template_nf_tem_todas_as_colunas_do_parser():
    df = pd.read_excel(io.BytesIO(template_nf()), sheet_name=0)
    assert set(df.columns) == set(NF_COLUMN_MAP.keys())
    assert len(df) == 0


def test_extract_consome_template_leads_sem_perder_colunas(tmp_path):
    caminho = tmp_path / "modelo_leads.xlsx"
    caminho.write_bytes(template_leads())
    out = extrair(caminho)
    # Todas as colunas do template são mapeadas para o destino (nenhuma ausente).
    assert len(out.columns) == len(COLUMN_MAP)
    assert len(out) == 0
