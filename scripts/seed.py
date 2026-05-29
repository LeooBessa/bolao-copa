"""Seed do bolão — Copa do Mundo 2026 (tabela oficial).

Popula a tabela real da Copa 2026 (formato 48 times / 12 grupos):
  * 72 jogos da fase de grupos — seleções, grupos, datas e horários reais
    (horário de Brasília, UTC-3).
  * 32 jogos do mata-mata (jogos 73–104) com datas/horários reais e times
    "A definir" (FECHADOS) — o admin define os confrontos conforme a
    competição avança, pela tela /admin/mata-mata.

Uso:
    python -m scripts.seed            # cria os jogos (idempotente)
    python -m scripts.seed --reset    # apaga TODOS os jogos e recria
"""

from __future__ import annotations

import argparse
from datetime import datetime

from sqlalchemy import delete, func, select

from app.database.base import Base
from app.database.session import SessionLocal, engine
from app.models.enums import Fase, StatusJogo
from app.models.jogo import Jogo
from app.utils.time import BRASILIA


def dt(mes: int, dia: int, hora: int, minuto: int = 0) -> datetime:
    """Cria um datetime de 2026 no fuso de Brasília."""
    return datetime(2026, mes, dia, hora, minuto, tzinfo=BRASILIA)


# --- Fase de grupos: (data_jogo, time_casa, time_fora, grupo) ----------
# Ordem cronológica conforme a tabela oficial.
GRUPOS_JOGOS: list[tuple[datetime, str, str, str]] = [
    # Quinta 11/06
    (dt(6, 11, 16), "México", "África do Sul", "A"),
    (dt(6, 11, 23), "Coreia do Sul", "República Tcheca", "A"),
    # Sexta 12/06
    (dt(6, 12, 16), "Canadá", "Bósnia", "B"),
    (dt(6, 12, 22), "Estados Unidos", "Paraguai", "D"),
    # Sábado 13/06
    (dt(6, 13, 1), "Austrália", "Turquia", "D"),
    (dt(6, 13, 16), "Qatar", "Suíça", "B"),
    (dt(6, 13, 19), "Brasil", "Marrocos", "C"),
    (dt(6, 13, 22), "Haiti", "Escócia", "C"),
    # Domingo 14/06
    (dt(6, 14, 14), "Alemanha", "Curaçao", "E"),
    (dt(6, 14, 17), "Holanda", "Japão", "F"),
    (dt(6, 14, 20), "Costa do Marfim", "Equador", "E"),
    (dt(6, 14, 23), "Suécia", "Tunísia", "F"),
    # Segunda 15/06
    (dt(6, 15, 13), "Espanha", "Cabo Verde", "H"),
    (dt(6, 15, 16), "Bélgica", "Egito", "G"),
    (dt(6, 15, 19), "Arábia Saudita", "Uruguai", "H"),
    (dt(6, 15, 22), "Irã", "Nova Zelândia", "G"),
    # Terça 16/06
    (dt(6, 16, 16), "França", "Senegal", "I"),
    (dt(6, 16, 19), "Iraque", "Noruega", "I"),
    (dt(6, 16, 22), "Argentina", "Argélia", "J"),
    # Quarta 17/06
    (dt(6, 17, 1), "Áustria", "Jordânia", "J"),
    (dt(6, 17, 14), "Portugal", "RD Congo", "K"),
    (dt(6, 17, 17), "Inglaterra", "Croácia", "L"),
    (dt(6, 17, 20), "Gana", "Panamá", "L"),
    (dt(6, 17, 23), "Uzbequistão", "Colômbia", "K"),
    # Quinta 18/06
    (dt(6, 18, 13), "República Tcheca", "África do Sul", "A"),
    (dt(6, 18, 16), "Suíça", "Bósnia", "B"),
    (dt(6, 18, 19), "Canadá", "Qatar", "B"),
    (dt(6, 18, 22), "México", "Coreia do Sul", "A"),
    # Sexta 19/06
    (dt(6, 19, 1), "Turquia", "Paraguai", "D"),
    (dt(6, 19, 16), "Estados Unidos", "Austrália", "D"),
    (dt(6, 19, 19), "Escócia", "Marrocos", "C"),
    (dt(6, 19, 22), "Brasil", "Haiti", "C"),
    # Sábado 20/06
    (dt(6, 20, 14), "Holanda", "Suécia", "F"),
    (dt(6, 20, 17), "Alemanha", "Costa do Marfim", "E"),
    (dt(6, 20, 21), "Equador", "Curaçao", "E"),
    # Domingo 21/06
    (dt(6, 21, 1), "Tunísia", "Japão", "F"),
    (dt(6, 21, 13), "Espanha", "Arábia Saudita", "H"),
    (dt(6, 21, 16), "Bélgica", "Irã", "G"),
    (dt(6, 21, 19), "Uruguai", "Cabo Verde", "H"),
    (dt(6, 21, 22), "Nova Zelândia", "Egito", "G"),
    # Segunda 22/06
    (dt(6, 22, 14), "Argentina", "Áustria", "J"),
    (dt(6, 22, 18), "França", "Iraque", "I"),
    (dt(6, 22, 21), "Noruega", "Senegal", "I"),
    # Terça 23/06
    (dt(6, 23, 0), "Jordânia", "Argélia", "J"),
    (dt(6, 23, 14), "Portugal", "Uzbequistão", "K"),
    (dt(6, 23, 17), "Inglaterra", "Gana", "L"),
    (dt(6, 23, 20), "Panamá", "Croácia", "L"),
    (dt(6, 23, 23), "Colômbia", "RD Congo", "K"),
    # Quarta 24/06
    (dt(6, 24, 16), "Suíça", "Canadá", "B"),
    (dt(6, 24, 16), "Bósnia", "Qatar", "B"),
    (dt(6, 24, 19), "Escócia", "Brasil", "C"),
    (dt(6, 24, 19), "Marrocos", "Haiti", "C"),
    (dt(6, 24, 22), "República Tcheca", "México", "A"),
    (dt(6, 24, 22), "África do Sul", "Coreia do Sul", "A"),
    # Quinta 25/06
    (dt(6, 25, 17), "Equador", "Alemanha", "E"),
    (dt(6, 25, 17), "Curaçao", "Costa do Marfim", "E"),
    (dt(6, 25, 20), "Tunísia", "Holanda", "F"),
    (dt(6, 25, 20), "Japão", "Suécia", "F"),
    (dt(6, 25, 23), "Turquia", "Estados Unidos", "D"),
    (dt(6, 25, 23), "Paraguai", "Austrália", "D"),
    # Sexta 26/06
    (dt(6, 26, 16), "Noruega", "França", "I"),
    (dt(6, 26, 16), "Senegal", "Iraque", "I"),
    (dt(6, 26, 21), "Uruguai", "Espanha", "H"),
    (dt(6, 26, 21), "Cabo Verde", "Arábia Saudita", "H"),
    (dt(6, 26, 0), "Egito", "Irã", "G"),
    (dt(6, 26, 0), "Nova Zelândia", "Bélgica", "G"),
    # Sábado 27/06
    (dt(6, 27, 18), "Panamá", "Inglaterra", "L"),
    (dt(6, 27, 18), "Croácia", "Gana", "L"),
    (dt(6, 27, 20, 30), "Colômbia", "Portugal", "K"),
    (dt(6, 27, 20, 30), "RD Congo", "Uzbequistão", "K"),
    (dt(6, 27, 23), "Jordânia", "Argentina", "J"),
    (dt(6, 27, 23), "Argélia", "Áustria", "J"),
]


# --- Mata-mata: (fase, numero_do_jogo, data_jogo) ----------------------
# Times "A definir" (placeholders). O número do jogo vai em `ordem`.
MATA_MATA_JOGOS: list[tuple[Fase, int, datetime]] = [
    # 32 avos (jogos 73–88)
    (Fase.TRINTA_E_DOIS_AVOS, 73, dt(6, 28, 16)),
    (Fase.TRINTA_E_DOIS_AVOS, 76, dt(6, 29, 14)),
    (Fase.TRINTA_E_DOIS_AVOS, 74, dt(6, 29, 17, 30)),
    (Fase.TRINTA_E_DOIS_AVOS, 75, dt(6, 29, 22)),
    (Fase.TRINTA_E_DOIS_AVOS, 78, dt(6, 30, 14)),
    (Fase.TRINTA_E_DOIS_AVOS, 77, dt(6, 30, 18)),
    (Fase.TRINTA_E_DOIS_AVOS, 79, dt(6, 30, 22)),
    (Fase.TRINTA_E_DOIS_AVOS, 80, dt(7, 1, 13)),
    (Fase.TRINTA_E_DOIS_AVOS, 82, dt(7, 1, 17)),
    (Fase.TRINTA_E_DOIS_AVOS, 81, dt(7, 1, 21)),
    (Fase.TRINTA_E_DOIS_AVOS, 84, dt(7, 2, 16)),
    (Fase.TRINTA_E_DOIS_AVOS, 83, dt(7, 2, 20)),
    (Fase.TRINTA_E_DOIS_AVOS, 85, dt(7, 2, 0)),
    (Fase.TRINTA_E_DOIS_AVOS, 88, dt(7, 3, 15)),
    (Fase.TRINTA_E_DOIS_AVOS, 86, dt(7, 3, 19)),
    (Fase.TRINTA_E_DOIS_AVOS, 87, dt(7, 3, 22, 30)),
    # Oitavas (jogos 89–96)
    (Fase.OITAVAS, 90, dt(7, 4, 14)),
    (Fase.OITAVAS, 89, dt(7, 4, 18)),
    (Fase.OITAVAS, 91, dt(7, 5, 17)),
    (Fase.OITAVAS, 92, dt(7, 5, 21)),
    (Fase.OITAVAS, 93, dt(7, 6, 16)),
    (Fase.OITAVAS, 94, dt(7, 6, 21)),
    (Fase.OITAVAS, 95, dt(7, 7, 13)),
    (Fase.OITAVAS, 96, dt(7, 7, 17)),
    # Quartas (jogos 97–100)
    (Fase.QUARTAS, 97, dt(7, 9, 17)),
    (Fase.QUARTAS, 98, dt(7, 10, 16)),
    (Fase.QUARTAS, 99, dt(7, 11, 18)),
    (Fase.QUARTAS, 100, dt(7, 11, 22)),
    # Semifinais (jogos 101–102)
    (Fase.SEMIFINAL, 101, dt(7, 14, 16)),
    (Fase.SEMIFINAL, 102, dt(7, 15, 16)),
    # Disputa de 3º lugar (jogo 103)
    (Fase.TERCEIRO, 103, dt(7, 18, 18)),
    # Final (jogo 104)
    (Fase.FINAL, 104, dt(7, 19, 16)),
]


def _build_jogos() -> list[Jogo]:
    jogos: list[Jogo] = []

    # Grupos: ordem = posição cronológica (1..72), status ABERTO.
    for i, (data, casa, fora, _grupo) in enumerate(GRUPOS_JOGOS, start=1):
        jogos.append(
            Jogo(
                fase=Fase.GRUPOS,
                ordem=i,
                time_casa=casa,
                time_fora=fora,
                data_jogo=data,
                status=StatusJogo.ABERTO,
            )
        )

    # Mata-mata: ordem = número oficial do jogo (73..104), times "A definir",
    # status FECHADO até o admin definir os confrontos.
    for fase, numero, data in MATA_MATA_JOGOS:
        jogos.append(
            Jogo(
                fase=fase,
                ordem=numero,
                time_casa="A definir",
                time_fora="A definir",
                data_jogo=data,
                status=StatusJogo.FECHADO,
            )
        )

    return jogos


def seed(reset: bool = False) -> None:
    # Garante que as tabelas existam (útil em dev/SQLite sem rodar Alembic).
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        if reset:
            db.execute(delete(Jogo))
            db.commit()
            print("⚠️  Todos os jogos foram apagados.")

        existentes = db.scalar(select(func.count(Jogo.id))) or 0
        if existentes and not reset:
            print(
                f"Já existem {existentes} jogos no banco. "
                "Use --reset para recriar. Nada a fazer."
            )
            return

        jogos = _build_jogos()
        db.add_all(jogos)
        db.commit()

        grupos = sum(1 for j in jogos if j.fase == Fase.GRUPOS)
        mata = len(jogos) - grupos
        print(
            f"✅ Seed concluído: {len(jogos)} jogos criados "
            f"({grupos} de grupos + {mata} de mata-mata)."
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed da Copa 2026")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Apaga todos os jogos antes de recriar.",
    )
    args = parser.parse_args()
    seed(reset=args.reset)
