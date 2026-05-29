"""Helpers de data/hora — sempre timezone-aware (UTC)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

# Fuso de Brasília (UTC-3, sem horário de verão desde 2019). Os jogos são
# cadastrados e exibidos neste fuso, embora o Postgres armazene em UTC.
BRASILIA = timezone(timedelta(hours=-3))


def now_utc() -> datetime:
    """Horário atual com timezone UTC (aware)."""
    return datetime.now(timezone.utc)


def ensure_aware(dt: datetime) -> datetime:
    """Garante que um datetime seja aware (assume UTC se vier naive).

    O PostgreSQL devolve timestamptz já com tz; SQLite pode devolver naive.
    Comparações entre aware e naive lançam TypeError — esta função evita isso.
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def fmt_data(dt: datetime | None) -> str:
    """Formata data para exibição em horário de Brasília (dd/mm/aaaa HH:MM)."""
    if dt is None:
        return "-"
    return ensure_aware(dt).astimezone(BRASILIA).strftime("%d/%m/%Y %H:%M")
