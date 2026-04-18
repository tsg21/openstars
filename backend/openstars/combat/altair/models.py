"""Altair combat data models.

All types used by the Altair combat engine. Kept internal to the
``openstars.combat.altair`` package — the main game engine does not
depend on these.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


class AltairCombatConfig(BaseModel):
    """Tuning knobs for an Altair battle.

    See PRD 82 §Constants.
    """

    S: int = Field(default=1000, gt=0, description="Scale factor (arena units per classic square)")
    T: int = Field(default=20, gt=0, description="Movement ticks per combat round")
    N_rounds: int = Field(default=16, gt=0, description="Maximum combat rounds per battle")
    ruleset_schema_version: str = Field(
        default="altair-v3",
        description="Schema version tag embedded in combat logs",
    )

    @property
    def arena_size(self) -> int:
        """Arena extent per axis: ``10 * S``."""
        return 10 * self.S


# ---------------------------------------------------------------------------
# Positions and tokens
# ---------------------------------------------------------------------------


class Position(BaseModel):
    """Integer coordinate in the Altair arena."""

    x: int = 0
    y: int = 0


class Token(BaseModel):
    """A single combat token (ship stack or starbase).

    Fields kept minimal for the v1 prototype — extend as needed.
    """

    id: str
    owner: str
    position: Position
    hp: int = Field(default=100, ge=0, description="Hit-points (single pool for v1)")
    movement_quarters: int = Field(
        default=4,
        ge=0,
        description="Classic quarter-squares of movement per round (from hull/engines)",
    )
    weapon_damage: int = Field(default=20, ge=0, description="Flat damage per shot (v1 stub)")
    weapon_range_classic: int = Field(
        default=2,
        ge=0,
        description="Weapon range in classic squares",
    )
    is_starbase: bool = False
    label: str | None = None


# ---------------------------------------------------------------------------
# Battle snapshot (input)
# ---------------------------------------------------------------------------


class BattleSnapshot(BaseModel):
    """Everything needed to run a deterministic Altair battle.

    Token ids must be unique within the snapshot.
    """

    tokens: list[Token]
    config: AltairCombatConfig = Field(default_factory=AltairCombatConfig)


# ---------------------------------------------------------------------------
# Combat events (output)
# ---------------------------------------------------------------------------


class RoundStartEvent(BaseModel):
    type: Literal["round_start"] = "round_start"
    round_index: int


class TickStartEvent(BaseModel):
    type: Literal["tick_start"] = "tick_start"
    round_index: int
    tick_index: int


class TokenMovedEvent(BaseModel):
    type: Literal["token_moved"] = "token_moved"
    token_id: str
    from_pos: Position
    to_pos: Position
    round_index: int
    tick_index: int


class ShootingPhaseStartEvent(BaseModel):
    type: Literal["shooting_phase_start"] = "shooting_phase_start"
    round_index: int


class WeaponFiredEvent(BaseModel):
    type: Literal["weapon_fired"] = "weapon_fired"
    attacker_id: str
    target_id: str
    damage: int
    dissipation_pct: int = Field(ge=0, le=100)
    hit: bool
    round_index: int


class DamageAppliedEvent(BaseModel):
    type: Literal["damage_applied"] = "damage_applied"
    target_id: str
    damage: int
    remaining_hp: int
    round_index: int


class TokenDestroyedEvent(BaseModel):
    type: Literal["token_destroyed"] = "token_destroyed"
    token_id: str
    round_index: int


class RoundEndEvent(BaseModel):
    type: Literal["round_end"] = "round_end"
    round_index: int


class BattleEndEvent(BaseModel):
    type: Literal["battle_end"] = "battle_end"
    reason: str


CombatEvent = (
    RoundStartEvent
    | TickStartEvent
    | TokenMovedEvent
    | ShootingPhaseStartEvent
    | WeaponFiredEvent
    | DamageAppliedEvent
    | TokenDestroyedEvent
    | RoundEndEvent
    | BattleEndEvent
)


# ---------------------------------------------------------------------------
# Combat log (output document)
# ---------------------------------------------------------------------------

CURRENT_SCHEMA_VERSION = "altair-v3"


class CombatLog(BaseModel):
    """Versioned, ordered log of a complete Altair battle."""

    schema_version: str = CURRENT_SCHEMA_VERSION
    config: AltairCombatConfig
    events: list[CombatEvent] = Field(default_factory=list)
