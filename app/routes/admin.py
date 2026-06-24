"""Rotas administrativas (prefixo /admin).

Protegidas por `require_admin`. Permitem cadastrar/editar jogos, controlar
status, registrar resultados (com pontuação automática) e gerenciar o
mata-mata (definir os times reais que substituem os placeholders).
"""

from __future__ import annotations

from urllib.parse import quote

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth.dependencies import require_admin
from app.database.session import get_db
from app.models.enums import ORDEM_FASES, Fase, StatusJogo
from app.models.jogo import Jogo
from app.models.palpite import Palpite
from app.models.usuario import Usuario
from app.schemas.jogo import JogoInput, ResultadoInput
from app.services.palpites import abrir_palpites_grupos, fechar_todos_palpites
from app.services.scoring import aplicar_resultado
from app.templating import render
from app.utils.time import ensure_aware

router = APIRouter(prefix="/admin", tags=["admin"])


def _redir(path: str, *, msg: str | None = None, erro: str | None = None):
    """Helper de redirect com mensagem flash via querystring."""
    qs = []
    if msg:
        qs.append(f"msg={quote(msg)}")
    if erro:
        qs.append(f"erro={quote(erro)}")
    sep = "?" if qs else ""
    return RedirectResponse(url=f"{path}{sep}{'&'.join(qs)}", status_code=303)


def _jogos_ordenados(db: Session) -> list[Jogo]:
    jogos = list(db.scalars(select(Jogo)))
    jogos.sort(
        key=lambda j: (ORDEM_FASES[j.fase], j.ordem, ensure_aware(j.data_jogo))
    )
    return jogos


# --- Dashboard admin ----------------------------------------------------
@router.get("")
def dashboard_admin(
    request: Request,
    admin: Usuario = Depends(require_admin),
    db: Session = Depends(get_db),
) -> object:
    total_jogos = db.scalar(select(func.count(Jogo.id))) or 0
    finalizados = (
        db.scalar(
            select(func.count(Jogo.id)).where(
                Jogo.status == StatusJogo.FINALIZADO
            )
        )
        or 0
    )
    abertos = (
        db.scalar(
            select(func.count(Jogo.id)).where(Jogo.status == StatusJogo.ABERTO)
        )
        or 0
    )
    fechados = (
        db.scalar(
            select(func.count(Jogo.id)).where(Jogo.status == StatusJogo.FECHADO)
        )
        or 0
    )
    total_usuarios = (
        db.scalar(
            select(func.count(Usuario.id)).where(Usuario.is_admin.is_(False))
        )
        or 0
    )
    total_palpites = db.scalar(select(func.count(Palpite.id))) or 0

    return render(
        request,
        "admin/dashboard.html",
        {
            "total_jogos": total_jogos,
            "finalizados": finalizados,
            "abertos": abertos,
            "fechados": fechados,
            "total_usuarios": total_usuarios,
            "total_palpites": total_palpites,
        },
        usuario=admin,
    )


# --- Abrir/fechar palpites em massa ------------------------------------
@router.post("/palpites/fechar-todos")
def fechar_todos(
    admin: Usuario = Depends(require_admin),
    db: Session = Depends(get_db),
):
    n = fechar_todos_palpites(db)
    return _redir(
        "/admin", msg=f"🔒 {n} jogos fechados. Ninguém pode mais palpitar."
    )


@router.post("/palpites/abrir-todos")
def abrir_todos(
    admin: Usuario = Depends(require_admin),
    db: Session = Depends(get_db),
):
    n = abrir_palpites_grupos(db)
    return _redir(
        "/admin", msg=f"🔓 {n} jogos da fase de grupos reabertos para palpites."
    )


# --- Tabela ao vivo (placar parcial) -----------------------------------
@router.get("/ao-vivo")
def admin_ao_vivo(
    request: Request,
    admin: Usuario = Depends(require_admin),
    db: Session = Depends(get_db),
    msg: str | None = None,
    erro: str | None = None,
) -> object:
    # Jogos não finalizados (candidatos a ficar ao vivo).
    jogos = [j for j in _jogos_ordenados(db) if j.status != StatusJogo.FINALIZADO]
    return render(
        request,
        "admin/ao_vivo.html",
        {"jogos": jogos, "msg": msg, "erro": erro},
        usuario=admin,
    )


@router.post("/ao-vivo/{jogo_id}/iniciar")
def ao_vivo_iniciar(
    jogo_id: int,
    admin: Usuario = Depends(require_admin),
    db: Session = Depends(get_db),
):
    jogo = db.get(Jogo, jogo_id)
    if jogo is None or jogo.status == StatusJogo.FINALIZADO:
        return _redir("/admin/ao-vivo", erro="Jogo inválido.")
    jogo.ao_vivo = True
    # Sempre começa em 0x0 (zera qualquer placar de uma transmissão anterior).
    jogo.gols_casa_ao_vivo = 0
    jogo.gols_fora_ao_vivo = 0
    db.commit()
    return _redir("/admin/ao-vivo", msg=f"🔴 {jogo.time_casa} x {jogo.time_fora} está AO VIVO.")


@router.post("/ao-vivo/{jogo_id}/gol")
def ao_vivo_gol(
    jogo_id: int,
    time: str = Form(...),
    delta: int = Form(1),
    admin: Usuario = Depends(require_admin),
    db: Session = Depends(get_db),
):
    jogo = db.get(Jogo, jogo_id)
    if jogo is None or not jogo.ao_vivo:
        return _redir("/admin/ao-vivo", erro="Jogo não está ao vivo.")
    if time == "casa":
        jogo.gols_casa_ao_vivo = max(0, (jogo.gols_casa_ao_vivo or 0) + delta)
    elif time == "fora":
        jogo.gols_fora_ao_vivo = max(0, (jogo.gols_fora_ao_vivo or 0) + delta)
    else:
        return _redir("/admin/ao-vivo", erro="Time inválido.")
    db.commit()
    return _redir("/admin/ao-vivo")


@router.post("/ao-vivo/{jogo_id}/encerrar")
def ao_vivo_encerrar(
    jogo_id: int,
    admin: Usuario = Depends(require_admin),
    db: Session = Depends(get_db),
):
    jogo = db.get(Jogo, jogo_id)
    if jogo is None:
        return _redir("/admin/ao-vivo", erro="Jogo não encontrado.")
    jogo.ao_vivo = False
    db.commit()
    return _redir("/admin/ao-vivo", msg="Transmissão ao vivo encerrada.")


# --- Gerenciar jogos (CRUD) --------------------------------------------
@router.get("/jogos")
def gerenciar_jogos(
    request: Request,
    admin: Usuario = Depends(require_admin),
    db: Session = Depends(get_db),
    msg: str | None = None,
    erro: str | None = None,
) -> object:
    return render(
        request,
        "admin/jogos.html",
        {
            "jogos": _jogos_ordenados(db),
            "fases": list(Fase),
            "status_opcoes": list(StatusJogo),
            "msg": msg,
            "erro": erro,
        },
        usuario=admin,
    )


@router.post("/jogos")
def criar_jogo(
    fase: str = Form(...),
    ordem: int = Form(0),
    time_casa: str = Form(...),
    time_fora: str = Form(...),
    data_jogo: str = Form(...),
    status: str = Form(StatusJogo.ABERTO.value),
    admin: Usuario = Depends(require_admin),
    db: Session = Depends(get_db),
):
    try:
        dados = JogoInput(
            fase=Fase(fase),
            ordem=ordem,
            time_casa=time_casa,
            time_fora=time_fora,
            data_jogo=data_jogo,  # type: ignore[arg-type]  # Pydantic faz o parse
            status=StatusJogo(status),
        )
    except (ValidationError, ValueError) as exc:
        return _redir("/admin/jogos", erro=f"Dados inválidos: {exc}")

    jogo = Jogo(
        fase=dados.fase,
        ordem=dados.ordem,
        time_casa=dados.time_casa,
        time_fora=dados.time_fora,
        data_jogo=dados.data_jogo,
        status=dados.status,
    )
    db.add(jogo)
    db.commit()
    return _redir("/admin/jogos", msg="Jogo criado com sucesso.")


@router.post("/jogos/{jogo_id}/editar")
def editar_jogo(
    jogo_id: int,
    fase: str = Form(...),
    ordem: int = Form(0),
    time_casa: str = Form(...),
    time_fora: str = Form(...),
    data_jogo: str = Form(...),
    admin: Usuario = Depends(require_admin),
    db: Session = Depends(get_db),
):
    jogo = db.get(Jogo, jogo_id)
    if jogo is None:
        return _redir("/admin/jogos", erro="Jogo não encontrado.")
    try:
        dados = JogoInput(
            fase=Fase(fase),
            ordem=ordem,
            time_casa=time_casa,
            time_fora=time_fora,
            data_jogo=data_jogo,  # type: ignore[arg-type]
        )
    except (ValidationError, ValueError) as exc:
        return _redir("/admin/jogos", erro=f"Dados inválidos: {exc}")

    jogo.fase = dados.fase
    jogo.ordem = dados.ordem
    jogo.time_casa = dados.time_casa
    jogo.time_fora = dados.time_fora
    jogo.data_jogo = dados.data_jogo
    db.commit()
    return _redir("/admin/jogos", msg="Jogo atualizado.")


@router.post("/jogos/{jogo_id}/status")
def mudar_status(
    jogo_id: int,
    status: str = Form(...),
    admin: Usuario = Depends(require_admin),
    db: Session = Depends(get_db),
):
    jogo = db.get(Jogo, jogo_id)
    if jogo is None:
        return _redir("/admin/jogos", erro="Jogo não encontrado.")
    try:
        jogo.status = StatusJogo(status)
    except ValueError:
        return _redir("/admin/jogos", erro="Status inválido.")
    db.commit()
    return _redir("/admin/jogos", msg=f"Status alterado para {jogo.status.label}.")


@router.post("/jogos/{jogo_id}/excluir")
def excluir_jogo(
    jogo_id: int,
    admin: Usuario = Depends(require_admin),
    db: Session = Depends(get_db),
):
    jogo = db.get(Jogo, jogo_id)
    if jogo is None:
        return _redir("/admin/jogos", erro="Jogo não encontrado.")
    db.delete(jogo)
    db.commit()
    return _redir("/admin/jogos", msg="Jogo excluído.")


# --- Atualizar resultados ----------------------------------------------
@router.get("/resultados")
def tela_resultados(
    request: Request,
    admin: Usuario = Depends(require_admin),
    db: Session = Depends(get_db),
    msg: str | None = None,
    erro: str | None = None,
) -> object:
    jogos = _jogos_ordenados(db)
    # Jogos já finalizados saem da lista principal (vão para um bloco recolhido),
    # deixando no topo só os que ainda precisam de resultado.
    pendentes = [j for j in jogos if j.status != StatusJogo.FINALIZADO]
    finalizados = [j for j in jogos if j.status == StatusJogo.FINALIZADO]
    return render(
        request,
        "admin/resultados.html",
        {
            "pendentes": pendentes,
            "finalizados": finalizados,
            "msg": msg,
            "erro": erro,
        },
        usuario=admin,
    )


@router.post("/resultados/{jogo_id}")
def registrar_resultado(
    jogo_id: int,
    gols_casa_real: int = Form(...),
    gols_fora_real: int = Form(...),
    classificado_real: str | None = Form(default=None),
    admin: Usuario = Depends(require_admin),
    db: Session = Depends(get_db),
):
    jogo = db.get(Jogo, jogo_id)
    if jogo is None:
        return _redir("/admin/resultados", erro="Jogo não encontrado.")

    try:
        dados = ResultadoInput(
            gols_casa_real=gols_casa_real,
            gols_fora_real=gols_fora_real,
            classificado_real=classificado_real,
            is_mata_mata=jogo.is_mata_mata,
        )
    except ValidationError as exc:
        msg = exc.errors()[0].get("msg", "Dados inválidos.")
        return _redir("/admin/resultados", erro=msg)

    # No mata-mata, o classificado precisa ser um dos dois times.
    if (
        jogo.is_mata_mata
        and dados.classificado_real
        and dados.classificado_real not in (jogo.time_casa, jogo.time_fora)
    ):
        return _redir(
            "/admin/resultados",
            erro="O classificado deve ser um dos dois times do jogo.",
        )

    n = aplicar_resultado(
        db,
        jogo,
        gols_casa=dados.gols_casa_real,
        gols_fora=dados.gols_fora_real,
        classificado_real=dados.classificado_real,
    )
    return _redir(
        "/admin/resultados",
        msg=f"Resultado registrado. {n} palpite(s) pontuado(s).",
    )


# --- Mata-mata: definir times reais ------------------------------------
@router.get("/mata-mata")
def tela_mata_mata(
    request: Request,
    admin: Usuario = Depends(require_admin),
    db: Session = Depends(get_db),
    msg: str | None = None,
    erro: str | None = None,
) -> object:
    jogos = [j for j in _jogos_ordenados(db) if j.is_mata_mata]
    return render(
        request,
        "admin/mata_mata.html",
        {"jogos": jogos, "msg": msg, "erro": erro},
        usuario=admin,
    )


@router.post("/mata-mata/{jogo_id}/times")
def definir_times(
    jogo_id: int,
    time_casa: str = Form(...),
    time_fora: str = Form(...),
    admin: Usuario = Depends(require_admin),
    db: Session = Depends(get_db),
):
    jogo = db.get(Jogo, jogo_id)
    if jogo is None or not jogo.is_mata_mata:
        return _redir("/admin/mata-mata", erro="Jogo de mata-mata não encontrado.")

    time_casa = time_casa.strip()
    time_fora = time_fora.strip()
    if not time_casa or not time_fora:
        return _redir("/admin/mata-mata", erro="Informe os dois times.")

    jogo.time_casa = time_casa
    jogo.time_fora = time_fora
    db.commit()
    return _redir("/admin/mata-mata", msg="Times atualizados.")
