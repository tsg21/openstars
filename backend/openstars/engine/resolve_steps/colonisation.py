"""Colonisation task resolution helpers."""

from dataclasses import dataclass

from openstars.engine.colonisation import COLONY_SHIP_HULL, recovered_minerals_for_colony_ships
from openstars.engine.models import (
    Cargo,
    Design,
    Fleet,
    FleetComposition,
    GameEvent,
    Minerals,
    PlanetState,
)

UNKNOWN_PLANET_NAME = "Unknown planet"


@dataclass(frozen=True)
class ColonizeResolution:
    fleet: Fleet
    planet: PlanetState | None
    events: list[GameEvent]
    dissolve_fleet: bool = False


def _fleet_name(fleet: Fleet, designs_by_id: dict[str, Design]) -> str:
    for entry in fleet.composition:
        design = designs_by_id.get(entry.design_id)
        if design is not None:
            return design.name
    return fleet.id


def fleet_has_colony_ship(fleet: Fleet, designs_by_id: dict[str, Design]) -> bool:
    """Return whether the fleet contains at least one colony ship."""
    return any(
        designs_by_id.get(entry.design_id) is not None
        and designs_by_id[entry.design_id].hull == COLONY_SHIP_HULL
        and entry.count > 0
        for entry in fleet.composition
    )


def colony_ship_entries(fleet: Fleet, designs_by_id: dict[str, Design]) -> list[FleetComposition]:
    """Return all colony ship composition entries in the fleet."""
    return [
        entry
        for entry in fleet.composition
        if designs_by_id.get(entry.design_id) is not None
        and designs_by_id[entry.design_id].hull == COLONY_SHIP_HULL
        and entry.count > 0
    ]


def recovered_colony_ship_minerals(
    entries: list[FleetComposition],
) -> Minerals:
    """Return total dismantle recovery for the provided colony ship entries."""
    return recovered_minerals_for_colony_ships(sum(entry.count for entry in entries))


def _failure_event(
    fleet: Fleet,
    designs_by_id: dict[str, Design],
    planet: PlanetState | None,
    planet_name: str,
    reason: str,
) -> GameEvent:
    return GameEvent(
        owner=fleet.owner,
        source_id=planet.id if planet is not None else None,
        code="colonisation.failed",
        values=[_fleet_name(fleet, designs_by_id), planet_name, reason],
    )


def execute_colonize_task(
    fleet: Fleet,
    planet: PlanetState | None,
    designs_by_id: dict[str, Design],
    planet_name: str | None = None,
) -> ColonizeResolution:
    """Resolve a colonize task for a fleet at a waypoint."""
    resolved_planet_name = planet_name or (planet.id if planet is not None else UNKNOWN_PLANET_NAME)

    if planet is None:
        return ColonizeResolution(
            fleet=fleet,
            planet=None,
            events=[
                _failure_event(
                    fleet,
                    designs_by_id,
                    None,
                    resolved_planet_name,
                    "no_planet",
                )
            ],
        )

    if planet.owner is not None:
        return ColonizeResolution(
            fleet=fleet,
            planet=planet,
            events=[
                _failure_event(
                    fleet,
                    designs_by_id,
                    planet,
                    resolved_planet_name,
                    "planet_already_owned",
                )
            ],
        )

    colony_entries = colony_ship_entries(fleet, designs_by_id)
    if not colony_entries:
        return ColonizeResolution(
            fleet=fleet,
            planet=planet,
            events=[
                _failure_event(
                    fleet,
                    designs_by_id,
                    planet,
                    resolved_planet_name,
                    "no_colony_ship",
                )
            ],
        )

    if fleet.cargo.colonists <= 0:
        return ColonizeResolution(
            fleet=fleet,
            planet=planet,
            events=[
                _failure_event(
                    fleet,
                    designs_by_id,
                    planet,
                    resolved_planet_name,
                    "no_colonists",
                )
            ],
        )

    recovered = recovered_colony_ship_minerals(colony_entries)
    surviving_composition = [
        entry
        for entry in fleet.composition
        if designs_by_id.get(entry.design_id) is None
        or designs_by_id[entry.design_id].hull != COLONY_SHIP_HULL
    ]
    updated_planet = planet.model_copy(
        update={
            "owner": fleet.owner,
            "population": fleet.cargo.colonists,
            "minerals": planet.minerals.model_copy(
                update={
                    "ironium": planet.minerals.ironium + recovered.ironium + fleet.cargo.ironium,
                    "boranium": planet.minerals.boranium
                    + recovered.boranium
                    + fleet.cargo.boranium,
                    "germanium": planet.minerals.germanium
                    + recovered.germanium
                    + fleet.cargo.germanium,
                }
            ),
        }
    )
    updated_fleet = fleet.model_copy(
        update={
            "composition": surviving_composition,
            "cargo": Cargo(),
        }
    )
    success_event = GameEvent(
        owner=fleet.owner,
        source_id=updated_planet.id,
        code="colonisation.colonised",
        values=[
            _fleet_name(fleet, designs_by_id),
            resolved_planet_name,
            fleet.cargo.colonists,
            recovered.ironium,
            recovered.boranium,
            recovered.germanium,
        ],
    )
    return ColonizeResolution(
        fleet=updated_fleet,
        planet=updated_planet,
        events=[success_event],
        dissolve_fleet=len(surviving_composition) == 0,
    )
