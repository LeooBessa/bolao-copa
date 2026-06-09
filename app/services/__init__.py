"""Camada de serviços: regras de negócio (travamento, pontuação, ranking)."""

from app.services.palpites import (
    abrir_palpites_grupos,
    fechar_todos_palpites,
    palpite_travado,
    salvar_palpite,
)
from app.services.ranking import montar_ranking, posicao_do_usuario
from app.services.scoring import (
    aplicar_resultado,
    calcular_pontos_grupos,
    calcular_pontos_mata_mata,
)

__all__ = [
    "palpite_travado",
    "salvar_palpite",
    "fechar_todos_palpites",
    "abrir_palpites_grupos",
    "montar_ranking",
    "posicao_do_usuario",
    "aplicar_resultado",
    "calcular_pontos_grupos",
    "calcular_pontos_mata_mata",
]
