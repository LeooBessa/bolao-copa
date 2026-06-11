"""Ranking: pontos consolidados mais os pontos provisórios dos jogos ao vivo.

Os pontos oficiais ficam gravados em `palpite.pontos` (jogos finalizados). Os
pontos provisórios são calculados na hora, a partir do placar parcial dos jogos
marcados como ao vivo. O ranking é ordenado pelo total (oficial + provisório),
então a posição muda durante a partida em andamento.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.jogo import Jogo
from app.models.palpite import Palpite
from app.models.usuario import Usuario
from app.services.scoring import pontos_provisorios


@dataclass
class LinhaRanking:
    posicao: int
    usuario_id: int
    nome: str
    pontos: int          # oficial (jogos finalizados)
    ao_vivo: int         # provisório (jogos ao vivo)
    total: int           # pontos + ao_vivo
    acertos: int         # nº de palpites com pontos > 0 (oficial)
    total_palpites: int


def ha_ao_vivo(db: Session) -> bool:
    """True se existe pelo menos um jogo marcado como ao vivo."""
    return bool(db.scalar(select(func.count(Jogo.id)).where(Jogo.ao_vivo.is_(True))))


def montar_ranking(db: Session) -> list[LinhaRanking]:
    """Monta o ranking somando o oficial com o provisório dos jogos ao vivo."""
    live = {j.id: j for j in db.scalars(select(Jogo).where(Jogo.ao_vivo.is_(True)))}

    palpites_por_usuario: dict[int, list[Palpite]] = defaultdict(list)
    for p in db.scalars(select(Palpite)):
        palpites_por_usuario[p.usuario_id].append(p)

    linhas: list[LinhaRanking] = []
    for u in db.scalars(select(Usuario).where(Usuario.is_admin.is_(False))):
        ps = palpites_por_usuario.get(u.id, [])
        # 'pontos' só está preenchido em jogos finalizados (ao vivo tem pontos=0).
        oficial = sum(p.pontos for p in ps)
        ao_vivo = sum(
            pontos_provisorios(p, live[p.jogo_id]) for p in ps if p.jogo_id in live
        )
        acertos = sum(1 for p in ps if p.pontos > 0)
        linhas.append(
            LinhaRanking(
                posicao=0,
                usuario_id=u.id,
                nome=u.nome,
                pontos=oficial,
                ao_vivo=ao_vivo,
                total=oficial + ao_vivo,
                acertos=acertos,
                total_palpites=len(ps),
            )
        )

    # Ordena pelo total (inclui ao vivo), depois por nome.
    linhas.sort(key=lambda l: (-l.total, l.nome.lower()))
    for i, l in enumerate(linhas, start=1):
        l.posicao = i
    return linhas


def posicao_do_usuario(db: Session, usuario_id: int) -> LinhaRanking | None:
    """Retorna a linha de ranking de um usuário específico."""
    for linha in montar_ranking(db):
        if linha.usuario_id == usuario_id:
            return linha
    return None
