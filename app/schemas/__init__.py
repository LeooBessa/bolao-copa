"""Schemas Pydantic para validação de entrada (formulários)."""

from app.schemas.auth import CadastroInput, LoginInput
from app.schemas.jogo import JogoInput, ResultadoInput
from app.schemas.palpite import PalpiteInput

__all__ = [
    "CadastroInput",
    "LoginInput",
    "JogoInput",
    "ResultadoInput",
    "PalpiteInput",
]
