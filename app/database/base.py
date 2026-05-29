"""Base declarativa do SQLAlchemy.

Todos os models herdam de `Base`. Mantida em módulo próprio para evitar
import circular entre `session.py` e os models.
"""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Classe base para todos os models ORM."""

    pass
