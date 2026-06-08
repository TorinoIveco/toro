"""Validação linha-a-linha do export (RNF-09).

`LeadRaw` valida o mínimo necessário para garantir integridade antes do
transform: presença de chave, datas parseáveis e UF plausível. Regras de
negócio mais ricas ficam em `domain.rules` e na camada de transformação.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator

from toro_insights.domain.constants import UFS_VALIDAS


class LeadRaw(BaseModel):
    """Linha bruta validada do export do Dynamics."""

    model_config = ConfigDict(str_strip_whitespace=True)

    oportunidade_id: UUID
    data_criacao: datetime | None = None
    data_modificacao: datetime | None = None
    data_associacao_vendedor: datetime | None = None
    data_primeiro_atendimento: datetime | None = None
    data_prevista_faturamento: datetime | None = None
    cliente_nome: str | None = None
    documento: str | None = None
    razao_status: str | None = None
    campanha: str | None = None
    status_relacionamento: str | None = None
    concessionaria: str | None = None
    vendedor: str | None = None
    fase_negocio: str | None = None
    tempo_atendimento_horas: int | None = None
    celular: str | None = None
    email: str | None = None
    necessidade: str | None = None
    produto_interesse: str | None = None
    modelo_interesse: str | None = None
    cidade: str | None = None
    uf: str | None = None

    @field_validator("uf")
    @classmethod
    def _uf_valida(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip().upper()
        if v and v not in UFS_VALIDAS:
            raise ValueError(f"UF inválida: {v!r}")
        return v or None

    @field_validator("tempo_atendimento_horas", mode="before")
    @classmethod
    def _tempo_int(cls, v: object) -> int | None:
        if v is None or v == "":
            return None
        try:
            return int(float(v))  # tolera "29335" e 29335.0
        except (TypeError, ValueError) as exc:
            raise ValueError(f"tempo_atendimento_horas não numérico: {v!r}") from exc
