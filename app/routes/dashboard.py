"""Dashboard do usuário: visão geral de pontuação, posição e jogos."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import require_participante
from app.database.session import get_db
from app.models.enums import ORDEM_FASES, StatusJogo
from app.models.jogo import Jogo
from app.models.usuario import Usuario
from app.services.ranking import ha_ao_vivo, posicao_do_usuario
from app.templating import render
from app.utils.time import ensure_aware, now_utc

router = APIRouter(tags=["dashboard"])


@router.get("/")
def dashboard(
    request: Request,
    usuario: Usuario = Depends(require_participante),
    db: Session = Depends(get_db),
) -> object:
    agora = now_utc()

    jogos = list(db.scalars(select(Jogo)))
    # Ordena por fase canônica e depois data.
    jogos.sort(key=lambda j: (ORDEM_FASES[j.fase], ensure_aware(j.data_jogo)))

    proximos = [
        j
        for j in jogos
        if j.status == StatusJogo.ABERTO and ensure_aware(j.data_jogo) >= agora
    ][:5]

    ultimos_resultados = [
        j for j in jogos if j.status == StatusJogo.FINALIZADO
    ]
    ultimos_resultados.sort(
        key=lambda j: ensure_aware(j.data_jogo), reverse=True
    )
    ultimos_resultados = ultimos_resultados[:5]

    linha = posicao_do_usuario(db, usuario.id)
    total_jogadores = len(
        [u for u in db.scalars(select(Usuario)) if not u.is_admin]
    )

    contexto = {
        # 'pontos' já inclui a parcela provisória dos jogos ao vivo (total).
        "pontos": linha.total if linha else 0,
        "ao_vivo_pts": linha.ao_vivo if linha else 0,
        "posicao": linha.posicao if linha else "-",
        "acertos": linha.acertos if linha else 0,
        "total_palpites": linha.total_palpites if linha else 0,
        "total_jogadores": total_jogadores,
        "proximos": proximos,
        "ultimos_resultados": ultimos_resultados,
        "ao_vivo": ha_ao_vivo(db),
    }
    return render(request, "dashboard.html", contexto, usuario=usuario)
