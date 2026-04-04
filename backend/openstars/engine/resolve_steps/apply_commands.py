"""Apply player commands."""

from openstars.engine.models import (
    AddProductionItemCommand,
    ClearProductionQueueCommand,
    JettisonCargoCommand,
    MoveProductionItemCommand,
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
from openstars.engine.turn_context import TurnContext


def apply_commands(ctx: TurnContext, all_commands: dict[str, PlayerCommands]) -> None:
    """Apply commands in-place. Processes players alphabetically for determinism."""
    for username in sorted(all_commands.keys()):
        for cmd in all_commands[username].commands:
            if isinstance(cmd, SetWaypointsCommand):
                apply_set_waypoints_command(ctx.fleets_by_id, username, cmd, ctx.max_coord)
            elif isinstance(cmd, RenameFleetCommand):
                apply_rename_fleet_command(ctx.fleets_by_id, username, cmd)
            elif isinstance(cmd, AddProductionItemCommand):
                ctx.next_id = apply_add_production_item_command(
                    planets_by_id=ctx.planets_by_id,
                    username=username,
                    cmd=cmd,
                    game_seed=ctx.global_state.game.seed,
                    next_id=ctx.next_id,
                )
            elif isinstance(cmd, MoveProductionItemCommand):
                apply_move_production_item_command(ctx.planets_by_id, username, cmd)
            elif isinstance(cmd, RemoveProductionItemCommand):
                apply_remove_production_item_command(ctx.planets_by_id, username, cmd)
            elif isinstance(cmd, ClearProductionQueueCommand):
                apply_clear_production_queue_command(ctx.planets_by_id, username, cmd)
            elif isinstance(cmd, JettisonCargoCommand):
                apply_jettison_cargo_command(ctx.fleets_by_id, ctx.planet_coords, username, cmd)
