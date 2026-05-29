"""Enums de domínio: fases do torneio e status do jogo."""

from __future__ import annotations

import enum


class Fase(str, enum.Enum):
    """Fases da Copa 2026 (48 times → Round of 32 antes das oitavas)."""

    GRUPOS = "grupos"
    TRINTA_E_DOIS_AVOS = "trinta_e_dois_avos"  # Round of 32
    OITAVAS = "oitavas"
    QUARTAS = "quartas"
    SEMIFINAL = "semifinal"
    TERCEIRO = "terceiro"
    FINAL = "final"

    @property
    def is_mata_mata(self) -> bool:
        """True para qualquer fase eliminatória (não-grupos)."""
        return self is not Fase.GRUPOS

    @property
    def label(self) -> str:
        """Rótulo amigável para exibição na UI."""
        return {
            Fase.GRUPOS: "Fase de Grupos",
            Fase.TRINTA_E_DOIS_AVOS: "32 avos de final",
            Fase.OITAVAS: "Oitavas de final",
            Fase.QUARTAS: "Quartas de final",
            Fase.SEMIFINAL: "Semifinal",
            Fase.TERCEIRO: "Disputa de 3º lugar",
            Fase.FINAL: "Final",
        }[self]


# Ordem canônica das fases (usada para ordenar listagens).
ORDEM_FASES: dict[Fase, int] = {fase: i for i, fase in enumerate(Fase)}


class StatusJogo(str, enum.Enum):
    """Status de um jogo no fluxo de palpites."""

    ABERTO = "aberto"          # aceitando palpites
    FECHADO = "fechado"        # palpites travados, sem resultado ainda
    FINALIZADO = "finalizado"  # resultado oficial registrado e pontuado

    @property
    def label(self) -> str:
        return {
            StatusJogo.ABERTO: "Aberto",
            StatusJogo.FECHADO: "Fechado",
            StatusJogo.FINALIZADO: "Finalizado",
        }[self]
