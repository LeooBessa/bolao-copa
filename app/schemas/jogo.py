"""Schemas de jogo (admin): criação/edição e registro de resultado."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator

from app.models.enums import Fase, StatusJogo
from app.utils.time import BRASILIA


class JogoInput(BaseModel):
    """Cadastro/edição de um jogo pelo admin."""

    fase: Fase
    ordem: int = Field(default=0, ge=0)
    time_casa: str = Field(min_length=1, max_length=80)
    time_fora: str = Field(min_length=1, max_length=80)
    data_jogo: datetime
    status: StatusJogo = StatusJogo.ABERTO

    @field_validator("time_casa", "time_fora")
    @classmethod
    def strip_time(cls, v: str) -> str:
        return v.strip()

    @field_validator("data_jogo")
    @classmethod
    def localiza_brasilia(cls, v: datetime) -> datetime:
        # O <input datetime-local> envia horário sem fuso (Brasília). Anexamos
        # o fuso para que o instante armazenado (em UTC) fique correto.
        if v.tzinfo is None:
            return v.replace(tzinfo=BRASILIA)
        return v


class ResultadoInput(BaseModel):
    """Registro do resultado oficial (admin).

    No mata-mata, `classificado_real` é obrigatório (faz parte do resultado);
    em jogos de grupos ele é ignorado.
    """

    gols_casa_real: int = Field(ge=0, le=99)
    gols_fora_real: int = Field(ge=0, le=99)
    classificado_real: str | None = Field(default=None, max_length=80)
    is_mata_mata: bool = False

    @field_validator("classificado_real")
    @classmethod
    def normaliza_classificado(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        return v or None

    @model_validator(mode="after")
    def exige_classificado_no_mata_mata(self) -> "ResultadoInput":
        if self.is_mata_mata and not self.classificado_real:
            raise ValueError(
                "No mata-mata é obrigatório informar o time classificado."
            )
        return self
