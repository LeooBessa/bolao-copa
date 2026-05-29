"""Entrypoint da Vercel.

A Vercel detecta a variável `app` (ASGI) neste arquivo dentro de /api e a
serve como uma serverless function. Todas as rotas são reescritas para cá
via vercel.json.
"""

from app.main import app  # noqa: F401  (exportado para a Vercel)
