"""Models ORM da aplicação.

Importar tudo aqui garante que o Alembic e o `Base.metadata` enxerguem
todas as tabelas ao gerar migrations / criar o schema.
"""

from app.models.enums import Fase, StatusJogo
from app.models.jogo import Jogo
from app.models.palpite import Palpite
from app.models.usuario import Usuario

__all__ = ["Fase", "StatusJogo", "Jogo", "Palpite", "Usuario"]
