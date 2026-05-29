"""Schemas de autenticação (cadastro e login)."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field, field_validator


class CadastroInput(BaseModel):
    """Dados do formulário de cadastro."""

    nome: str = Field(min_length=2, max_length=120)
    email: EmailStr
    senha: str = Field(min_length=6, max_length=128)

    @field_validator("nome")
    @classmethod
    def nome_sem_espacos_extra(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Nome é obrigatório.")
        return v

    @field_validator("email")
    @classmethod
    def email_lower(cls, v: str) -> str:
        return v.strip().lower()


class LoginInput(BaseModel):
    """Dados do formulário de login."""

    email: EmailStr
    senha: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def email_lower(cls, v: str) -> str:
        return v.strip().lower()
