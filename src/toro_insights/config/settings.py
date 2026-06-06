"""Configurações da aplicação (Twelve-Factor: config via ambiente)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Raiz do projeto = .../TORO Insights (3 níveis acima deste arquivo: config/ -> toro_insights/ -> src/ -> raiz)
PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """Configurações carregadas de variáveis de ambiente / arquivo .env."""

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = Field(..., alias="DATABASE_URL")
    db_schema: str = Field("toro", alias="DB_SCHEMA")

    documento_hash_salt: str = Field(..., alias="DOCUMENTO_HASH_SALT")
    nf_match_janela_dias: int = Field(30, alias="NF_MATCH_JANELA_DIAS")

    quarentena_dir: Path = Field(PROJECT_ROOT / "data" / "quarentena", alias="QUARENTENA_DIR")

    log_level: str = Field("INFO", alias="LOG_LEVEL")
    log_file: Path = Field(PROJECT_ROOT / "logs" / "toro_insights.log", alias="LOG_FILE")

    # Acesso ao app Streamlit (persona única: Gerente de Marketing)
    # Sem defaults — obrigatório definir no .env para evitar credenciais triviais em produção.
    app_usuario: str = Field(..., alias="APP_USUARIO")
    app_senha: str = Field(..., alias="APP_SENHA")

    # Assistente IA (Google Gemini)
    gemini_api_key: str = Field("", alias="GEMINI_API_KEY")
    gemini_model: str = Field("gemini-2.5-flash", alias="GEMINI_MODEL")

    @property
    def ddl_path(self) -> Path:
        """Caminho do DDL canônico (fonte única de verdade do schema)."""
        return PROJECT_ROOT / "docs" / "ddl_postgresql_v1.sql"

    @property
    def model_path(self) -> Path:
        """Caminho do modelo de lead scoring (joblib)."""
        return PROJECT_ROOT / "models" / "lead_scoring.joblib"


@lru_cache
def get_settings() -> Settings:
    """Retorna uma instância única (cacheada) das configurações."""
    return Settings()  # type: ignore[call-arg]
