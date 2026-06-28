"""Regras de palpite: travamento e persistência (upsert)."""

from __future__ import annotations

from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import Fase, StatusJogo
from app.models.jogo import Jogo
from app.models.palpite import Palpite
from app.schemas.palpite import PalpiteInput
from app.utils.time import BRASILIA, ensure_aware, now_utc


def palpite_travado(jogo: Jogo) -> bool:
    """Diz se um jogo já não aceita mais palpites.

    Trava quando o status é fechado/finalizado OU quando o horário do jogo
    já chegou (data_jogo <= agora).
    """
    if jogo.status in (StatusJogo.FECHADO, StatusJogo.FINALIZADO):
        return True
    return now_utc() >= ensure_aware(jogo.data_jogo)


def abertura_palpite(jogo: Jogo):
    """Momento em que o jogo abre para palpite: 00h (Brasília) do dia da partida.

    Para jogos à 00h (madrugada), abre no dia anterior, senão não haveria
    janela de palpite.
    """
    kickoff = ensure_aware(jogo.data_jogo).astimezone(BRASILIA)
    abertura = kickoff.replace(hour=0, minute=0, second=0, microsecond=0)
    if abertura >= kickoff:
        abertura = abertura - timedelta(days=1)
    return abertura


def palpite_disponivel(jogo: Jogo) -> bool:
    """True se o jogo aceita palpite AGORA.

    Precisa estar aberto (não travado) e já ter chegado a abertura do dia.
    """
    if palpite_travado(jogo):
        return False
    return now_utc() >= abertura_palpite(jogo)


def jogo_revela_palpites(jogo: Jogo) -> bool:
    """Diz se os palpites de todos já podem ser vistos.

    Só libera quando o jogo realmente começa (chegou o horário) ou quando já
    foi finalizado. Fechar a aposta antes do horário NÃO revela os palpites.
    """
    if jogo.status == StatusJogo.FINALIZADO:
        return True
    return now_utc() >= ensure_aware(jogo.data_jogo)


def fechar_todos_palpites(db: Session) -> int:
    """Trava TODOS os jogos não finalizados (ninguém pode palpitar). Retorna nº alterado."""
    n = 0
    for j in db.scalars(select(Jogo)):
        if j.status not in (StatusJogo.FINALIZADO, StatusJogo.FECHADO):
            j.status = StatusJogo.FECHADO
            n += 1
    db.commit()
    return n


def abrir_palpites_grupos(db: Session, *, futuro: bool = False) -> int:
    """Reabre os jogos da fase de grupos não finalizados. Retorna nº alterado.

    Com `futuro=True`, empurra a data de jogos cujo horário já passou para +3h,
    garantindo que destravem (a trava também considera o horário do jogo).
    """
    n = 0
    agora = now_utc()
    for j in db.scalars(select(Jogo).where(Jogo.fase == Fase.GRUPOS)):
        if j.status == StatusJogo.FINALIZADO:
            continue
        j.status = StatusJogo.ABERTO
        if futuro and ensure_aware(j.data_jogo) <= agora:
            j.data_jogo = agora + timedelta(hours=3)
        n += 1
    db.commit()
    return n


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

    Lança ValueError se o jogo não estiver disponível (ainda não abriu ou já
    travou). Não recalcula pontos aqui: a pontuação só é gravada quando o admin
    finaliza o resultado.
    """
    if not palpite_disponivel(jogo):
        if palpite_travado(jogo):
            raise ValueError("Os palpites deste jogo estão travados.")
        raise ValueError("Este jogo ainda não abriu para palpite.")

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
