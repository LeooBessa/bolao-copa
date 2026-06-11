"""Listagem de jogos para o usuário, agrupados por fase."""

from __future__ import annotations

from collections import defaultdict
from urllib.parse import quote

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.session import get_db
from app.models.enums import ORDEM_FASES, Fase, StatusJogo
from app.models.jogo import Jogo
from app.models.palpite import Palpite
from app.models.usuario import Usuario
from app.services.palpites import jogo_revela_palpites, palpite_travado
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
                "revela": jogo_revela_palpites(j),
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


@router.get("/jogos/{jogo_id}/palpites")
def palpites_dos_adversarios(
    jogo_id: int,
    request: Request,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> object:
    """Mostra os palpites de TODOS os participantes para um jogo.

    Só é liberado quando o jogo já está travado (começou/fechado/finalizado),
    para não permitir que um participante copie o palpite do outro antes do
    jogo começar.
    """
    jogo = db.get(Jogo, jogo_id)
    if jogo is None:
        return RedirectResponse(url="/jogos?erro=Jogo+nao+encontrado", status_code=303)

    if not jogo_revela_palpites(jogo):
        msg = quote("Os palpites dos outros só aparecem quando o jogo começar.")
        return RedirectResponse(url=f"/jogos?erro={msg}", status_code=303)

    # Palpites de todos os participantes (não-admin) para este jogo.
    palpites = {
        p.usuario_id: p
        for p in db.scalars(select(Palpite).where(Palpite.jogo_id == jogo_id))
    }
    participantes = db.scalars(
        select(Usuario).where(Usuario.is_admin.is_(False))
    ).all()

    finalizado = jogo.status == StatusJogo.FINALIZADO
    linhas = [
        {"usuario": u, "palpite": palpites.get(u.id), "eu": u.id == usuario.id}
        for u in participantes
    ]
    # Ordena: quem pontuou mais primeiro (se finalizado), depois quem palpitou,
    # depois por nome.
    linhas.sort(
        key=lambda l: (
            -(l["palpite"].pontos if l["palpite"] else -1),
            0 if l["palpite"] else 1,
            l["usuario"].nome.lower(),
        )
    )

    return render(
        request,
        "jogo_palpites.html",
        {"jogo": jogo, "linhas": linhas, "finalizado": finalizado},
        usuario=usuario,
    )
