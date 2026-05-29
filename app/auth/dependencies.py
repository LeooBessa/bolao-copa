"""Dependencies do FastAPI para proteção de rotas.

O JWT é lido do cookie httpOnly (sessão segura). Como o frontend é
server-rendered, redirecionamos para /login quando não autenticado em vez
de retornar 401 puro.
"""

from __future__ import annotations

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.auth.security import decodificar_token
from app.config import settings
from app.database.session import get_db
from app.models.usuario import Usuario


class RedirectException(Exception):
    """Exceção usada para sinalizar um redirect a partir de uma dependency."""

    def __init__(self, location: str) -> None:
        self.location = location


def _usuario_do_request(request: Request, db: Session) -> Usuario | None:
    """Extrai o usuário a partir do cookie JWT, se válido."""
    token = request.cookies.get(settings.cookie_name)
    if not token:
        return None
    payload = decodificar_token(token)
    if not payload:
        return None
    sub = payload.get("sub")
    if sub is None:
        return None
    try:
        usuario_id = int(sub)
    except (TypeError, ValueError):
        return None
    return db.get(Usuario, usuario_id)


def get_optional_user(
    request: Request, db: Session = Depends(get_db)
) -> Usuario | None:
    """Retorna o usuário logado ou None (não força autenticação)."""
    return _usuario_do_request(request, db)


def get_current_user(
    request: Request, db: Session = Depends(get_db)
) -> Usuario:
    """Exige usuário autenticado; senão redireciona para /login."""
    usuario = _usuario_do_request(request, db)
    if usuario is None:
        raise RedirectException("/login")
    return usuario


def require_admin(
    usuario: Usuario = Depends(get_current_user),
) -> Usuario:
    """Exige usuário autenticado E admin; senão redireciona para o dashboard."""
    if not usuario.is_admin:
        raise RedirectException("/")
    return usuario


def require_participante(
    usuario: Usuario = Depends(get_current_user),
) -> Usuario:
    """Exige usuário comum (não-admin).

    O admin apenas registra resultados — não faz palpites nem tem dashboard
    pessoal. Por isso é redirecionado para o painel admin nessas telas.
    """
    if usuario.is_admin:
        raise RedirectException("/admin")
    return usuario


__all__ = [
    "RedirectException",
    "get_optional_user",
    "get_current_user",
    "require_admin",
    "require_participante",
]
