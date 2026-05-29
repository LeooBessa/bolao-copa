"""schema inicial: usuarios, jogos, palpites

Revision ID: 0001_initial
Revises:
Create Date: 2026-01-01 00:00:00

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "usuarios",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nome", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("senha_hash", sa.String(length=255), nullable=False),
        sa.Column(
            "is_admin", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_usuarios_email", "usuarios", ["email"], unique=True)

    op.create_table(
        "jogos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("fase", sa.String(length=30), nullable=False),
        sa.Column("ordem", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("time_casa", sa.String(length=80), nullable=False),
        sa.Column("time_fora", sa.String(length=80), nullable=False),
        sa.Column("gols_casa_real", sa.Integer(), nullable=True),
        sa.Column("gols_fora_real", sa.Integer(), nullable=True),
        sa.Column("classificado_real", sa.String(length=80), nullable=True),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="aberto",
        ),
        sa.Column("data_jogo", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_jogos_fase", "jogos", ["fase"])
    op.create_index("ix_jogos_status", "jogos", ["status"])

    op.create_table(
        "palpites",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("jogo_id", sa.Integer(), nullable=False),
        sa.Column("gols_casa_palpite", sa.Integer(), nullable=False),
        sa.Column("gols_fora_palpite", sa.Integer(), nullable=False),
        sa.Column("classificado_palpite", sa.String(length=80), nullable=True),
        sa.Column("pontos", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["usuario_id"], ["usuarios.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["jogo_id"], ["jogos.id"], ondelete="CASCADE"),
        sa.UniqueConstraint(
            "usuario_id", "jogo_id", name="uq_palpite_usuario_jogo"
        ),
    )
    op.create_index("ix_palpites_usuario_id", "palpites", ["usuario_id"])
    op.create_index("ix_palpites_jogo_id", "palpites", ["jogo_id"])


def downgrade() -> None:
    op.drop_table("palpites")
    op.drop_index("ix_jogos_status", table_name="jogos")
    op.drop_index("ix_jogos_fase", table_name="jogos")
    op.drop_table("jogos")
    op.drop_index("ix_usuarios_email", table_name="usuarios")
    op.drop_table("usuarios")
