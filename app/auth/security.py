"""Funções de segurança: hashing de senha (bcrypt) e tokens JWT."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

import bcrypt
from jose import JWTError, jwt

from app.config import settings
from app.utils.time import now_utc

# bcrypt opera sobre no máximo 72 bytes; truncamos para evitar erro/silenciamento
# inconsistente entre versões.
_BCRYPT_MAX_BYTES = 72


def _to_bytes(senha: str) -> bytes:
    return senha.encode("utf-8")[:_BCRYPT_MAX_BYTES]


# --- Senhas -------------------------------------------------------------
def hash_senha(senha: str) -> str:
    """Gera o hash bcrypt de uma senha em texto puro."""
    return bcrypt.hashpw(_to_bytes(senha), bcrypt.gensalt()).decode("utf-8")


def verificar_senha(senha: str, senha_hash: str) -> bool:
    """Confere uma senha contra o hash armazenado."""
    try:
        return bcrypt.checkpw(_to_bytes(senha), senha_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


# --- JWT ----------------------------------------------------------------
def criar_token(usuario_id: int, *, is_admin: bool) -> str:
    """Cria um JWT assinado contendo o id do usuário e flag de admin."""
    expira = now_utc() + timedelta(minutes=settings.jwt_expire_minutes)
    payload: dict[str, Any] = {
        "sub": str(usuario_id),
        "adm": is_admin,
        "exp": expira,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decodificar_token(token: str) -> dict[str, Any] | None:
    """Decodifica e valida um JWT. Retorna o payload ou None se inválido."""
    try:
        return jwt.decode(
            token, settings.secret_key, algorithms=[settings.jwt_algorithm]
        )
    except JWTError:
        return None
