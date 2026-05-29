"""Listagem de jogos para o usuário, agrupados por fase."""

from __future__ import annotations

from collections import defaultdict

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.session import get_db
from app.models.enums import ORDEM_FASES, Fase
from app.models.jogo import Jogo
from app.models.palpite import Palpite
from app.models.usuario import Usuario
from app.services.palpites import palpite_travado
from app.templating import render
from app.utils.time import ensure_aware

router = APIRouter(tags=["jogos"])


@router.get("/jogos")
def listar_jogos(
    request: Request,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> object:
    jogos = list(db.scalars(select(Jogo)))
    jogos.sort(key=lambda j: (ORDEM_FASES[j.fase], j.ordem, ensure_aware(j.data_jogo)))

    # Mapa de palpites do usuário por jogo.
    palpites = {
        p.jogo_id: p
        for p in db.scalars(
            select(Palpite).where(Palpite.usuario_id == usuario.id)
        )
    }

    grupos: dict[Fase, list[dict]] = defaultdict(list)
    for j in jogos:
        grupos[j.fase].append(
            {
                "jogo": j,
                "palpite": palpites.get(j.id),
                "travado": palpite_travado(j),
            }
        )

    # Lista ordenada de (fase, itens) para iterar no template.
    fases_ordenadas = sorted(grupos.items(), key=lambda kv: ORDEM_FASES[kv[0]])

    return render(
        request,
        "jogos.html",
        {"fases": fases_ordenadas},
        usuario=usuario,
    )
