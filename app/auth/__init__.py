"""Autenticação: hashing de senha, JWT e dependencies de proteção de rotas."""

from app.auth.dependencies import (
    get_current_user,
    get_optional_user,
    require_admin,
)
from app.auth.security import (
    criar_token,
    decodificar_token,
    hash_senha,
    verificar_senha,
)

__all__ = [
    "hash_senha",
    "verificar_senha",
    "criar_token",
    "decodificar_token",
    "get_current_user",
    "get_optional_user",
    "require_admin",
]
