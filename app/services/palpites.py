"""Regras de palpite: travamento e persistência (upsert)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import StatusJogo
from app.models.jogo import Jogo
from app.models.palpite import Palpite
from app.schemas.palpite import PalpiteInput
from app.utils.time import ensure_aware, now_utc


def palpite_travado(jogo: Jogo) -> bool:
    """Diz se um jogo já não aceita mais palpites.

    Trava quando o status é fechado/finalizado OU quando o horário do jogo
    já chegou (data_jogo <= agora).
    """
    if jogo.status in (StatusJogo.FECHADO, StatusJogo.FINALIZADO):
        return True
    return now_utc() >= ensure_aware(jogo.data_jogo)


def buscar_palpite(
    db: Session, *, usuario_id: int, jogo_id: int
) -> Palpite | None:
    """Retorna o palpite existente do usuário para o jogo, se houver."""
    stmt = select(Palpite).where(
        Palpite.usuario_id == usuario_id, Palpite.jogo_id == jogo_id
    )
    return db.scalar(stmt)


def salvar_palpite(
    db: Session, *, usuario_id: int, jogo: Jogo, dados: PalpiteInput
) -> Palpite:
    """Cria ou atualiza (upsert) o palpite do usuário para um jogo.

    Lança ValueError se o jogo já estiver travado. Não recalcula pontos aqui:
    a pontuação só é gravada quando o admin finaliza o resultado.
    """
    if palpite_travado(jogo):
        raise ValueError("Os palpites deste jogo estão travados.")

    palpite = buscar_palpite(db, usuario_id=usuario_id, jogo_id=jogo.id)
    if palpite is None:
        palpite = Palpite(usuario_id=usuario_id, jogo_id=jogo.id)
        db.add(palpite)

    palpite.gols_casa_palpite = dados.gols_casa_palpite
    palpite.gols_fora_palpite = dados.gols_fora_palpite
    palpite.classificado_palpite = (
        dados.classificado_palpite if jogo.is_mata_mata else None
    )
    db.commit()
    db.refresh(palpite)
    return palpite
