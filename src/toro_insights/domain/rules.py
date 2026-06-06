"""Regras de negócio puras (sem I/O) — testáveis isoladamente.

Implementa as regras RN-01, RN-07, RN-08, RN-09, RN-11 e RN-12 do SRS.
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime

from toro_insights.domain.constants import TARGET_FASE


def normalizar_fase(fase: str | None) -> str:
    """Normaliza a Fase do Negócio para comparação (RN-01): trim, espaços, upper."""
    if not fase:
        return ""
    return re.sub(r"\s+", " ", str(fase).strip()).upper()


def calcular_target(fase: str | None) -> tuple[bool, int]:
    """RN-01 — retorna (venda_concretizada, target_ml) a partir da Fase do Negócio."""
    venda = normalizar_fase(fase) == TARGET_FASE
    return venda, int(venda)


def somente_digitos(valor: str | None) -> str:
    """Extrai apenas dígitos de um documento (ignora máscara/asteriscos)."""
    if not valor:
        return ""
    return re.sub(r"\D", "", str(valor))


def inferir_tipo_pessoa(documento: str | None) -> str | None:
    """RN-09 — PF (11 dígitos) / PJ (14 dígitos). None se indeterminado.

    Observação: o documento chega mascarado (ex.: '079.***.***-55'); a contagem
    considera apenas os dígitos visíveis, então pode ser indeterminada.
    """
    n = len(somente_digitos(documento))
    if n == 11:
        return "PF"
    if n == 14:
        return "PJ"
    return None


def hash_documento(documento: str | None, salt: str) -> str | None:
    """RN-11 — pseudonimiza o documento via SHA-256 com salt. None se vazio."""
    base = somente_digitos(documento) or (str(documento).strip() if documento else "")
    if not base:
        return None
    return hashlib.sha256(f"{salt}:{base}".encode()).hexdigest()


def _delta_horas(inicio: datetime | None, fim: datetime | None) -> float | None:
    """Diferença em horas entre dois instantes; None se faltar algum."""
    if inicio is None or fim is None:
        return None
    return (fim - inicio).total_seconds() / 3600.0


def calcular_tempo_resposta_horas(
    data_criacao: datetime | None, data_primeiro_atendimento: datetime | None
) -> float | None:
    """RN-08 — horas entre criação e 1º atendimento; None se inconsistente/ausente."""
    delta = _delta_horas(data_criacao, data_primeiro_atendimento)
    if delta is None or delta < 0:
        return None
    return round(delta, 2)


def calcular_dias_no_funil(
    data_criacao: datetime | None, data_modificacao: datetime | None
) -> float | None:
    """Dias entre criação e última modificação; None se ausente/negativo."""
    delta = _delta_horas(data_criacao, data_modificacao)
    if delta is None or delta < 0:
        return None
    return round(delta / 24.0, 2)


def datas_inconsistentes(
    data_criacao: datetime | None,
    data_associacao_vendedor: datetime | None,
    data_primeiro_atendimento: datetime | None,
    data_modificacao: datetime | None,
) -> bool:
    """RN-08 (DQ) — True se alguma data posterior for anterior à criação."""
    if data_criacao is None:
        return False
    for d in (data_associacao_vendedor, data_primeiro_atendimento, data_modificacao):
        if d is not None and d < data_criacao:
            return True
    return False
