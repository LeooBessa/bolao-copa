"""API REST (JSON) — microsserviço para clientes/integrações externas.

Mesma lógica de negócio da web (services reutilizados), mas com:
  * autenticação via Bearer token (header Authorization), não cookie;
  * respostas JSON e erros HTTP (401/403/404/422), sem redirect.

Prefixo: /api
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.api_deps import get_api_user, require_api_participante
from app.auth.security import criar_token, hash_senha, verificar_senha
from app.config import settings
from app.database.session import get_db
from app.models.enums import ORDEM_FASES
from app.models.jogo import Jogo
from app.models.palpite import Palpite
from app.models.usuario import Usuario
from app.schemas.api import ApiLogin, ApiPalpite, ApiRegister
from app.schemas.palpite import PalpiteInput
from app.services.palpites import palpite_travado, salvar_palpite
from app.services.ranking import montar_ranking, posicao_do_usuario
from app.utils.time import ensure_aware, fmt_data

router = APIRouter(prefix="/api", tags=["api"])


# --- Serialização -------------------------------------------------------
def _serialize_palpite(p: Palpite | None) -> dict[str, Any] | None:
    if p is None:
        return None
    return {
        "gols_casa_palpite": p.gols_casa_palpite,
        "gols_fora_palpite": p.gols_fora_palpite,
        "classificado_palpite": p.classificado_palpite,
        "pontos": p.pontos,
    }


def _serialize_jogo(jogo: Jogo, palpite: Palpite | None = None) -> dict[str, Any]:
    return {
        "id": jogo.id,
        "fase": jogo.fase.value,
        "fase_label": jogo.fase.label,
        "ordem": jogo.ordem,
        "time_casa": jogo.time_casa,
        "time_fora": jogo.time_fora,
        "status": jogo.status.value,
        "status_label": jogo.status.label,
        "is_mata_mata": jogo.is_mata_mata,
        "data_jogo": ensure_aware(jogo.data_jogo).isoformat(),
        "data_fmt": fmt_data(jogo.data_jogo),
        "gols_casa_real": jogo.gols_casa_real,
        "gols_fora_real": jogo.gols_fora_real,
        "classificado_real": jogo.classificado_real,
        "tem_resultado": jogo.tem_resultado,
        "travado": palpite_travado(jogo),
        "palpite": _serialize_palpite(palpite),
    }


def _serialize_usuario(u: Usuario, db: Session) -> dict[str, Any]:
    linha = posicao_do_usuario(db, u.id)
    return {
        "id": u.id,
        "nome": u.nome,
        "email": u.email,
        "is_admin": u.is_admin,
        "pontos": linha.pontos if linha else 0,
        "posicao": linha.posicao if linha else None,
        "acertos": linha.acertos if linha else 0,
        "total_palpites": linha.total_palpites if linha else 0,
    }


# --- Autenticação -------------------------------------------------------
@router.post("/auth/register", status_code=status.HTTP_201_CREATED)
def api_register(dados: ApiRegister, db: Session = Depends(get_db)) -> dict[str, Any]:
    if db.scalar(select(Usuario).where(Usuario.email == dados.email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Este email já está cadastrado.")

    is_admin = bool(
        settings.admin_email and dados.email == settings.admin_email.strip().lower()
    )
    usuario = Usuario(
        nome=dados.nome,
        email=dados.email,
        senha_hash=hash_senha(dados.senha),
        is_admin=is_admin,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)

    token = criar_token(usuario.id, is_admin=usuario.is_admin)
    return {"token": token, "usuario": _serialize_usuario(usuario, db)}


@router.post("/auth/login")
def api_login(dados: ApiLogin, db: Session = Depends(get_db)) -> dict[str, Any]:
    usuario = db.scalar(select(Usuario).where(Usuario.email == dados.email))
    if usuario is None or not verificar_senha(dados.senha, usuario.senha_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Email ou senha incorretos.")

    token = criar_token(usuario.id, is_admin=usuario.is_admin)
    return {"token": token, "usuario": _serialize_usuario(usuario, db)}


@router.get("/me")
def api_me(
    usuario: Usuario = Depends(get_api_user), db: Session = Depends(get_db)
) -> dict[str, Any]:
    return _serialize_usuario(usuario, db)


# --- Jogos & palpites ---------------------------------------------------
@router.get("/jogos")
def api_jogos(
    usuario: Usuario = Depends(get_api_user), db: Session = Depends(get_db)
) -> list[dict[str, Any]]:
    jogos = list(db.scalars(select(Jogo)))
    jogos.sort(
        key=lambda j: (ORDEM_FASES[j.fase], j.ordem, ensure_aware(j.data_jogo))
    )
    palpites = {
        p.jogo_id: p
        for p in db.scalars(select(Palpite).where(Palpite.usuario_id == usuario.id))
    }
    return [_serialize_jogo(j, palpites.get(j.id)) for j in jogos]


@router.post("/palpites/{jogo_id}")
def api_salvar_palpite(
    jogo_id: int,
    dados: ApiPalpite,
    usuario: Usuario = Depends(require_api_participante),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    jogo = db.get(Jogo, jogo_id)
    if jogo is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Jogo não encontrado.")
    if palpite_travado(jogo):
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Palpites travados para este jogo."
        )

    # Validação cruzada (empate no mata-mata exige classificado).
    try:
        validado = PalpiteInput(
            gols_casa_palpite=dados.gols_casa_palpite,
            gols_fora_palpite=dados.gols_fora_palpite,
            classificado_palpite=dados.classificado_palpite,
            is_mata_mata=jogo.is_mata_mata,
        )
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc))

    if (
        jogo.is_mata_mata
        and validado.classificado_palpite
        and validado.classificado_palpite not in (jogo.time_casa, jogo.time_fora)
    ):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "O classificado deve ser um dos dois times do jogo.",
        )

    try:
        palpite = salvar_palpite(
            db, usuario_id=usuario.id, jogo=jogo, dados=validado
        )
    except ValueError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc))

    return _serialize_jogo(jogo, palpite)


# --- Ranking & histórico ------------------------------------------------
@router.get("/ranking")
def api_ranking(
    usuario: Usuario = Depends(get_api_user), db: Session = Depends(get_db)
) -> list[dict[str, Any]]:
    return [
        {
            "posicao": l.posicao,
            "usuario_id": l.usuario_id,
            "nome": l.nome,
            "pontos": l.pontos,
            "acertos": l.acertos,
            "total_palpites": l.total_palpites,
            "eu": l.usuario_id == usuario.id,
        }
        for l in montar_ranking(db)
    ]


@router.get("/historico")
def api_historico(
    usuario: Usuario = Depends(get_api_user), db: Session = Depends(get_db)
) -> list[dict[str, Any]]:
    from app.models.enums import StatusJogo

    jogos = list(
        db.scalars(select(Jogo).where(Jogo.status == StatusJogo.FINALIZADO))
    )
    jogos.sort(key=lambda j: ensure_aware(j.data_jogo), reverse=True)
    palpites = {
        p.jogo_id: p
        for p in db.scalars(select(Palpite).where(Palpite.usuario_id == usuario.id))
    }
    return [_serialize_jogo(j, palpites.get(j.id)) for j in jogos]
