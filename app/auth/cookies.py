"""Helpers para gravar/limpar o cookie de sessão (JWT)."""

from __future__ import annotations

from fastapi import Response

from app.config import settings


def set_auth_cookie(response: Response, token: str) -> None:
    """Grava o JWT em cookie httpOnly, SameSite=Lax e Secure em produção."""
    response.set_cookie(
        key=settings.cookie_name,
        value=token,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
        max_age=settings.jwt_expire_minutes * 60,
        path="/",
    )


def clear_auth_cookie(response: Response) -> None:
    """Remove o cookie de sessão (logout)."""
    response.delete_cookie(key=settings.cookie_name, path="/")
