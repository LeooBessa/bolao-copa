"""Dependencies de autenticação para a API REST (clientes mobile).

Diferente da web (que usa cookie + redirect), a API espera o JWT no header
`Authorization: Bearer <token>` e responde com 401 JSON quando ausente/ inválido.
"""

from __future__ import annotations

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.security import decodificar_token
from app.database.session import get_db
from app.models.usuario import Usuario


def _nao_autorizado(detail: str = "Não autenticado.") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_api_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> Usuario:
    """Resolve o usuário a partir do header Bearer; 401 se inválido."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise _nao_autorizado("Header Authorization Bearer ausente.")

    token = authorization.split(" ", 1)[1].strip()
    payload = decodificar_token(token)
    if not payload or "sub" not in payload:
        raise _nao_autorizado("Token inválido ou expirado.")

    try:
        usuario_id = int(payload["sub"])
    except (TypeError, ValueError):
        raise _nao_autorizado("Token malformado.")

    usuario = db.get(Usuario, usuario_id)
    if usuario is None:
        raise _nao_autorizado("Usuário não encontrado.")
    return usuario


def require_api_participante(
    usuario: Usuario = Depends(get_api_user),
) -> Usuario:
    """Exige usuário comum (admin não faz palpites)."""
    if usuario.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administradores não registram palpites.",
        )
    return usuario
