"""Transform — validação, limpeza e engenharia de atributos.

Saída: DataFrame pronto para `toro.crm_leads` (sem `carga_id`/`valor_faturado`,
preenchidos depois pelo pipeline e pela integração de NF).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from loguru import logger
from pydantic import ValidationError

from toro_insights.domain import rules
from toro_insights.domain.constants import DATE_COLUMNS
from toro_insights.schemas.lead_raw import LeadRaw

#: Colunas finais gravadas em crm_leads pelo transform.
_COLUNAS_SAIDA = [
    "oportunidade_id", "data_criacao", "data_modificacao", "data_associacao_vendedor",
    "data_primeiro_atendimento", "data_prevista_faturamento", "ano", "cliente_nome",
    "documento", "documento_hash", "tipo_pessoa", "celular", "email", "campanha",
    "concessionaria", "vendedor", "cidade", "uf", "necessidade", "status_relacionamento",
    "fase_negocio", "razao_status", "bucket_funil", "ordem_funil", "tempo_atendimento_horas",
    "tempo_resposta_horas", "dias_no_funil", "venda_concretizada", "target_ml",
    "is_perda", "flag_data_inconsistente",
]


def _limpar_linha(row: dict) -> dict:
    """Converte NaN/NaT em None para a validação Pydantic."""
    return {k: (None if pd.isna(v) else v) for k, v in row.items()}


def validar(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Valida cada linha com Pydantic (RNF-09).

    Retorna (df_valido, df_quarentena). Linhas inválidas NÃO abortam a carga;
    vão para a quarentena com a coluna `_erro`.
    """
    # Datas parseadas uma vez, de forma robusta (dd/mm/yyyy).
    for col in DATE_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], dayfirst=True, errors="coerce")

    validos: list[dict] = []
    invalidos: list[dict] = []
    for raw in df.to_dict(orient="records"):
        try:
            modelo = LeadRaw(**_limpar_linha(raw))
            validos.append(modelo.model_dump())
        except ValidationError as exc:
            invalidos.append({**raw, "_erro": "; ".join(e["msg"] for e in exc.errors())})

    logger.info(f"Validação: {len(validos)} válidas, {len(invalidos)} em quarentena.")
    df_ok = pd.DataFrame(validos) if validos else pd.DataFrame(columns=df.columns)
    df_quar = pd.DataFrame(invalidos)
    return df_ok, df_quar


def transformar(df: pd.DataFrame, mapa_fases: pd.DataFrame, salt: str) -> pd.DataFrame:
    """Aplica regras de negócio e engenharia de atributos sobre linhas válidas."""
    if df.empty:
        return pd.DataFrame(columns=_COLUNAS_SAIDA)

    df = df.copy()

    # Normaliza dimensões textuais (geo em caixa alta, trim).
    for col in ("cidade", "concessionaria", "campanha", "necessidade", "status_relacionamento"):
        if col in df.columns:
            df[col] = df[col].astype("string").str.strip()
    df["cidade"] = df["cidade"].str.upper()
    df["uf"] = df["uf"].astype("string").str.strip().str.upper()

    # RN-01 — target a partir da Fase do Negócio.
    alvo = df["fase_negocio"].apply(rules.calcular_target)
    df["venda_concretizada"] = alvo.apply(lambda t: t[0])
    df["target_ml"] = alvo.apply(lambda t: t[1])

    # RN-06 — bucket/ordem/perda via dim_fase_negocio.
    dim = mapa_fases.rename(columns={"fase_original": "fase_negocio"})[
        ["fase_negocio", "bucket_funil", "ordem_funil", "is_perda"]
    ]
    df = df.merge(dim, on="fase_negocio", how="left")

    # RN-09 / RN-11 — tipo de pessoa e hash do documento.
    df["tipo_pessoa"] = df["documento"].apply(rules.inferir_tipo_pessoa)
    df["documento_hash"] = df["documento"].apply(lambda d: rules.hash_documento(d, salt))

    # RN-12 — ano de criação.
    df["ano"] = pd.to_datetime(df["data_criacao"], errors="coerce").dt.year.astype("Int64")

    # RN-08 — durações e flag de qualidade de datas.
    df["tempo_resposta_horas"] = df.apply(
        lambda r: rules.calcular_tempo_resposta_horas(
            r["data_criacao"], r["data_primeiro_atendimento"]
        ),
        axis=1,
    )
    df["dias_no_funil"] = df.apply(
        lambda r: rules.calcular_dias_no_funil(r["data_criacao"], r["data_modificacao"]),
        axis=1,
    )
    df["flag_data_inconsistente"] = df.apply(
        lambda r: rules.datas_inconsistentes(
            r["data_criacao"], r["data_associacao_vendedor"],
            r["data_primeiro_atendimento"], r["data_modificacao"],
        ),
        axis=1,
    )

    # data_prevista_faturamento é DATE (sem hora).
    df["data_prevista_faturamento"] = pd.to_datetime(
        df["data_prevista_faturamento"], errors="coerce"
    ).dt.date

    df["oportunidade_id"] = df["oportunidade_id"].astype(str)
    df["is_perda"] = df["is_perda"].fillna(False).astype(bool)

    # Garante todas as colunas de saída (preenche faltantes com NA).
    for col in _COLUNAS_SAIDA:
        if col not in df.columns:
            df[col] = np.nan

    df = df[_COLUNAS_SAIDA]

    # RN-03 — uma linha por oportunidade (defesa contra arquivos no grão de item).
    antes = len(df)
    df = df.drop_duplicates(subset="oportunidade_id", keep="first")
    removidas = antes - len(df)
    if removidas:
        logger.warning(f"Removidas {removidas} linhas com oportunidade_id duplicado (mantida a 1ª).")

    return df
