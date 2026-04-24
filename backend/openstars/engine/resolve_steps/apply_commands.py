"""Apply player commands."""

from collections.abc import Mapping
from typing import Any

from pydantic import TypeAdapter

from openstars.engine.models import (
    AddProductionItemCommand,
    ClearProductionQueueCommand,
    JettisonCargoCommand,
    MergeSplitFleetsCommand,
    MoveProductionItemCommand,
    PlayerCommand,
    PlayerCommands,
    RemoveProductionItemCommand,
    RenameFleetCommand,
    SetPlanetProductionModeCommand,
    SetResearchCommand,
    SetWaypointsCommand,
)
from openstars.engine.resolve_steps.commands.jettison_cargo import apply_jettison_cargo_command
from openstars.engine.resolve_steps.commands.merge_split_fleets import (
    apply_merge_split_fleets_command,
)
from openstars.engine.resolve_steps.commands.production import (
    apply_add_production_item_command,
    apply_clear_production_queue_command,
    apply_move_production_item_command,
    apply_remove_production_item_command,
)
from openstars.engine.resolve_steps.commands.rename_fleet import apply_rename_fleet_command
from openstars.engine.resolve_steps.commands.set_planet_production_mode import (
    apply_set_planet_production_mode_command,
)
from openstars.engine.resolve_steps.commands.set_research import apply_set_research_command
from openstars.engine.resolve_steps.commands.set_waypoints import apply_set_waypoints_command
from openstars.engine.turn_context import TurnContext

_PLAYER_COMMAND_ADAPTER = TypeAdapter(PlayerCommand)


def _replace_tmp_ids(value: Any, replacements: Mapping[str, str]) -> Any:
    if isinstance(value, str):
        return replacements.get(value, value)
    if isinstance(value, list):
        return [_replace_tmp_ids(item, replacements) for item in value]
    if isinstance(value, dict):
        return {key: _replace_tmp_ids(val, replacements) for key, val in value.items()}
    return value


def _rewrite_commands(
    commands: list[PlayerCommand], replacements: Mapping[str, str]
) -> list[PlayerCommand]:
    if not replacements:
        return commands
    rewritten: list[PlayerCommand] = []
    for command in commands:
        payload = command.model_dump(mode="python")
        rewritten_payload = _replace_tmp_ids(payload, replacements)
        rewritten.append(_PLAYER_COMMAND_ADAPTER.validate_python(rewritten_payload))
    return rewritten


def apply_commands(ctx: TurnContext, all_commands: dict[str, PlayerCommands]) -> None:
    """Apply commands in-place. Processes players alphabetically for determinism."""
    for username in sorted(all_commands.keys()):
        command_list = list(all_commands[username].commands)
        index = 0
        while index < len(command_list):
            cmd = command_list[index]
            if isinstance(cmd, SetWaypointsCommand):
                apply_set_waypoints_command(ctx.fleets_by_id, username, cmd, ctx.max_coord)
            elif isinstance(cmd, RenameFleetCommand):
                apply_rename_fleet_command(ctx.fleets_by_id, username, cmd)
            elif isinstance(cmd, AddProductionItemCommand):
                apply_add_production_item_command(ctx.planets_by_id, username, cmd, ctx)
            elif isinstance(cmd, MoveProductionItemCommand):
                apply_move_production_item_command(ctx.planets_by_id, username, cmd)
            elif isinstance(cmd, RemoveProductionItemCommand):
                apply_remove_production_item_command(ctx.planets_by_id, username, cmd)
            elif isinstance(cmd, ClearProductionQueueCommand):
                apply_clear_production_queue_command(ctx.planets_by_id, username, cmd)
            elif isinstance(cmd, JettisonCargoCommand):
                apply_jettison_cargo_command(ctx.fleets_by_id, ctx.planet_coords, username, cmd)
            elif isinstance(cmd, MergeSplitFleetsCommand):
                replacements = apply_merge_split_fleets_command(ctx, username, cmd)
                if replacements:
                    remaining = command_list[index + 1 :]
                    command_list[index + 1 :] = _rewrite_commands(remaining, replacements)
            elif isinstance(cmd, SetResearchCommand):
                apply_set_research_command(ctx, username, cmd)
            elif isinstance(cmd, SetPlanetProductionModeCommand):
                apply_set_planet_production_mode_command(ctx, username, cmd)
            index += 1
