"""Validação dos itens de NF (RNF-09) antes da carga em nf_faturamento."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator


class NfItemRaw(BaseModel):
    """Linha (item de NF) validada do relatório de faturamento do ERP."""

    model_config = ConfigDict(str_strip_whitespace=True)

    oportunidade_id: UUID
    numero_nf: str | None = None
    data_emissao: datetime | None = None
    produto: str | None = None
    gama: str | None = None
    modelo: str | None = None
    quantidade: float | None = None
    valor_unitario: float | None = None
    valor_total: float | None = None

    @field_validator("numero_nf", mode="before")
    @classmethod
    def _nf_para_texto(cls, v: object) -> str | None:
        """Converte número de NF (vem como float 115523.0) para texto '115523'."""
        if v is None or v == "":
            return None
        if isinstance(v, float) and v.is_integer():
            return str(int(v))
        return str(v).strip()

    @field_validator("quantidade", "valor_unitario", "valor_total", mode="before")
    @classmethod
    def _numerico(cls, v: object) -> float | None:
        if v is None or v == "":
            return None
        try:
            return float(v)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"valor não numérico: {v!r}") from exc
