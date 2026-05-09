"""Fleet movement using integer arithmetic (PRD 07).

1 light-year = 2^29 coordinate units.
All computation is integer-only — no floating point.
"""

import logging
from dataclasses import dataclass

from openstars.engine.galaxy import LIGHT_YEAR
from openstars.engine.models import Design, Fleet, GameEvent, PlanetState, Position, Waypoint
from openstars.engine.race.models import LRT, Race
from openstars.engine.resolve_steps.colonisation import execute_colonise_task
from openstars.engine.resolve_steps.freight import (
    execute_transfer_task,
    execute_transport_task,
    fleet_fuel_capacity,
)
from openstars.engine.turn_context import TurnContext
from openstars.engine.util import compute_bearing, isqrt

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class WaypointExecutionResult:
    fleet: Fleet | None
    events: list[GameEvent]


def _execute_waypoint_task(
    fleet: Fleet,
    wp: Waypoint,
    fleets_by_id: dict[str, Fleet],
    planets_by_coord: dict[tuple[int, int], PlanetState],
    planets_by_id: dict[str, PlanetState],
    designs_by_id: dict[str, Design],
    planet_names_by_id: dict[str, str] | None = None,
) -> WaypointExecutionResult:
    if wp.task is None:
        return WaypointExecutionResult(fleet=fleet, events=[])

    if wp.task.type == "transport":
        planet = planets_by_coord.get((wp.x, wp.y))
        if planet is None:
            return WaypointExecutionResult(fleet=fleet, events=[])
        updated_fleet, updated_planet = execute_transport_task(
            fleet,
            planet,
            wp.task,
            designs_by_id,
        )
        planets_by_id[updated_planet.id] = updated_planet
        planets_by_coord[(wp.x, wp.y)] = updated_planet
        return WaypointExecutionResult(fleet=updated_fleet, events=[])

    if wp.task.type == "transfer" and wp.task.fleet_id is not None:
        target = fleets_by_id.get(wp.task.fleet_id)
        if (
            target is None
            or target.owner != fleet.owner
            or target.position.x != wp.x
            or target.position.y != wp.y
        ):
            return WaypointExecutionResult(fleet=fleet, events=[])
        updated_fleet, updated_target = execute_transfer_task(fleet, target, wp.task, designs_by_id)
        fleets_by_id[target.id] = updated_target
        return WaypointExecutionResult(fleet=updated_fleet, events=[])

    if wp.task.type == "colonise":
        planet = planets_by_coord.get((wp.x, wp.y))
        colonise_result = execute_colonise_task(
            fleet,
            planet,
            designs_by_id,
            planet_name=(
                planet_names_by_id.get(planet.id, planet.id)
                if planet is not None and planet_names_by_id is not None
                else None
            ),
        )
        if colonise_result.planet is not None:
            planets_by_id[colonise_result.planet.id] = colonise_result.planet
            planets_by_coord[(wp.x, wp.y)] = colonise_result.planet
        if colonise_result.dissolve_fleet:
            fleets_by_id.pop(fleet.id, None)
            return WaypointExecutionResult(fleet=None, events=colonise_result.events)
        return WaypointExecutionResult(fleet=colonise_result.fleet, events=colonise_result.events)

    return WaypointExecutionResult(fleet=fleet, events=[])


def _per_ship_mass(design: Design, fleet: Fleet) -> int:
    total_ships = max(sum(entry.count for entry in fleet.composition), 1)
    cargo_mass = (
        fleet.cargo.ironium
        + fleet.cargo.boranium
        + fleet.cargo.germanium
        + ((fleet.cargo.colonists + 99) // 100)
    )
    cargo_mass_per_ship = (cargo_mass + total_ships - 1) // total_ships
    return design.mass + cargo_mass_per_ship


def _fuel_multiplier_x100(race: Race) -> int:
    if LRT.IMPROVED_FUEL_EFFICIENCY in race.lrts:
        return 85
    return 100


def _fuel_for_leg(
    fleet: Fleet,
    designs_by_id: dict[str, Design],
    warp: int,
    distance_light_years: int,
    *,
    fuel_multiplier_x100: int = 100,
) -> int:
    total = 0
    for entry in fleet.composition:
        design = designs_by_id.get(entry.design_id)
        if design is None or entry.count <= 0:
            continue
        ship_mass = _per_ship_mass(design, fleet)
        ship_fuel = (
            (ship_mass * design.fuel_usage[warp - 1] * distance_light_years // 200) + 9
        ) // 10
        ship_fuel = ship_fuel * fuel_multiplier_x100 // 100
        total += ship_fuel * entry.count
    return total


def _effective_warp(
    fleet: Fleet,
    waypoint: Waypoint,
    leg_distance_light_years: int,
    designs_by_id: dict[str, Design],
    *,
    fuel_multiplier_x100: int = 100,
) -> tuple[int, int]:
    requested = waypoint.warp
    if requested is None:
        requested = 1
        for candidate in range(10, 0, -1):
            required_fuel = _fuel_for_leg(
                fleet,
                designs_by_id,
                candidate,
                leg_distance_light_years,
                fuel_multiplier_x100=fuel_multiplier_x100,
            )
            if required_fuel <= fleet.fuel:
                requested = candidate
                break

    actual = requested
    while actual >= 2:
        required_fuel = _fuel_for_leg(
            fleet,
            designs_by_id,
            actual,
            leg_distance_light_years,
            fuel_multiplier_x100=fuel_multiplier_x100,
        )
        if required_fuel <= fleet.fuel:
            break
        actual -= 1
    if actual < 2:
        actual = 1
    return requested, actual


def move_fleet(
    ctx: TurnContext,
    fleet: Fleet,
) -> tuple[Fleet | None, list[GameEvent]]:
    """Move a fleet toward its waypoints for one turn.

    Args:
        fleet: The fleet to move.

    Returns:
        Updated fleet with new position and consumed waypoints.
    """
    if not fleet.waypoints:
        return fleet, []

    # Current position (mutable copy)
    fx = fleet.position.x
    fy = fleet.position.y
    waypoints = list(fleet.waypoints)
    updated_fleet = fleet
    events: list[GameEvent] = []
    remaining_budget: int | None = None
    fuel_multiplier_x100 = _fuel_multiplier_x100(ctx.race_by_username[fleet.owner])

    while waypoints and (remaining_budget is None or remaining_budget > 0):
        wp = waypoints[0]
        dx = wp.x - fx
        dy = wp.y - fy
        dist_sq = dx * dx + dy * dy
        dist = isqrt(dist_sq)

        if dist_sq == 0:
            # Already at waypoint
            log.debug(
                "move: fleet=%s owner=%s at waypoint (%d,%d) task=%s",
                fleet.id,
                fleet.owner,
                fx,
                fy,
                wp.task.type if wp.task else None,
            )
            updated_fleet = updated_fleet.model_copy(update={"position": Position(x=fx, y=fy)})
            task_result = _execute_waypoint_task(
                updated_fleet,
                wp,
                ctx.fleets_by_id,
                ctx.planets_by_coord,
                ctx.planets_by_id,
                ctx.designs_by_id,
                ctx.planet_names,
            )
            events.extend(task_result.events)
            if task_result.fleet is None:
                return None, events
            updated_fleet = task_result.fleet
            consumed_wp = waypoints.pop(0)
            if updated_fleet.repeat:
                waypoints.append(consumed_wp)
            continue

        requested_warp, effective_warp = _effective_warp(
            updated_fleet,
            wp,
            max(dist // LIGHT_YEAR, 0),
            ctx.designs_by_id,
            fuel_multiplier_x100=fuel_multiplier_x100,
        )
        if requested_warp > effective_warp:
            events.append(
                GameEvent(
                    owner=fleet.owner,
                    source_id=fleet.id,
                    code="fleet.fuel_warning",
                    values=[requested_warp, effective_warp],
                )
            )
        leg_budget = effective_warp * effective_warp * LIGHT_YEAR
        budget = leg_budget if remaining_budget is None else min(remaining_budget, leg_budget)

        travel_bearing = compute_bearing(fx, fy, wp.x, wp.y)

        if dist <= budget:
            # Fleet arrives at waypoint
            fx = wp.x
            fy = wp.y
            remaining_budget = budget - dist
            fuel_used = _fuel_for_leg(
                updated_fleet,
                ctx.designs_by_id,
                effective_warp,
                max(dist // LIGHT_YEAR, 0),
                fuel_multiplier_x100=fuel_multiplier_x100,
            )
            log.debug(
                "move: fleet=%s owner=%s arrived at (%d,%d) task=%s",
                fleet.id,
                fleet.owner,
                fx,
                fy,
                wp.task.type if wp.task else None,
            )
            updated_fleet = updated_fleet.model_copy(
                update={
                    "position": Position(x=fx, y=fy),
                    "bearing": travel_bearing,
                    "fuel": max(updated_fleet.fuel - fuel_used, 0),
                }
            )
            task_result = _execute_waypoint_task(
                updated_fleet,
                wp,
                ctx.fleets_by_id,
                ctx.planets_by_coord,
                ctx.planets_by_id,
                ctx.designs_by_id,
                ctx.planet_names,
            )
            events.extend(task_result.events)
            if task_result.fleet is None:
                return None, events
            updated_fleet = task_result.fleet
            planet = ctx.planets_by_coord.get((fx, fy))
            if (
                planet is not None
                and planet.owner == updated_fleet.owner
                and planet.starbase is not None
                and planet.starbase.can_build_ships
            ):
                updated_fleet = updated_fleet.model_copy(
                    update={"fuel": fleet_fuel_capacity(updated_fleet, ctx.designs_by_id)}
                )

            consumed_wp = waypoints.pop(0)
            if updated_fleet.repeat:
                waypoints.append(consumed_wp)
        else:
            # Fleet moves toward waypoint (doesn't reach it)
            new_fx = fx + (dx * budget) // dist
            new_fy = fy + (dy * budget) // dist
            fuel_used = _fuel_for_leg(
                updated_fleet,
                ctx.designs_by_id,
                effective_warp,
                max(budget // LIGHT_YEAR, 0),
                fuel_multiplier_x100=fuel_multiplier_x100,
            )
            log.debug(
                "move: fleet=%s owner=%s moved (%d,%d)->(%d,%d) toward (%d,%d)",
                fleet.id,
                fleet.owner,
                fx,
                fy,
                new_fx,
                new_fy,
                wp.x,
                wp.y,
            )
            fx = new_fx
            fy = new_fy
            updated_fleet = updated_fleet.model_copy(update={"bearing": travel_bearing})
            updated_fleet = updated_fleet.model_copy(
                update={"fuel": max(updated_fleet.fuel - fuel_used, 0)}
            )
            remaining_budget = 0

    return (
        Fleet(
            id=updated_fleet.id,
            name=updated_fleet.name,
            owner=updated_fleet.owner,
            position=Position(x=fx, y=fy),
            composition=updated_fleet.composition,
            cargo=updated_fleet.cargo,
            fuel=updated_fleet.fuel,
            repeat=updated_fleet.repeat,
            waypoints=[Waypoint(x=wp.x, y=wp.y, warp=wp.warp, task=wp.task) for wp in waypoints],
            bearing=updated_fleet.bearing,
        ),
        events,
    )


def move_fleets(ctx: TurnContext) -> None:
    """Move all fleets one turn. Populates ctx.fleets and accumulates ctx.owner_events."""
    moved_fleets = []
    for fid in sorted(list(ctx.fleets_by_id.keys())):
        if fid not in ctx.fleets_by_id:
            continue
        moved, events = move_fleet(
            ctx,
            ctx.fleets_by_id[fid],
        )
        ctx.append_events(events)
        if moved is None:
            continue
        ctx.fleets_by_id[fid] = moved
        moved_fleets.append(moved)
    ctx.fleets = moved_fleets
