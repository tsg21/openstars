"""Altair combat engine — tick loop, movement AI, and shooting.

Entry point: ``run_battle(snap, cfg) -> CombatLog``.
"""

from __future__ import annotations

from openstars.combat.altair.geometry import distance, in_range
from openstars.combat.altair.models import (
    AltairCombatConfig,
    BattleEndEvent,
    BattleSnapshot,
    CombatEvent,
    CombatLog,
    DamageAppliedEvent,
    Position,
    RoundEndEvent,
    RoundStartEvent,
    ShootingPhaseStartEvent,
    TickStartEvent,
    Token,
    TokenDestroyedEvent,
    TokenMovedEvent,
    WeaponFiredEvent,
)

# ---------------------------------------------------------------------------
# Movement budget helpers (PRD 82 §Movement)
# ---------------------------------------------------------------------------


def budget_round(quarters_round: int, S: int) -> int:
    """Arena-unit movement budget for one round.

    ``(quarters_round * S) // 4``  — no dampener penalty in v1.
    """
    return (quarters_round * S) // 4


def budget_tick(budget_round_val: int, T: int, k: int) -> int:
    """Arena-unit budget for tick *k* within a round.

    Distributes ``budget_round`` across *T* ticks so the sum is exact.
    """
    b = budget_round_val // T
    r = budget_round_val % T
    return b + (1 if k < r else 0)


# ---------------------------------------------------------------------------
# Simplified movement AI (v1)
# ---------------------------------------------------------------------------


def _pick_primary_target(token: Token, enemies: list[Token]) -> Token | None:
    """v1: closest living enemy by Euclidean distance, tie-break on id."""
    if not enemies:
        return None
    tx, ty = token.position.x, token.position.y
    return min(
        enemies,
        key=lambda e: (distance(tx, ty, e.position.x, e.position.y), e.id),
    )


def _move_toward(
    token: Token,
    target: Token,
    max_dist: int,
    arena_size: int,
) -> Position:
    """Move *token* toward *target* by up to *max_dist* arena units.

    Uses integer truncation for the step vector. Clamps to arena bounds.
    """
    dx = target.position.x - token.position.x
    dy = target.position.y - token.position.y
    d = distance(token.position.x, token.position.y, target.position.x, target.position.y)
    if d == 0 or max_dist == 0:
        return token.position.model_copy()

    # Scale the direction vector to at most max_dist
    step_x = (dx * max_dist) // d
    step_y = (dy * max_dist) // d

    new_x = max(0, min(arena_size - 1, token.position.x + step_x))
    new_y = max(0, min(arena_size - 1, token.position.y + step_y))
    return Position(x=new_x, y=new_y)


# ---------------------------------------------------------------------------
# Shooting phase (v1 stub — single weapon, single HP pool)
# ---------------------------------------------------------------------------


def _run_shooting_phase(
    tokens: list[Token],
    cfg: AltairCombatConfig,
    round_index: int,
    events: list[CombatEvent],
) -> None:
    """Fire once per living token. Deterministic order by token id."""
    events.append(ShootingPhaseStartEvent(round_index=round_index))

    alive = [t for t in tokens if t.hp > 0]
    for attacker in sorted(alive, key=lambda t: t.id):
        if attacker.hp <= 0:
            continue
        enemies = [t for t in alive if t.owner != attacker.owner and t.hp > 0]
        target = _pick_primary_target(attacker, enemies)
        if target is None:
            continue

        dist = distance(
            attacker.position.x,
            attacker.position.y,
            target.position.x,
            target.position.y,
        )
        hit = in_range(dist, attacker.weapon_range_classic, cfg.S, attacker.is_starbase)
        events.append(
            WeaponFiredEvent(
                attacker_id=attacker.id,
                target_id=target.id,
                damage=attacker.weapon_damage if hit else 0,
                hit=hit,
                round_index=round_index,
            )
        )
        if hit:
            target.hp = max(0, target.hp - attacker.weapon_damage)
            events.append(
                DamageAppliedEvent(
                    target_id=target.id,
                    damage=attacker.weapon_damage,
                    remaining_hp=target.hp,
                    round_index=round_index,
                )
            )
            if target.hp <= 0:
                events.append(
                    TokenDestroyedEvent(
                        token_id=target.id,
                        round_index=round_index,
                    )
                )


# ---------------------------------------------------------------------------
# Battle-end checks
# ---------------------------------------------------------------------------


def _battle_over(tokens: list[Token]) -> str | None:
    """Return an end reason string, or None if the battle continues."""
    alive_owners = {t.owner for t in tokens if t.hp > 0}
    if len(alive_owners) == 0:
        return "all_destroyed"
    if len(alive_owners) == 1:
        return "one_side_eliminated"
    return None


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def run_battle(snap: BattleSnapshot, cfg: AltairCombatConfig | None = None) -> CombatLog:
    """Run a complete Altair battle and return the event log.

    Deterministic: same *snap* and *cfg* always produce the same log.
    """
    if cfg is None:
        cfg = snap.config

    tokens = [t.model_copy(deep=True) for t in snap.tokens]
    events: list[CombatEvent] = []
    arena_size = cfg.arena_size

    for round_index in range(cfg.N_rounds):
        events.append(RoundStartEvent(round_index=round_index))

        # Pre-compute per-token round budgets
        budgets = {t.id: budget_round(t.movement_quarters, cfg.S) for t in tokens if t.hp > 0}

        # --- Movement ticks ---
        for tick_index in range(cfg.T):
            events.append(TickStartEvent(round_index=round_index, tick_index=tick_index))

            # Deterministic order: sort by token id (skip ±15% jitter in v1)
            # TODO: implement weight-based ordering with ±15% jitter (PRD 82)
            alive = sorted([t for t in tokens if t.hp > 0], key=lambda t: t.id)
            for token in alive:
                enemies = [t for t in alive if t.owner != token.owner and t.hp > 0]
                target = _pick_primary_target(token, enemies)
                if target is None:
                    continue

                tick_budget = budget_tick(budgets.get(token.id, 0), cfg.T, tick_index)
                if tick_budget == 0:
                    continue

                old_pos = token.position.model_copy()
                new_pos = _move_toward(token, target, tick_budget, arena_size)
                if new_pos.x != old_pos.x or new_pos.y != old_pos.y:
                    token.position = new_pos
                    events.append(
                        TokenMovedEvent(
                            token_id=token.id,
                            from_pos=old_pos,
                            to_pos=new_pos,
                            round_index=round_index,
                            tick_index=tick_index,
                        )
                    )

        # --- Shooting phase ---
        _run_shooting_phase(tokens, cfg, round_index, events)

        events.append(RoundEndEvent(round_index=round_index))

        reason = _battle_over(tokens)
        if reason is not None:
            events.append(BattleEndEvent(reason=reason))
            break
    else:
        events.append(BattleEndEvent(reason="max_rounds_reached"))

    return CombatLog(schema_version=cfg.ruleset_schema_version, config=cfg, events=events)
