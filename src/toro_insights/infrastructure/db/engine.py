"""Fábrica do SQLAlchemy Engine (conexão única e reutilizável)."""

from __future__ import annotations

from functools import lru_cache

from sqlalchemy import Engine, create_engine

from toro_insights.config.settings import get_settings


@lru_cache
def get_engine() -> Engine:
    """Cria (uma vez) o Engine do SQLAlchemy a partir de DATABASE_URL."""
    settings = get_settings()
    return create_engine(
        settings.database_url,
        pool_pre_ping=True,
        future=True,
        # LGPD/Segurança: oculta valores de parâmetros SQL nas mensagens de exceção,
        # evitando que PII (cliente_nome, documento, etc.) apareça em logs de erro.
        hide_parameters=True,
        # Devolve conexões ao pool com ROLLBACK (evita 'idle in transaction'
        # segurando locks de leitura e bloqueando o TRUNCATE da carga).
        pool_reset_on_return="rollback",
        # Recicla conexões ociosas (pooler do Supabase pode encerrá-las).
        pool_recycle=1800,
    )
