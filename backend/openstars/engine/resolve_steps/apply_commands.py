"""Apply player commands."""

from openstars.engine.models import (
    AddProductionItemCommand,
    ClearProductionQueueCommand,
    Fleet,
    Galaxy,
    JettisonCargoCommand,
    MoveProductionItemCommand,
    PlanetState,
    PlayerCommands,
    RemoveProductionItemCommand,
    RenameFleetCommand,
    SetWaypointsCommand,
)
from openstars.engine.resolve_steps.commands.jettison_cargo import apply_jettison_cargo_command
from openstars.engine.resolve_steps.commands.production import (
    apply_add_production_item_command,
    apply_clear_production_queue_command,
    apply_move_production_item_command,
    apply_remove_production_item_command,
)
from openstars.engine.resolve_steps.commands.rename_fleet import apply_rename_fleet_command
from openstars.engine.resolve_steps.commands.set_waypoints import apply_set_waypoints_command


def apply_commands(
    fleets_by_id: dict[str, Fleet],
    planets_by_id: dict[str, PlanetState],
    planet_coords: set[tuple[int, int]],
    all_commands: dict[str, PlayerCommands],
    max_coord: int,
    game_seed: int,
    next_id: int,
) -> int:
    """Apply commands in-place and return the updated next-id counter.

    Processes players alphabetically for determinism.
    """
    for username in sorted(all_commands.keys()):
        for cmd in all_commands[username].commands:
            if isinstance(cmd, SetWaypointsCommand):
                apply_set_waypoints_command(fleets_by_id, username, cmd, max_coord)
            elif isinstance(cmd, RenameFleetCommand):
                apply_rename_fleet_command(fleets_by_id, username, cmd)
            elif isinstance(cmd, AddProductionItemCommand):
                next_id = apply_add_production_item_command(
                    planets_by_id=planets_by_id,
                    username=username,
                    cmd=cmd,
                    game_seed=game_seed,
                    next_id=next_id,
                )
            elif isinstance(cmd, MoveProductionItemCommand):
                apply_move_production_item_command(planets_by_id, username, cmd)
            elif isinstance(cmd, RemoveProductionItemCommand):
                apply_remove_production_item_command(planets_by_id, username, cmd)
            elif isinstance(cmd, ClearProductionQueueCommand):
                apply_clear_production_queue_command(planets_by_id, username, cmd)
            elif isinstance(cmd, JettisonCargoCommand):
                apply_jettison_cargo_command(fleets_by_id, planet_coords, username, cmd)

    return next_id


def galaxy_max_coord(galaxy: Galaxy) -> int:
    """Return the maximum coordinate value for a galaxy size."""
    from openstars.engine.galaxy import GALAXY_SIZES

    bits = GALAXY_SIZES.get(galaxy.galaxy.size, 40)
    return (1 << bits) - 1
