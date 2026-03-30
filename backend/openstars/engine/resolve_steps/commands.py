"""Apply player commands (set_waypoints)."""

from openstars.engine.models import Fleet, Galaxy, PlayerCommands, Position


def apply_commands(
    fleets_by_id: dict[str, Fleet],
    all_commands: dict[str, PlayerCommands],
    max_coord: int,
) -> None:
    """Apply set_waypoints commands in-place on fleets_by_id.

    Processes players alphabetically for determinism.
    """
    for username in sorted(all_commands.keys()):
        for cmd in all_commands[username].commands:
            if cmd.type == "set_waypoints":
                fleet = fleets_by_id.get(cmd.fleet_id)
                if fleet is None:
                    continue
                if fleet.owner != username:
                    continue

                valid_waypoints = [
                    Position(x=wp.x, y=wp.y)
                    for wp in cmd.waypoints
                    if 0 <= wp.x <= max_coord and 0 <= wp.y <= max_coord
                ]

                fleets_by_id[cmd.fleet_id] = Fleet(
                    id=fleet.id,
                    owner=fleet.owner,
                    position=fleet.position,
                    composition=fleet.composition,
                    waypoints=valid_waypoints,
                )


def galaxy_max_coord(galaxy: Galaxy) -> int:
    """Return the maximum coordinate value for a galaxy size."""
    from openstars.engine.galaxy import GALAXY_SIZES

    bits = GALAXY_SIZES.get(galaxy.galaxy.size, 40)
    return (1 << bits) - 1
