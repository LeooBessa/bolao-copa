"""Ranking: agrega os pontos já gravados nos palpites.

Importante: isto NÃO reexecuta a lógica de pontuação — apenas soma os valores
de `palpite.pontos` que foram gravados quando o admin finalizou cada jogo.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models.palpite import Palpite
from app.models.usuario import Usuario


@dataclass
class LinhaRanking:
    posicao: int
    usuario_id: int
    nome: str
    pontos: int
    acertos: int  # nº de palpites com pontos > 0
    total_palpites: int


def montar_ranking(db: Session) -> list[LinhaRanking]:
    """Monta o ranking geral, ordenado por pontos (desc) e nome (asc).

    Consulta portável entre SQLite (dev) e PostgreSQL (produção).
    """
    stmt = (
        select(
            Usuario.id.label("uid"),
            Usuario.nome.label("nome"),
            func.coalesce(func.sum(Palpite.pontos), 0).label("pontos"),
            func.count(Palpite.id).label("total"),
            func.coalesce(
                func.sum(case((Palpite.pontos > 0, 1), else_=0)), 0
            ).label("acertos"),
        )
        .select_from(Usuario)
        .outerjoin(Palpite, Palpite.usuario_id == Usuario.id)
        .where(Usuario.is_admin.is_(False))
        .group_by(Usuario.id, Usuario.nome)
    )

    rows = db.execute(stmt).all()
    # Ordena por pontos desc, depois nome asc (desempate estável).
    rows = sorted(rows, key=lambda r: (-int(r.pontos), r.nome.lower()))

    ranking: list[LinhaRanking] = []
    for i, r in enumerate(rows, start=1):
        ranking.append(
            LinhaRanking(
                posicao=i,
                usuario_id=int(r.uid),
                nome=r.nome,
                pontos=int(r.pontos),
                acertos=int(r.acertos),
                total_palpites=int(r.total),
            )
        )
    return ranking


def posicao_do_usuario(db: Session, usuario_id: int) -> LinhaRanking | None:
    """Retorna a linha de ranking de um usuário específico."""
    for linha in montar_ranking(db):
        if linha.usuario_id == usuario_id:
            return linha
    return None
