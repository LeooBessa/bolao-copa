"""Application factory do FastAPI.

Monta rotas, arquivos estáticos, templates e tratadores de exceção.
Exposto como `app` para o uvicorn (dev) e para a Vercel (api/index.py).
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.auth.dependencies import RedirectException
from app.routes import admin, auth, dashboard, historico, jogos, palpites, ranking
from app.templating import STATIC_DIR


def create_app() -> FastAPI:
    app = FastAPI(
        title="Bolão da Copa do Mundo Arianjo",
        docs_url=None,  # API interna; sem Swagger público
        redoc_url=None,
    )

    # Arquivos estáticos (CSS compilado do Tailwind, JS).
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    # --- Tratamento do redirect vindo das dependencies de auth ---------
    @app.exception_handler(RedirectException)
    async def _redirect_handler(
        request: Request, exc: RedirectException
    ) -> RedirectResponse:
        return RedirectResponse(url=exc.location, status_code=303)

    # --- Rotas ----------------------------------------------------------
    app.include_router(auth.router)
    app.include_router(dashboard.router)
    app.include_router(jogos.router)
    app.include_router(palpites.router)
    app.include_router(ranking.router)
    app.include_router(historico.router)
    app.include_router(admin.router)

    return app


app = create_app()
