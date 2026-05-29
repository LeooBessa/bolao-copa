"""Configuração central da aplicação.

Lê variáveis de ambiente (via `.env` em desenvolvimento) usando
pydantic-settings. Centralizar aqui evita espalhar `os.getenv` pelo código.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurações tipadas da aplicação."""

    # --- Banco de dados -------------------------------------------------
    # Connection string do Supabase. Em produção/serverless use o POOLER
    # (transaction mode, porta 6543), não a conexão direta (5432).
    database_url: str = "sqlite:///./bolao_dev.db"

    # --- Segurança / JWT -----------------------------------------------
    secret_key: str = "troque-isto-por-uma-chave-secreta-bem-grande"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # 7 dias

    # Nome do cookie que guarda o JWT (sessão segura, httpOnly).
    cookie_name: str = "bolao_session"

    # --- Bootstrap do admin --------------------------------------------
    # Ao cadastrar com este email, o usuário recebe is_admin=True.
    admin_email: str = ""

    # --- Ambiente -------------------------------------------------------
    # "production" => cookies Secure (somente HTTPS). "development" => não.
    environment: str = "development"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    """Retorna uma instância única (cacheada) das configurações."""
    return Settings()


settings = get_settings()
