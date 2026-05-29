"""Ambiente do Alembic.

Lê a URL do banco das settings da aplicação e usa o metadata do `Base`
(com todos os models importados) como alvo das migrations.
"""

from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

from app.config import settings
from app.database.base import Base

# Importa os models para registrá-los em Base.metadata.
import app.models  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# A URL vem das settings (lê DATABASE_URL do .env). Usamos diretamente, sem
# passar pelo configparser do Alembic — que interpreta '%' (ex.: senhas
# percent-encoded) como sintaxe de interpolação.
DATABASE_URL = settings.database_url


def run_migrations_offline() -> None:
    """Migrations em modo offline (gera SQL sem conectar)."""
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Migrations em modo online (conecta no banco)."""
    connectable = create_engine(DATABASE_URL, poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
