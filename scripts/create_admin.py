"""Cria (ou atualiza) a conta de administrador padrão.

Login fixo: o admin já existe no banco — não depende de cadastro. As
credenciais vêm de variáveis de ambiente:

    ADMIN_EMAIL     email de login do admin (ex.: admin@bolao.com)
    ADMIN_PASSWORD  senha do admin

Uso:
    python -m scripts.create_admin

Se o usuário já existir, a senha é redefinida e ele é promovido a admin
(útil para "resetar" a senha do admin padrão).
"""

from __future__ import annotations

import os
import sys

from sqlalchemy import select

from app.auth.security import hash_senha
from app.config import settings
from app.database.base import Base
from app.database.session import SessionLocal, engine
from app.models.usuario import Usuario


def main() -> None:
    email = (settings.admin_email or "").strip().lower()
    senha = os.environ.get("ADMIN_PASSWORD", "")

    if not email:
        sys.exit("❌ Defina ADMIN_EMAIL no .env.")
    if len(senha) < 6:
        sys.exit("❌ Defina ADMIN_PASSWORD (mín. 6 caracteres) no ambiente/.env.")

    # Garante que as tabelas existam (idempotente).
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        usuario = db.scalar(select(Usuario).where(Usuario.email == email))
        if usuario is None:
            usuario = Usuario(nome="Administrador", email=email)
            db.add(usuario)
            acao = "criado"
        else:
            acao = "atualizado"

        usuario.senha_hash = hash_senha(senha)
        usuario.is_admin = True
        db.commit()

    print(f"✅ Admin {acao}: {email} (is_admin=True).")


if __name__ == "__main__":
    main()
