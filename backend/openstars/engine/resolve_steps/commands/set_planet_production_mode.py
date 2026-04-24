"""Apply set_planet_production_mode command."""

from openstars.engine.models import SetPlanetProductionModeCommand
from openstars.engine.turn_context import TurnContext
from openstars.server.errors import GameError


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
