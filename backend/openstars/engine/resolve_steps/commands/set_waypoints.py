"""Apply set-waypoints command."""

import logging

from openstars.engine.models import Fleet, SetWaypointsCommand, Waypoint

log = logging.getLogger(__name__)


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
