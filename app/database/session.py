"""Engine e sessão do SQLAlchemy.

Em ambiente serverless (Vercel) não devemos manter um pool de conexões na
aplicação — o pooler do Supabase (pgBouncer) já cuida disso. Por isso usamos
`NullPool`: cada request abre e fecha sua própria conexão.
"""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from app.config import settings

# SQLite (usado só em dev/local rápido) precisa de connect_args específico e
# não aceita NullPool da mesma forma; tratamos os dois casos.
_is_sqlite = settings.database_url.startswith("sqlite")

if _is_sqlite:
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
        future=True,
    )
else:
    engine = create_engine(
        settings.database_url,
        poolclass=NullPool,  # ideal para serverless + pooler do Supabase
        pool_pre_ping=True,
        future=True,
    )

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    class_=Session,
)


def get_db() -> Generator[Session, None, None]:
    """Dependency do FastAPI que fornece uma sessão por request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
