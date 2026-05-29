"""Tela de ranking geral."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.session import get_db
from app.models.usuario import Usuario
from app.services.ranking import montar_ranking
from app.templating import render

router = APIRouter(tags=["ranking"])


@router.get("/ranking")
def ranking(
    request: Request,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> object:
    linhas = montar_ranking(db)
    return render(
        request,
        "ranking.html",
        {"linhas": linhas, "meu_id": usuario.id},
        usuario=usuario,
    )
