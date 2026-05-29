"""Histórico do usuário: jogos finalizados, palpite e pontos obtidos."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import require_participante
from app.database.session import get_db
from app.models.enums import StatusJogo
from app.models.jogo import Jogo
from app.models.palpite import Palpite
from app.models.usuario import Usuario
from app.templating import render
from app.utils.time import ensure_aware

router = APIRouter(tags=["historico"])


@router.get("/historico")
def historico(
    request: Request,
    usuario: Usuario = Depends(require_participante),
    db: Session = Depends(get_db),
) -> object:
    jogos = list(
        db.scalars(select(Jogo).where(Jogo.status == StatusJogo.FINALIZADO))
    )
    jogos.sort(key=lambda j: ensure_aware(j.data_jogo), reverse=True)

    palpites = {
        p.jogo_id: p
        for p in db.scalars(
            select(Palpite).where(Palpite.usuario_id == usuario.id)
        )
    }

    itens = [{"jogo": j, "palpite": palpites.get(j.id)} for j in jogos]
    total_pontos = sum(
        (p.pontos for p in palpites.values()), 0
    )

    return render(
        request,
        "historico.html",
        {"itens": itens, "total_pontos": total_pontos},
        usuario=usuario,
    )
