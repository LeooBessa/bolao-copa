"""Schemas de entrada da API REST (corpos JSON)."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field, field_validator


class ApiLogin(BaseModel):
    email: EmailStr
    senha: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def lower(cls, v: str) -> str:
        return v.strip().lower()


class ApiRegister(BaseModel):
    nome: str = Field(min_length=2, max_length=120)
    email: EmailStr
    senha: str = Field(min_length=6, max_length=128)

    @field_validator("nome")
    @classmethod
    def nome_strip(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Nome é obrigatório.")
        return v

    @field_validator("email")
    @classmethod
    def lower(cls, v: str) -> str:
        return v.strip().lower()


class ApiPalpite(BaseModel):
    gols_casa_palpite: int = Field(ge=0, le=99)
    gols_fora_palpite: int = Field(ge=0, le=99)
    classificado_palpite: str | None = Field(default=None, max_length=80)

    @field_validator("classificado_palpite")
    @classmethod
    def normaliza(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        return v or None
