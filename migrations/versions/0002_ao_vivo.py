"""tabela ao vivo: placar parcial em jogos

Revision ID: 0002_ao_vivo
Revises: 0001_initial
Create Date: 2026-06-09 18:00:00

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_ao_vivo"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "jogos",
        sa.Column(
            "ao_vivo", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
    )
    op.add_column(
        "jogos", sa.Column("gols_casa_ao_vivo", sa.Integer(), nullable=True)
    )
    op.add_column(
        "jogos", sa.Column("gols_fora_ao_vivo", sa.Integer(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("jogos", "gols_fora_ao_vivo")
    op.drop_column("jogos", "gols_casa_ao_vivo")
    op.drop_column("jogos", "ao_vivo")
