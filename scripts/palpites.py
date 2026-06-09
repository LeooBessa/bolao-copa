"""Abre/fecha os palpites em massa (útil para a apresentação).

  python -m scripts.palpites --fechar          # trava TODOS (ninguém palpita)
  python -m scripts.palpites --abrir           # reabre os jogos da fase de grupos
  python -m scripts.palpites --abrir --futuro  # reabre E joga a data p/ +3h
                                               # (garante destravado num demo,
                                               #  mesmo que o horário já tenha passado)

Jogos FINALIZADOS nunca são alterados. "Fechar" trava qualquer jogo não
finalizado; "abrir" reabre os jogos de grupos (os de mata-mata seguem
fechados por terem times "A definir").
"""

from __future__ import annotations

import argparse

from app.database.session import SessionLocal
from app.services.palpites import abrir_palpites_grupos, fechar_todos_palpites


def main() -> None:
    parser = argparse.ArgumentParser(description="Abrir/fechar palpites em massa")
    grupo = parser.add_mutually_exclusive_group(required=True)
    grupo.add_argument("--fechar", action="store_true", help="Trava todos os palpites.")
    grupo.add_argument("--abrir", action="store_true", help="Reabre os jogos de grupos.")
    parser.add_argument(
        "--futuro",
        action="store_true",
        help="Ao abrir, joga a data dos jogos para +3h (garante destravado em demo).",
    )
    args = parser.parse_args()

    with SessionLocal() as db:
        if args.fechar:
            n = fechar_todos_palpites(db)
            print(f"🔒 {n} jogos fechados. Ninguém pode palpitar.")
        else:
            n = abrir_palpites_grupos(db, futuro=args.futuro)
            extra = " (datas ajustadas para +3h)" if args.futuro else ""
            print(f"🔓 {n} jogos de grupos reabertos{extra}.")


if __name__ == "__main__":
    main()
