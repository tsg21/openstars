"""Altair combat model (ruleset id ``altair``).

Scaled integer arena, ticks per combat round, Euclidean ``isqrt`` distance.
PRD: docs/prd/82-combat-altair.md
"""

from openstars.combat.altair.engine import run_battle
from openstars.combat.altair.models import (
    AltairCombatConfig,
    BattleSnapshot,
    CombatLog,
    Token,
    TokenWeapon,
)

__all__ = [
    "AltairCombatConfig",
    "BattleSnapshot",
    "CombatLog",
    "Token",
    "TokenWeapon",
    "run_battle",
]
