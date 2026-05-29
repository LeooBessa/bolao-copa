"""Configuração do motor de templates Jinja2 (compartilhado entre rotas)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.models.usuario import Usuario
from app.utils.time import BRASILIA, ensure_aware, fmt_data

_BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = _BASE_DIR / "templates"
STATIC_DIR = _BASE_DIR / "static"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

def _dtlocal(dt) -> str:
    """Formata datetime (em Brasília) para o value de <input datetime-local>."""
    if dt is None:
        return ""
    return ensure_aware(dt).astimezone(BRASILIA).strftime("%Y-%m-%dT%H:%M")


# Filtros/globais úteis nos templates.
templates.env.filters["data"] = fmt_data
templates.env.filters["dtlocal"] = _dtlocal
templates.env.autoescape = True  # anti-XSS (padrão do Jinja2, reforçado)


def render(
    request: Request,
    nome_template: str,
    contexto: dict[str, Any] | None = None,
    *,
    usuario: Usuario | None = None,
    status_code: int = 200,
) -> HTMLResponse:
    """Renderiza um template injetando contexto comum (usuário, request)."""
    ctx: dict[str, Any] = {
        "request": request,
        "usuario": usuario,
    }
    if contexto:
        ctx.update(contexto)
    return templates.TemplateResponse(
        request=request,
        name=nome_template,
        context=ctx,
        status_code=status_code,
    )
