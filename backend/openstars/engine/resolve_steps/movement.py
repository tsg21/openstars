"""Fleet movement using integer arithmetic (PRD 07).

1 parsec = 2^29 coordinate units.
All computation is integer-only — no floating point.
"""

import logging

from openstars.engine.galaxy import PARSEC
from openstars.engine.models import Design, Fleet, PlanetState, Position, Waypoint
from openstars.engine.resolve_steps.freight import execute_transfer_task, execute_transport_task
from openstars.engine.util import isqrt

log = logging.getLogger(__name__)


def _execute_waypoint_task(
    fleet: Fleet,
    wp: Waypoint,
    fleets_by_id: dict[str, Fleet],
    planets_by_coord: dict[tuple[int, int], PlanetState],
    planets_by_id: dict[str, PlanetState],
    designs_by_id: dict[str, Design],
) -> Fleet:
    if wp.task is None:
        return fleet

    if wp.task.type == "transport":
        planet = planets_by_coord.get((wp.x, wp.y))
        if planet is None:
            return fleet
        updated_fleet, updated_planet = execute_transport_task(
            fleet,
            planet,
            wp.task,
            designs_by_id,
        )
        planets_by_id[updated_planet.id] = updated_planet
        planets_by_coord[(wp.x, wp.y)] = updated_planet
        return updated_fleet

    if wp.task.type == "transfer" and wp.task.fleet_id is not None:
        target = fleets_by_id.get(wp.task.fleet_id)
        if (
            target is None
            or target.owner != fleet.owner
            or target.position.x != wp.x
            or target.position.y != wp.y
        ):
            return fleet
        updated_fleet, updated_target = execute_transfer_task(fleet, target, wp.task, designs_by_id)
        fleets_by_id[target.id] = updated_target
        return updated_fleet

    return fleet


def move_fleet(
    fleet: Fleet,
    designs_speed: dict[str, int],
    planets_by_coord: dict[tuple[int, int], PlanetState],
    fleets_by_id: dict[str, Fleet],
    designs_by_id: dict[str, Design],
    planets_by_id: dict[str, PlanetState],
) -> Fleet:
    """Move a fleet toward its waypoints for one turn.

    Args:
        fleet: The fleet to move.
        designs_speed: Mapping of design_id → speed in parsecs.

    Returns:
        Updated fleet with new position and consumed waypoints.
    """
    if not fleet.waypoints:
        return fleet

    # Fleet speed = slowest design in composition (parsecs/turn)
    speed = min(designs_speed.get(comp.design_id, 0) for comp in fleet.composition)
    if speed <= 0:
        return fleet

    # Movement budget in coordinate units
    budget = speed * PARSEC

    # Current position (mutable copy)
    fx = fleet.position.x
    fy = fleet.position.y
    waypoints = list(fleet.waypoints)
    updated_fleet = fleet

    while budget > 0 and waypoints:
        wp = waypoints[0]
        dx = wp.x - fx
        dy = wp.y - fy
        dist_sq = dx * dx + dy * dy

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
            updated_fleet = _execute_waypoint_task(
                updated_fleet,
                wp,
                fleets_by_id,
                planets_by_coord,
                planets_by_id,
                designs_by_id,
            )
            consumed_wp = waypoints.pop(0)
            if updated_fleet.repeat:
                waypoints.append(consumed_wp)
            continue

        dist = isqrt(dist_sq)

        if dist <= budget:
            # Fleet arrives at waypoint
            fx = wp.x
            fy = wp.y
            budget -= dist
            log.debug(
                "move: fleet=%s owner=%s arrived at (%d,%d) task=%s",
                fleet.id,
                fleet.owner,
                fx,
                fy,
                wp.task.type if wp.task else None,
            )
            updated_fleet = updated_fleet.model_copy(update={"position": Position(x=fx, y=fy)})
            updated_fleet = _execute_waypoint_task(
                updated_fleet,
                wp,
                fleets_by_id,
                planets_by_coord,
                planets_by_id,
                designs_by_id,
            )

            consumed_wp = waypoints.pop(0)
            if updated_fleet.repeat:
                waypoints.append(consumed_wp)
        else:
            # Fleet moves toward waypoint (doesn't reach it)
            new_fx = fx + (dx * budget) // dist
            new_fy = fy + (dy * budget) // dist
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
            budget = 0

    return Fleet(
        id=updated_fleet.id,
        owner=updated_fleet.owner,
        position=Position(x=fx, y=fy),
        composition=updated_fleet.composition,
        cargo=updated_fleet.cargo,
        repeat=updated_fleet.repeat,
        waypoints=[Waypoint(x=wp.x, y=wp.y, task=wp.task) for wp in waypoints],
    )


def move_fleets(
    fleets_by_id: dict[str, Fleet],
    design_speeds: dict[str, int],
    planets_by_coord: dict[tuple[int, int], PlanetState],
    designs_by_id: dict[str, Design],
    planets_by_id: dict[str, PlanetState],
) -> list[Fleet]:
    """Move all fleets one turn. Returns a list in sorted fleet ID order."""
    moved_fleets = []
    for fid in sorted(fleets_by_id):
        moved = move_fleet(
            fleets_by_id[fid],
            design_speeds,
            planets_by_coord,
            fleets_by_id,
            designs_by_id,
            planets_by_id,
        )
        fleets_by_id[fid] = moved
        moved_fleets.append(moved)
    return moved_fleets
