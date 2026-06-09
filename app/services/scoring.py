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

A pontuação oficial é GRAVADA em `palpite.pontos` quando o admin registra o
resultado (`aplicar_resultado`). As mesmas regras são reaproveitadas para a
pontuação PROVISÓRIA (tabela ao vivo), aplicando-as ao placar parcial.
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


# --- Núcleo das regras (recebem placares explícitos) -------------------
def pontos_grupos(
    gc_palpite: int, gf_palpite: int, gc_real: int | None, gf_real: int | None
) -> int:
    """Pontos de um palpite contra um placar de grupos qualquer."""
    if gc_real is None or gf_real is None:
        return 0
    if gc_palpite == gc_real and gf_palpite == gf_real:
        return 3
    acertou = _resultado_1x2(gc_palpite, gf_palpite) == _resultado_1x2(
        gc_real, gf_real
    )
    return 1 if acertou else 0


def pontos_mata_mata(
    gc_palpite: int,
    gf_palpite: int,
    classif_palpite: str | None,
    time_casa: str,
    time_fora: str,
    gc_real: int | None,
    gf_real: int | None,
    classif_real: str | None,
) -> int:
    """Pontos de um palpite contra um placar de mata-mata qualquer."""
    if gc_real is None or gf_real is None or not classif_real:
        return 0
    # Classificado implícito pelo palpite (ou o escolhido, se empate).
    if gc_palpite > gf_palpite:
        classif_p = time_casa
    elif gf_palpite > gc_palpite:
        classif_p = time_fora
    else:
        classif_p = classif_palpite
    if classif_p != classif_real:
        return 0
    placar_exato = gc_palpite == gc_real and gf_palpite == gf_real
    return 3 if placar_exato else 1


# --- Wrappers de conveniência (resultado OFICIAL) ----------------------
def calcular_pontos_grupos(palpite: Palpite, jogo: Jogo) -> int:
    return pontos_grupos(
        palpite.gols_casa_palpite,
        palpite.gols_fora_palpite,
        jogo.gols_casa_real,
        jogo.gols_fora_real,
    )


def calcular_pontos_mata_mata(palpite: Palpite, jogo: Jogo) -> int:
    return pontos_mata_mata(
        palpite.gols_casa_palpite,
        palpite.gols_fora_palpite,
        palpite.classificado_palpite,
        jogo.time_casa,
        jogo.time_fora,
        jogo.gols_casa_real,
        jogo.gols_fora_real,
        jogo.classificado_real,
    )


def calcular_pontos(palpite: Palpite, jogo: Jogo) -> int:
    """Despacha para a regra correta conforme a fase do jogo (resultado oficial)."""
    if jogo.is_mata_mata:
        return calcular_pontos_mata_mata(palpite, jogo)
    return calcular_pontos_grupos(palpite, jogo)


# --- Pontuação PROVISÓRIA (placar ao vivo) -----------------------------
def pontos_provisorios(palpite: Palpite, jogo: Jogo) -> int:
    """Pontos que o palpite faria com o placar parcial atual (ao vivo).

    No mata-mata, o classificado provisório é quem está na frente (ninguém
    pontua enquanto estiver empatado, pois o classificado ainda é indefinido).
    """
    gc, gf = jogo.gols_casa_ao_vivo, jogo.gols_fora_ao_vivo
    if gc is None or gf is None:
        return 0
    if jogo.is_mata_mata:
        if gc > gf:
            classif = jogo.time_casa
        elif gf > gc:
            classif = jogo.time_fora
        else:
            classif = None
        return pontos_mata_mata(
            palpite.gols_casa_palpite,
            palpite.gols_fora_palpite,
            palpite.classificado_palpite,
            jogo.time_casa,
            jogo.time_fora,
            gc,
            gf,
            classif,
        )
    return pontos_grupos(
        palpite.gols_casa_palpite, palpite.gols_fora_palpite, gc, gf
    )


def aplicar_resultado(
    db: Session,
    jogo: Jogo,
    *,
    gols_casa: int,
    gols_fora: int,
    classificado_real: str | None,
) -> int:
    """Registra o resultado oficial e pontua todos os palpites do jogo.

    Marca o jogo como FINALIZADO, encerra o "ao vivo", grava `pontos` em cada
    palpite e faz commit. Retorna a quantidade de palpites pontuados.
    """
    jogo.gols_casa_real = gols_casa
    jogo.gols_fora_real = gols_fora
    jogo.classificado_real = classificado_real if jogo.is_mata_mata else None
    jogo.status = StatusJogo.FINALIZADO
    jogo.ao_vivo = False  # acabou: sai da tabela ao vivo

    for palpite in jogo.palpites:
        palpite.pontos = calcular_pontos(palpite, jogo)

    db.commit()
    return len(jogo.palpites)
