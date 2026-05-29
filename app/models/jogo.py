"""Model de jogo (partida)."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.enums import Fase, StatusJogo

if TYPE_CHECKING:
    from app.models.palpite import Palpite


class Jogo(Base):
    __tablename__ = "jogos"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Fase do torneio e ordem dentro da fase (para exibição estável).
    fase: Mapped[Fase] = mapped_column(
        SAEnum(Fase, name="fase_enum", native_enum=False, length=30),
        nullable=False,
        index=True,
    )
    ordem: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Times. Aceitam placeholders no mata-mata (ex.: "1A", "2B", "Vencedor W37").
    time_casa: Mapped[str] = mapped_column(String(80), nullable=False)
    time_fora: Mapped[str] = mapped_column(String(80), nullable=False)

    # Resultado oficial (preenchido pelo admin ao finalizar).
    gols_casa_real: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    gols_fora_real: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    # Vencedor oficial no mata-mata (nome do time). Simétrico a
    # `classificado_palpite`. Em jogos de grupos fica nulo.
    classificado_real: Mapped[Optional[str]] = mapped_column(
        String(80), nullable=True
    )

    status: Mapped[StatusJogo] = mapped_column(
        SAEnum(StatusJogo, name="status_enum", native_enum=False, length=20),
        default=StatusJogo.ABERTO,
        nullable=False,
        index=True,
    )
    data_jogo: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    palpites: Mapped[list["Palpite"]] = relationship(
        back_populates="jogo", cascade="all, delete-orphan"
    )

    # ------------------------------------------------------------------
    @property
    def is_mata_mata(self) -> bool:
        return self.fase.is_mata_mata

    @property
    def tem_resultado(self) -> bool:
        return self.gols_casa_real is not None and self.gols_fora_real is not None

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<Jogo {self.id} {self.fase.value} "
            f"{self.time_casa} x {self.time_fora} [{self.status.value}]>"
        )
