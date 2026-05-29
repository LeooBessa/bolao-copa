"""Model de palpite (aposta de um usuário em um jogo)."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.jogo import Jogo
    from app.models.usuario import Usuario


class Palpite(Base):
    __tablename__ = "palpites"
    # Um único palpite por usuário em cada jogo (editar = upsert).
    __table_args__ = (
        UniqueConstraint("usuario_id", "jogo_id", name="uq_palpite_usuario_jogo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    jogo_id: Mapped[int] = mapped_column(
        ForeignKey("jogos.id", ondelete="CASCADE"), nullable=False, index=True
    )

    gols_casa_palpite: Mapped[int] = mapped_column(Integer, nullable=False)
    gols_fora_palpite: Mapped[int] = mapped_column(Integer, nullable=False)
    # Obrigatório no mata-mata quando o palpite é empate ("quem avança?").
    classificado_palpite: Mapped[Optional[str]] = mapped_column(
        String(80), nullable=True
    )

    # Pontuação gravada quando o admin finaliza o jogo (não recalculada em runtime).
    pontos: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    usuario: Mapped["Usuario"] = relationship(back_populates="palpites")
    jogo: Mapped["Jogo"] = relationship(back_populates="palpites")

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<Palpite u={self.usuario_id} j={self.jogo_id} "
            f"{self.gols_casa_palpite}x{self.gols_fora_palpite} pts={self.pontos}>"
        )
