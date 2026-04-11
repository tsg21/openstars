"""Apply set-waypoints command."""

import logging
from typing import Any

from openstars.engine.models import Fleet, SetWaypointsCommand, Waypoint
from openstars.server.errors import GameError

log = logging.getLogger(__name__)


def parse_set_waypoints_command(
    cmd_dict: dict[str, Any],
    username: str,
    owned_fleet_ids: set[str],
    declared_tmp_fleet_ids: set[str],
    max_coord: int,
) -> SetWaypointsCommand:
    fleet_id = cmd_dict.get("fleet_id")
    if not fleet_id:
        raise GameError(400, "MISSING_FLEET_ID", "Command missing fleet_id")
    if fleet_id not in owned_fleet_ids and fleet_id not in declared_tmp_fleet_ids:
        raise GameError(
            400,
            "FLEET_NOT_OWNED",
            f"Fleet {fleet_id} is not owned by player {username}",
        )

    waypoints_raw = cmd_dict.get("waypoints", [])
    waypoints = []
    for wp in waypoints_raw:
        if not isinstance(wp, dict) or "x" not in wp or "y" not in wp:
            raise GameError(400, "INVALID_WAYPOINT", "Waypoints must have x and y")
        wx, wy = wp["x"], wp["y"]
        if not isinstance(wx, int) or not isinstance(wy, int):
            raise GameError(400, "INVALID_WAYPOINT", "Waypoint coordinates must be integers")
        if not (0 <= wx <= max_coord and 0 <= wy <= max_coord):
            raise GameError(
                400,
                "WAYPOINT_OUT_OF_BOUNDS",
                f"Waypoint ({wx}, {wy}) is outside galaxy bounds (0-{max_coord})",
            )
        waypoints.append(Waypoint.model_validate(wp))

    return SetWaypointsCommand(fleet_id=fleet_id, waypoints=waypoints)


def apply_set_waypoints_command(
    fleets_by_id: dict[str, Fleet],
    username: str,
    cmd: SetWaypointsCommand,
    max_coord: int,
) -> None:
    fleet = fleets_by_id.get(cmd.fleet_id)
    if fleet is None or fleet.owner != username:
        return

    valid_waypoints = [
        Waypoint(x=wp.x, y=wp.y, warp=wp.warp, task=wp.task)
        for wp in cmd.waypoints
        if 0 <= wp.x <= max_coord and 0 <= wp.y <= max_coord
    ]

    wp_summary = [(wp.x, wp.y, wp.task.type if wp.task else None) for wp in valid_waypoints]
    log.debug(
        "cmd set_waypoints: fleet=%s owner=%s waypoints=%s", cmd.fleet_id, username, wp_summary
    )

    fleets_by_id[cmd.fleet_id] = Fleet(
        id=fleet.id,
        name=fleet.name,
        owner=fleet.owner,
        position=fleet.position,
        composition=fleet.composition,
        cargo=fleet.cargo,
        fuel=fleet.fuel,
        repeat=fleet.repeat if cmd.repeat is None else cmd.repeat,
        waypoints=valid_waypoints,
        bearing=fleet.bearing,
    )
