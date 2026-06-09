"""Página pública 'Ao Vivo': tabela provisória em tempo (quase) real.

A página se auto-atualiza periodicamente (polling via meta refresh), então
todos os clientes convergem para o mesmo placar logo após o admin registrar um
gol — uma sincronização cliente-servidor de estado compartilhado.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.session import get_db
from app.models.usuario import Usuario
from app.services.ao_vivo import montar_tabela_ao_vivo, ranking_ao_vivo
from app.templating import render, templates

router = APIRouter(tags=["ao-vivo"])


@router.get("/ao-vivo")
def ao_vivo(
    request: Request,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> object:
    tabelas = montar_tabela_ao_vivo(db)
    ranking = ranking_ao_vivo(db)
    return render(
        request,
        "ao_vivo.html",
        {"tabelas": tabelas, "ranking": ranking, "meu_id": usuario.id},
        usuario=usuario,
    )


@router.get("/ao-vivo/fragmento")
def ao_vivo_fragmento(
    request: Request,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> object:
    """Retorna SÓ o conteúdo dinâmico (HTML), para o polling suave via fetch."""
    tabelas = montar_tabela_ao_vivo(db)
    ranking = ranking_ao_vivo(db)
    return templates.TemplateResponse(
        request=request,
        name="partials/ao_vivo_conteudo.html",
        context={"tabelas": tabelas, "ranking": ranking, "meu_id": usuario.id},
    )
