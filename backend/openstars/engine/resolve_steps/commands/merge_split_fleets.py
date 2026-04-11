"""Apply merge/split fleet commands."""

from collections import defaultdict
from math import floor

from openstars.engine.models import (
    Cargo,
    Fleet,
    FleetComposition,
    MergeSplitFleetsCommand,
    Position,
)
from openstars.engine.turn_context import TurnContext

_CARGO_TYPES = ("ironium", "boranium", "germanium", "colonists")


def _total_ships(composition: list[FleetComposition]) -> int:
    return sum(entry.count for entry in composition)


def _fuel_capacity(ctx: TurnContext, composition: list[FleetComposition]) -> int:
    total = 0
    for entry in composition:
        design = ctx.designs_by_id.get(entry.design_id)
        if design is None:
            continue
        total += design.fuel_capacity * entry.count
    return total


def _cargo_capacity(ctx: TurnContext, composition: list[FleetComposition]) -> int:
    total = 0
    for entry in composition:
        design = ctx.designs_by_id.get(entry.design_id)
        if design is None:
            continue
        total += design.cargo_capacity * entry.count
    return total


def _distribute_resource(total: int, capacities: dict[str, int]) -> dict[str, int]:
    cap_sum = sum(capacities.values())
    if cap_sum == 0:
        return {fleet_id: 0 for fleet_id in capacities}

    shares: dict[str, int] = {}
    allocated = 0
    for fleet_id, capacity in capacities.items():
        share = floor(total * capacity / cap_sum)
        shares[fleet_id] = share
        allocated += share

    remainder = total - allocated
    if remainder > 0:
        winner = max(
            capacities.keys(),
            key=lambda fleet_id: (capacities[fleet_id], not fleet_id.startswith("tmp_"), fleet_id),
        )
        shares[winner] += remainder

    return shares


def validate_merge_split_fleets_command(
    ctx: TurnContext,
    username: str,
    cmd: MergeSplitFleetsCommand,
) -> None:
    if not cmd.fleets:
        raise ValueError("merge_split_fleets requires at least one fleet entry")

    seen_ids: set[str] = set()
    referenced_real_fleets: list[Fleet] = []

    for entry in cmd.fleets:
        if entry.fleet_id in seen_ids:
            raise ValueError(f"merge_split_fleets duplicate fleet id: {entry.fleet_id}")
        seen_ids.add(entry.fleet_id)

        if entry.fleet_id.startswith("tmp_"):
            if entry.fleet_id in ctx.fleets_by_id:
                raise ValueError(
                    f"merge_split_fleets tmp id clashes with existing fleet id: {entry.fleet_id}"
                )
            continue

        fleet = ctx.fleets_by_id.get(entry.fleet_id)
        if fleet is None:
            raise ValueError(f"merge_split_fleets unknown fleet id: {entry.fleet_id}")
        if fleet.owner != username:
            raise ValueError(f"merge_split_fleets fleet not owned by player: {entry.fleet_id}")
        referenced_real_fleets.append(fleet)

    if not referenced_real_fleets:
        raise ValueError("merge_split_fleets must include at least one existing fleet id")

    expected_position = referenced_real_fleets[0].position
    for fleet in referenced_real_fleets[1:]:
        if fleet.position != expected_position:
            raise ValueError("merge_split_fleets requires all listed fleets to be colocated")

    source_totals: dict[str, int] = defaultdict(int)
    for fleet in referenced_real_fleets:
        for ship in fleet.composition:
            source_totals[ship.design_id] += ship.count

    result_totals: dict[str, int] = defaultdict(int)
    for entry in cmd.fleets:
        for ship in entry.ships:
            if ship.count < 0:
                raise ValueError("merge_split_fleets ship counts must be non-negative")
            result_totals[ship.design_id] += ship.count

    if dict(source_totals) != dict(result_totals):
        raise ValueError("merge_split_fleets ship totals do not match source fleets")

    if sum(result_totals.values()) <= 0:
        raise ValueError("merge_split_fleets cannot dissolve all fleets")


def apply_merge_split_fleets_command(
    ctx: TurnContext,
    username: str,
    cmd: MergeSplitFleetsCommand,
) -> dict[str, str]:
    validate_merge_split_fleets_command(ctx, username, cmd)

    existing_fleets = [
        ctx.fleets_by_id[entry.fleet_id]
        for entry in cmd.fleets
        if not entry.fleet_id.startswith("tmp_")
    ]
    position = existing_fleets[0].position

    total_fuel = sum(fleet.fuel for fleet in existing_fleets)
    total_cargo = Cargo(
        ironium=sum(fleet.cargo.ironium for fleet in existing_fleets),
        boranium=sum(fleet.cargo.boranium for fleet in existing_fleets),
        germanium=sum(fleet.cargo.germanium for fleet in existing_fleets),
        colonists=sum(fleet.cargo.colonists for fleet in existing_fleets),
    )

    tmp_to_real: dict[str, str] = {}
    touched_fleet_ids: list[str] = []

    for entry in cmd.fleets:
        composition = [ship.model_copy() for ship in entry.ships]
        if entry.fleet_id.startswith("tmp_"):
            real_id = ctx.allocate_id("FL")
            tmp_to_real[entry.fleet_id] = real_id
            fleet_name = entry.name or f"Fleet {real_id}"
            ctx.fleets_by_id[real_id] = Fleet(
                id=real_id,
                name=fleet_name,
                owner=username,
                position=Position(x=position.x, y=position.y),
                composition=composition,
                cargo=Cargo(),
                fuel=0,
                waypoints=[],
            )
            touched_fleet_ids.append(real_id)
            continue

        fleet = ctx.fleets_by_id[entry.fleet_id]
        fleet.composition = composition
        if entry.name is not None:
            fleet.name = entry.name
        touched_fleet_ids.append(fleet.id)

    for fleet_id in list(touched_fleet_ids):
        fleet = ctx.fleets_by_id.get(fleet_id)
        if fleet is None:
            continue
        if _total_ships(fleet.composition) <= 0:
            del ctx.fleets_by_id[fleet_id]

    surviving_ids = [fleet_id for fleet_id in touched_fleet_ids if fleet_id in ctx.fleets_by_id]

    fuel_caps = {
        fleet_id: _fuel_capacity(ctx, ctx.fleets_by_id[fleet_id].composition)
        for fleet_id in surviving_ids
    }
    fuel_shares = _distribute_resource(total_fuel, fuel_caps)

    cargo_caps = {
        fleet_id: _cargo_capacity(ctx, ctx.fleets_by_id[fleet_id].composition)
        for fleet_id in surviving_ids
    }

    cargo_shares = {
        cargo_type: _distribute_resource(getattr(total_cargo, cargo_type), cargo_caps)
        for cargo_type in _CARGO_TYPES
    }

    for fleet_id in surviving_ids:
        fleet = ctx.fleets_by_id[fleet_id]
        fleet.fuel = fuel_shares.get(fleet_id, 0)
        fleet.cargo = Cargo(
            ironium=cargo_shares["ironium"].get(fleet_id, 0),
            boranium=cargo_shares["boranium"].get(fleet_id, 0),
            germanium=cargo_shares["germanium"].get(fleet_id, 0),
            colonists=cargo_shares["colonists"].get(fleet_id, 0),
        )

    return tmp_to_real
