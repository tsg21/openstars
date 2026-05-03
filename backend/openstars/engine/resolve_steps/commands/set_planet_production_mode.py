"""Apply set_planet_production_mode command."""

from typing import Any

from openstars.engine.models import SetPlanetProductionModeCommand
from openstars.engine.resolve_steps.commands.parsing import (
    CommandParseContext,
    register_command_parser,
)
from openstars.engine.turn_context import TurnContext
from openstars.server.errors import GameError


def parse_set_planet_production_mode_command(
    cmd_dict: dict[str, Any],
    ctx: CommandParseContext,
) -> SetPlanetProductionModeCommand:
    planet_id = cmd_dict.get("planet_id")
    if not isinstance(planet_id, str) or not planet_id:
        raise GameError(400, "MISSING_PLANET_ID", "Command missing planet_id")
    if planet_id not in ctx.owned_planets:
        raise GameError(
            400,
            "PLANET_NOT_OWNED",
            f"Planet {planet_id} is not owned by player {ctx.username}",
        )
    return SetPlanetProductionModeCommand(
        planet_id=planet_id,
        contribute_only_leftover_to_research=bool(
            cmd_dict.get("contribute_only_leftover_to_research", False)
        ),
    )


register_command_parser("set_planet_production_mode", parse_set_planet_production_mode_command)


def apply_set_planet_production_mode_command(
    ctx: TurnContext,
    username: str,
    cmd: SetPlanetProductionModeCommand,
) -> None:
    planet = ctx.planets_by_id.get(cmd.planet_id)
    if planet is None or planet.owner != username:
        raise GameError(
            400,
            "PLANET_NOT_OWNED",
            f"Planet {cmd.planet_id} is not owned by player {username}",
        )
    planet.contribute_only_leftover_to_research = cmd.contribute_only_leftover_to_research
