"""Combat detection and resolution step."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from math import ceil

from openstars.combat.altair.engine import run_battle
from openstars.combat.altair.geometry import scaled_sin_cos
from openstars.combat.altair.models import (
    AltairCombatConfig,
    BattleSnapshot,
    CombatLog,
    DamageAppliedEvent,
    TokenDestroyedEvent,
)
from openstars.combat.altair.models import (
    Position as ArenaPosition,
)
from openstars.combat.fleet_to_tokens import tokens_from_fleet
from openstars.engine.component_catalogue import ComponentCatalogue
from openstars.engine.models import Fleet, GameEvent, Position
from openstars.engine.turn_context import TurnContext
from openstars.storage.base import GameStorage


def detect_battle_sites(fleets: Iterable[Fleet]) -> list[list[Fleet]]:
    grouped: dict[tuple[int, int], list[Fleet]] = defaultdict(list)
    for fleet in fleets:
        grouped[(fleet.position.x, fleet.position.y)].append(fleet)

    sites: list[tuple[tuple[int, int], list[Fleet]]] = []
    for coord, group in grouped.items():
        owners = {fleet.owner for fleet in group}
        if len(owners) < 2:
            continue
        sites.append((coord, sorted(group, key=lambda fleet: fleet.id)))

    sites.sort(key=lambda item: f"{item[0][0]},{item[0][1]}")
    return [group for _, group in sites]


def arena_entry_positions(owners: list[str], arena_size: int) -> dict[str, Position]:
    centre = arena_size // 2
    if len(owners) <= 1:
        return {owner: Position(x=centre, y=centre) for owner in owners}

    radius = arena_size * 4 // 10
    owner_positions: dict[str, Position] = {}
    for index, owner in enumerate(owners):
        sin_scaled, cos_scaled = scaled_sin_cos(index, len(owners))
        owner_positions[owner] = Position(
            x=centre + (radius * cos_scaled) // 1_000_000,
            y=centre + (radius * sin_scaled) // 1_000_000,
        )
    return owner_positions


def build_battle_snapshot(
    fleets: list[Fleet],
    designs_by_id: dict,
    catalogue: ComponentCatalogue,
    config: AltairCombatConfig,
    *,
    battle_id: str,
) -> BattleSnapshot:
    owners = sorted({fleet.owner for fleet in fleets})
    owner_positions = arena_entry_positions(owners, config.arena_size)
    tokens = []
    for fleet in fleets:
        tokens.extend(
            tokens_from_fleet(
                fleet,
                designs_by_id,
                catalogue,
                position=ArenaPosition.model_validate(owner_positions[fleet.owner].model_dump()),
                token_id_prefix=battle_id,
            )
        )
    return BattleSnapshot(tokens=tokens, config=config)


def _final_hp_by_token(log: CombatLog, snap_before: BattleSnapshot) -> dict[str, int]:
    hp = {token.id: token.hp for token in snap_before.tokens}
    for event in log.events:
        if isinstance(event, DamageAppliedEvent):
            hp[event.target_id] = event.remaining_hp
        elif isinstance(event, TokenDestroyedEvent):
            hp[event.token_id] = 0
    return hp


def apply_casualties(
    snap_before: BattleSnapshot,
    log: CombatLog,
    fleets_by_id: dict[str, Fleet],
) -> tuple[dict[str, Fleet], dict[str, int]]:
    final_hp = _final_hp_by_token(log, snap_before)
    lost_by_owner: dict[str, int] = defaultdict(int)

    for token in snap_before.tokens:
        if token.ship_count <= 0:
            continue
        _prefix, fleet_id, index_str = token.id.rsplit("-", 2)
        fleet = fleets_by_id.get(fleet_id)
        if fleet is None:
            continue
        comp_index = int(index_str)
        if comp_index < 0 or comp_index >= len(fleet.composition):
            continue

        initial_hp = token.hp
        remaining_hp = max(0, final_hp.get(token.id, initial_hp))
        if initial_hp <= 0:
            destroyed = token.ship_count
        else:
            lost_ratio = max(0.0, min(1.0, (initial_hp - remaining_hp) / initial_hp))
            destroyed = min(token.ship_count, ceil(token.ship_count * lost_ratio))

        new_count = max(0, fleet.composition[comp_index].count - destroyed)
        lost_by_owner[fleet.owner] += destroyed
        fleet.composition[comp_index] = fleet.composition[comp_index].model_copy(
            update={"count": new_count}
        )
        fleets_by_id[fleet.id] = fleet

    updated: dict[str, Fleet] = {}
    for fleet_id, fleet in fleets_by_id.items():
        composition = [entry for entry in fleet.composition if entry.count > 0]
        if sum(entry.count for entry in composition) <= 0:
            continue
        updated[fleet_id] = fleet.model_copy(update={"composition": composition})

    return updated, dict(lost_by_owner)


def run_combat_step(
    ruleset: str,
    snap: BattleSnapshot,
    *,
    cfg: AltairCombatConfig | None = None,
) -> CombatLog:
    if ruleset == "altair":
        return run_battle(snap, cfg)
    if ruleset == "classic":
        raise NotImplementedError("classic ruleset not implemented")
    raise ValueError(f"unsupported combat ruleset: {ruleset}")


def resolve_combat(ctx: TurnContext, storage: GameStorage) -> None:
    if ctx.component_catalogue is None:
        raise ValueError("resolve_combat requires a component catalogue")

    battle_sites = detect_battle_sites(ctx.fleets_by_id.values())
    for site in battle_sites:
        battle_id = ctx.allocate_id("BT")
        snapshot = build_battle_snapshot(
            site,
            ctx.designs_by_id,
            ctx.component_catalogue,
            AltairCombatConfig(),
            battle_id=battle_id,
        )
        log = run_combat_step(ctx.global_state.game.combat_ruleset, snapshot)
        storage.save_combat_log(ctx.game_id, battle_id, log)

        pre_battle_by_id = {fleet.id: fleet.model_copy(deep=True) for fleet in site}
        ctx.fleets_by_id, ships_lost_by_owner = apply_casualties(snapshot, log, ctx.fleets_by_id)

        location_name = "deep space"
        site_coord = (site[0].position.x, site[0].position.y)
        galaxy_planet = next(
            (planet for planet in ctx.galaxy.planets if (planet.x, planet.y) == site_coord),
            None,
        )
        if galaxy_planet is not None:
            location_name = galaxy_planet.name

        owners = sorted({fleet.owner for fleet in site})
        for owner in owners:
            source_id = sorted(
                fleet.id for fleet in pre_battle_by_id.values() if fleet.owner == owner
            )[0]
            ctx.append_event(
                GameEvent(
                    owner=owner,
                    source_id=source_id,
                    code="combat.resolved",
                    values=[battle_id, location_name, ships_lost_by_owner.get(owner, 0)],
                )
            )

    ctx.fleets = [ctx.fleets_by_id[fleet_id] for fleet_id in sorted(ctx.fleets_by_id)]


# Backward-compatible export name requested in task text.
run_combat = run_combat_step
