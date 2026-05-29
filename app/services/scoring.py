"""Lógica de pontuação.

Regras (do spec):

Fase de grupos
  - placar exato ............................ 3 pontos
  - acertou o resultado (1/X/2) ............. 1 ponto
  - errou .................................... 0 pontos

Mata-mata (o classificado faz parte do resultado; empate sozinho não pontua)
  - placar exato + classificado correto ..... 3 pontos
  - classificado correto (placar errado) .... 1 ponto
  - acertou empate mas errou classificado ... 0 pontos
  - errou ................................... 0 pontos

A pontuação é GRAVADA em `palpite.pontos` quando o admin registra o resultado
oficial (`aplicar_resultado`). Nunca é recalculada a cada carregamento.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.enums import StatusJogo
from app.models.jogo import Jogo
from app.models.palpite import Palpite


def _resultado_1x2(gols_casa: int, gols_fora: int) -> str:
    """Classifica um placar como '1' (casa), '2' (fora) ou 'X' (empate)."""
    if gols_casa > gols_fora:
        return "1"
    if gols_fora > gols_casa:
        return "2"
    return "X"


def calcular_pontos_grupos(palpite: Palpite, jogo: Jogo) -> int:
    """Pontuação de um palpite na fase de grupos."""
    if not jogo.tem_resultado:
        return 0

    placar_exato = (
        palpite.gols_casa_palpite == jogo.gols_casa_real
        and palpite.gols_fora_palpite == jogo.gols_fora_real
    )
    if placar_exato:
        return 3

    acertou_resultado = _resultado_1x2(
        palpite.gols_casa_palpite, palpite.gols_fora_palpite
    ) == _resultado_1x2(jogo.gols_casa_real, jogo.gols_fora_real)
    return 1 if acertou_resultado else 0


def _classificado_do_palpite(palpite: Palpite, jogo: Jogo) -> str | None:
    """Time que o usuário previu que avança.

    Se o palpite não é empate, o classificado é implícito pelo placar; se for
    empate, vem de `classificado_palpite`.
    """
    if palpite.gols_casa_palpite > palpite.gols_fora_palpite:
        return jogo.time_casa
    if palpite.gols_fora_palpite > palpite.gols_casa_palpite:
        return jogo.time_fora
    return palpite.classificado_palpite


def calcular_pontos_mata_mata(palpite: Palpite, jogo: Jogo) -> int:
    """Pontuação de um palpite no mata-mata."""
    if not jogo.tem_resultado or not jogo.classificado_real:
        return 0

    acertou_classificado = (
        _classificado_do_palpite(palpite, jogo) == jogo.classificado_real
    )
    if not acertou_classificado:
        # Inclui o caso "acertou empate mas errou quem avança".
        return 0

    placar_exato = (
        palpite.gols_casa_palpite == jogo.gols_casa_real
        and palpite.gols_fora_palpite == jogo.gols_fora_real
    )
    return 3 if placar_exato else 1


def calcular_pontos(palpite: Palpite, jogo: Jogo) -> int:
    """Despacha para a regra correta conforme a fase do jogo."""
    if jogo.is_mata_mata:
        return calcular_pontos_mata_mata(palpite, jogo)
    return calcular_pontos_grupos(palpite, jogo)


def aplicar_resultado(
    db: Session,
    jogo: Jogo,
    *,
    gols_casa: int,
    gols_fora: int,
    classificado_real: str | None,
) -> int:
    """Registra o resultado oficial e pontua todos os palpites do jogo.

    Marca o jogo como FINALIZADO, grava `pontos` em cada palpite e faz commit.
    Retorna a quantidade de palpites pontuados.
    """
    jogo.gols_casa_real = gols_casa
    jogo.gols_fora_real = gols_fora
    jogo.classificado_real = classificado_real if jogo.is_mata_mata else None
    jogo.status = StatusJogo.FINALIZADO

    for palpite in jogo.palpites:
        palpite.pontos = calcular_pontos(palpite, jogo)

    db.commit()
    return len(jogo.palpites)
