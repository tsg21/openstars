"""Colonisation resolution helpers (PRD 16)."""

from openstars.engine.models import Design, Fleet, GameEvent, Minerals, PlanetState

COLONY_SHIP_HULL = "colony_ship"
DISMANTLE_RECOVERY_NUMERATOR = 1
DISMANTLE_RECOVERY_DENOMINATOR = 3
COLONY_SHIP_COST = Minerals(ironium=5, boranium=5, germanium=15)


def fleet_has_colony_ship(fleet: Fleet, designs_by_id: dict[str, Design]) -> bool:
    return count_colony_ships(fleet, designs_by_id) > 0


def count_colony_ships(fleet: Fleet, designs_by_id: dict[str, Design]) -> int:
    return sum(
        comp.count
        for comp in fleet.composition
        if designs_by_id.get(comp.design_id) is not None
        and designs_by_id[comp.design_id].hull == COLONY_SHIP_HULL
    )


def recovered_minerals_for_colony_ships(count: int) -> Minerals:
    return Minerals(
        ironium=(COLONY_SHIP_COST.ironium * count * DISMANTLE_RECOVERY_NUMERATOR)
        // DISMANTLE_RECOVERY_DENOMINATOR,
        boranium=(COLONY_SHIP_COST.boranium * count * DISMANTLE_RECOVERY_NUMERATOR)
        // DISMANTLE_RECOVERY_DENOMINATOR,
        germanium=(COLONY_SHIP_COST.germanium * count * DISMANTLE_RECOVERY_NUMERATOR)
        // DISMANTLE_RECOVERY_DENOMINATOR,
    )


def _failed_event(fleet: Fleet, planet: PlanetState | None, reason: str) -> GameEvent:
    return GameEvent(
        type="colonize_failed",
        turn=0,
        fleet_id=fleet.id,
        owner=fleet.owner,
        planet_id=planet.id if planet else None,
        reason=reason,
    )


def resolve_colonize_task(
    fleet: Fleet,
    planet: PlanetState | None,
    designs_by_id: dict[str, Design],
) -> tuple[Fleet | None, PlanetState | None, GameEvent]:
    if planet is None:
        return fleet, planet, _failed_event(fleet, planet, "no_planet")
    if planet.owner is not None:
        return fleet, planet, _failed_event(fleet, planet, "planet_already_owned")

    colony_ship_count = count_colony_ships(fleet, designs_by_id)
    if colony_ship_count <= 0:
        return fleet, planet, _failed_event(fleet, planet, "no_colony_ship")
    if fleet.cargo.colonists <= 0:
        return fleet, planet, _failed_event(fleet, planet, "no_colonists")

    landed_colonists = fleet.cargo.colonists
    recovered = recovered_minerals_for_colony_ships(colony_ship_count)
    updated_planet = planet.model_copy(
        update={
            "owner": fleet.owner,
            "population": landed_colonists,
            "minerals": Minerals(
                ironium=planet.minerals.ironium + recovered.ironium + fleet.cargo.ironium,
                boranium=planet.minerals.boranium + recovered.boranium + fleet.cargo.boranium,
                germanium=planet.minerals.germanium + recovered.germanium + fleet.cargo.germanium,
            ),
        }
    )

    remaining_composition = [
        comp
        for comp in fleet.composition
        if designs_by_id.get(comp.design_id) is None
        or designs_by_id[comp.design_id].hull != COLONY_SHIP_HULL
    ]
    event = GameEvent(
        type="colonised",
        turn=0,
        fleet_id=fleet.id,
        owner=fleet.owner,
        planet_id=planet.id,
        colonists_landed=landed_colonists,
        minerals_recovered=recovered,
    )
    if not remaining_composition:
        return None, updated_planet, event

    updated_fleet = fleet.model_copy(
        update={
            "composition": remaining_composition,
            "cargo": fleet.cargo.model_copy(
                update={
                    "colonists": 0,
                    "ironium": 0,
                    "boranium": 0,
                    "germanium": 0,
                }
            ),
        }
    )
    return updated_fleet, updated_planet, event
