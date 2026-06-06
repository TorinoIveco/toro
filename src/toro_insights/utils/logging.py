"""Configuração centralizada de logs com Loguru (RNF-04)."""

from __future__ import annotations

import sys

from loguru import logger

from toro_insights.config.settings import get_settings

_configured = False


def setup_logging() -> "logger.__class__":
    """Configura o logger global (console + arquivo). Idempotente."""
    global _configured
    if _configured:
        return logger

    settings = get_settings()
    logger.remove()
    logger.add(
        sys.stderr,
        level=settings.log_level,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>"
        ),
        # LGPD/Segurança: desativa dump de variáveis locais e backtrace estendido
        # para evitar que valores de parâmetros SQL (contendo PII) apareçam nos logs.
        diagnose=False,
        backtrace=False,
    )
    settings.log_file.parent.mkdir(parents=True, exist_ok=True)
    logger.add(
        settings.log_file,
        level=settings.log_level,
        rotation="10 MB",
        retention="30 days",
        encoding="utf-8",
        # LGPD/Segurança: sem dump de variáveis locais nem backtrace estendido no arquivo.
        diagnose=False,
        backtrace=False,
    )
    _configured = True
    return logger
