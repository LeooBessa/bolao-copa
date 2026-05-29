"""Schema de palpite enviado pelo usuário."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator, model_validator


class PalpiteInput(BaseModel):
    """Palpite de um usuário em um jogo.

    No mata-mata, se o palpite for empate, `classificado_palpite` é
    obrigatório ("quem avança?"). A validação cruzada depende de saber se o
    jogo é de mata-mata — passamos `is_mata_mata` no contexto.
    """

    gols_casa_palpite: int = Field(ge=0, le=99)
    gols_fora_palpite: int = Field(ge=0, le=99)
    classificado_palpite: str | None = Field(default=None, max_length=80)
    is_mata_mata: bool = False

    @field_validator("classificado_palpite")
    @classmethod
    def normaliza(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        return v or None

    @model_validator(mode="after")
    def valida_classificado(self) -> "PalpiteInput":
        if self.is_mata_mata:
            empate = self.gols_casa_palpite == self.gols_fora_palpite
            if empate and not self.classificado_palpite:
                raise ValueError(
                    "Palpite de empate no mata-mata exige escolher quem avança."
                )
        else:
            # Em grupos não faz sentido ter classificado.
            self.classificado_palpite = None
        return self
