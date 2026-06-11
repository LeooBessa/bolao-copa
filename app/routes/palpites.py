"""Rotas de palpite: tela "Meus palpites" e submissão de um palpite."""

from __future__ import annotations

from collections import defaultdict

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import require_participante
from app.database.session import get_db
from app.models.enums import ORDEM_FASES, Fase
from app.models.jogo import Jogo
from app.models.palpite import Palpite
from app.models.usuario import Usuario
from app.schemas.palpite import PalpiteInput
from app.services.palpites import (
    jogo_revela_palpites,
    palpite_travado,
    salvar_palpite,
)
from app.templating import render
from app.utils.time import ensure_aware

router = APIRouter(tags=["palpites"])


@router.get("/palpites")
def meus_palpites(
    request: Request,
    usuario: Usuario = Depends(require_participante),
    db: Session = Depends(get_db),
    msg: str | None = None,
    erro: str | None = None,
) -> object:
    """Tela de criação/edição de palpites, agrupada por fase."""
    jogos = list(db.scalars(select(Jogo)))
    jogos.sort(key=lambda j: (ORDEM_FASES[j.fase], j.ordem, ensure_aware(j.data_jogo)))

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
    fases_ordenadas = sorted(grupos.items(), key=lambda kv: ORDEM_FASES[kv[0]])

    return render(
        request,
        "palpites.html",
        {"fases": fases_ordenadas, "msg": msg, "erro": erro},
        usuario=usuario,
    )


@router.post("/palpites/{jogo_id}")
def salvar(
    jogo_id: int,
    request: Request,
    gols_casa_palpite: int = Form(...),
    gols_fora_palpite: int = Form(...),
    classificado_palpite: str | None = Form(default=None),
    usuario: Usuario = Depends(require_participante),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    jogo = db.get(Jogo, jogo_id)
    if jogo is None:
        return RedirectResponse(
            url="/palpites?erro=Jogo+n%C3%A3o+encontrado", status_code=303
        )

    if palpite_travado(jogo):
        return RedirectResponse(
            url="/palpites?erro=Palpites+travados+para+este+jogo",
            status_code=303,
        )

    try:
        dados = PalpiteInput(
            gols_casa_palpite=gols_casa_palpite,
            gols_fora_palpite=gols_fora_palpite,
            classificado_palpite=classificado_palpite,
            is_mata_mata=jogo.is_mata_mata,
        )
    except ValidationError:
        return RedirectResponse(
            url="/palpites?erro=Palpite+inv%C3%A1lido+(verifique+quem+avan%C3%A7a)",
            status_code=303,
        )

    # Garante que o classificado escolhido seja um dos dois times do jogo.
    if (
        jogo.is_mata_mata
        and dados.classificado_palpite
        and dados.classificado_palpite not in (jogo.time_casa, jogo.time_fora)
    ):
        return RedirectResponse(
            url="/palpites?erro=Classificado+inv%C3%A1lido", status_code=303
        )

    try:
        salvar_palpite(db, usuario_id=usuario.id, jogo=jogo, dados=dados)
    except ValueError as exc:
        from urllib.parse import quote

        return RedirectResponse(
            url=f"/palpites?erro={quote(str(exc))}", status_code=303
        )

    return RedirectResponse(
        url="/palpites?msg=Palpite+salvo+com+sucesso", status_code=303
    )
