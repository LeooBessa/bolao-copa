"""Tabela ao vivo: pontuação PROVISÓRIA a partir do placar parcial.

Não grava nada — calcula em tempo real (a cada carregamento da página) usando
as mesmas regras do resultado oficial, aplicadas ao placar ao vivo.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import ORDEM_FASES
from app.models.jogo import Jogo
from app.models.palpite import Palpite
from app.models.usuario import Usuario
from app.services.scoring import pontos_provisorios
from app.utils.time import ensure_aware


@dataclass
class LinhaJogoAoVivo:
    usuario_id: int
    nome: str
    palpite: Palpite | None
    pontos: int  # provisórios com o placar atual


@dataclass
class JogoAoVivo:
    jogo: Jogo
    linhas: list[LinhaJogoAoVivo] = field(default_factory=list)


def jogos_ao_vivo(db: Session) -> list[Jogo]:
    """Jogos marcados como 'ao vivo', em ordem de fase/horário."""
    jogos = list(db.scalars(select(Jogo).where(Jogo.ao_vivo.is_(True))))
    jogos.sort(key=lambda j: (ORDEM_FASES[j.fase], j.ordem, ensure_aware(j.data_jogo)))
    return jogos


def _participantes(db: Session) -> list[Usuario]:
    return list(db.scalars(select(Usuario).where(Usuario.is_admin.is_(False))))


def tabela_de_um_jogo(db: Session, jogo: Jogo) -> JogoAoVivo:
    """Pontos provisórios de cada participante para um jogo ao vivo."""
    palpites = {
        p.usuario_id: p
        for p in db.scalars(select(Palpite).where(Palpite.jogo_id == jogo.id))
    }
    linhas = []
    for u in _participantes(db):
        p = palpites.get(u.id)
        linhas.append(
            LinhaJogoAoVivo(
                usuario_id=u.id,
                nome=u.nome,
                palpite=p,
                pontos=pontos_provisorios(p, jogo) if p else 0,
            )
        )
    # Mais pontos primeiro; depois quem palpitou; depois nome.
    linhas.sort(key=lambda l: (-l.pontos, 0 if l.palpite else 1, l.nome.lower()))
    return JogoAoVivo(jogo=jogo, linhas=linhas)


def montar_tabela_ao_vivo(db: Session) -> list[JogoAoVivo]:
    """Tabela provisória de cada jogo que está ao vivo."""
    return [tabela_de_um_jogo(db, j) for j in jogos_ao_vivo(db)]
