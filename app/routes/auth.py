"""Rotas públicas de autenticação: cadastro, login e logout."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.cookies import clear_auth_cookie, set_auth_cookie
from app.auth.security import criar_token, hash_senha, verificar_senha
from app.config import settings
from app.database.session import get_db
from app.models.usuario import Usuario
from app.schemas.auth import CadastroInput, LoginInput
from app.templating import render

router = APIRouter(tags=["auth"])


def _erros_legiveis(exc: ValidationError) -> list[str]:
    """Converte erros do Pydantic em mensagens curtas para o usuário."""
    return [e.get("msg", "Dado inválido.") for e in exc.errors()]


# --- Cadastro -----------------------------------------------------------
@router.get("/cadastro")
def cadastro_form(request: Request) -> object:
    return render(request, "auth/cadastro.html", {"erros": []})


@router.post("/cadastro")
def cadastro_submit(
    request: Request,
    nome: str = Form(...),
    email: str = Form(...),
    senha: str = Form(...),
    db: Session = Depends(get_db),
) -> object:
    try:
        dados = CadastroInput(nome=nome, email=email, senha=senha)
    except ValidationError as exc:
        return render(
            request,
            "auth/cadastro.html",
            {"erros": _erros_legiveis(exc), "nome": nome, "email": email},
            status_code=400,
        )

    existe = db.scalar(select(Usuario).where(Usuario.email == dados.email))
    if existe:
        return render(
            request,
            "auth/cadastro.html",
            {
                "erros": ["Este email já está cadastrado."],
                "nome": dados.nome,
                "email": dados.email,
            },
            status_code=400,
        )

    # Bootstrap do admin via .env: o email configurado vira admin.
    is_admin = bool(
        settings.admin_email
        and dados.email == settings.admin_email.strip().lower()
    )

    usuario = Usuario(
        nome=dados.nome,
        email=dados.email,
        senha_hash=hash_senha(dados.senha),
        is_admin=is_admin,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)

    # Já autentica após o cadastro.
    token = criar_token(usuario.id, is_admin=usuario.is_admin)
    resp = RedirectResponse(url="/", status_code=303)
    set_auth_cookie(resp, token)
    return resp


# --- Login --------------------------------------------------------------
@router.get("/login")
def login_form(request: Request) -> object:
    return render(request, "auth/login.html", {"erros": []})


@router.post("/login")
def login_submit(
    request: Request,
    email: str = Form(...),
    senha: str = Form(...),
    db: Session = Depends(get_db),
) -> object:
    try:
        dados = LoginInput(email=email, senha=senha)
    except ValidationError:
        return render(
            request,
            "auth/login.html",
            {"erros": ["Email ou senha inválidos."], "email": email},
            status_code=400,
        )

    usuario = db.scalar(select(Usuario).where(Usuario.email == dados.email))
    if usuario is None or not verificar_senha(dados.senha, usuario.senha_hash):
        return render(
            request,
            "auth/login.html",
            {"erros": ["Email ou senha incorretos."], "email": dados.email},
            status_code=401,
        )

    token = criar_token(usuario.id, is_admin=usuario.is_admin)
    resp = RedirectResponse(url="/", status_code=303)
    set_auth_cookie(resp, token)
    return resp


# --- Logout -------------------------------------------------------------
@router.get("/logout")
def logout() -> RedirectResponse:
    resp = RedirectResponse(url="/login", status_code=303)
    clear_auth_cookie(resp)
    return resp
