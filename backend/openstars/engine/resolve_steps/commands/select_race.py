"""Apply select-race command."""

from openstars.engine.models import SelectRaceCommand
from openstars.engine.race.costs import validate_race
from openstars.engine.race.presets import PREDEFINED_RACES
from openstars.engine.turn_context import TurnContext
from openstars.server.errors import GameError

PREDEFINED_RACE_UNKNOWN = "PREDEFINED_RACE_UNKNOWN"
RACE_REVALIDATION_FAILED = "RACE_REVALIDATION_FAILED"


def apply_select_race_command(ctx: TurnContext, username: str, cmd: SelectRaceCommand) -> None:
    if cmd.predefined_id is not None:
        race = PREDEFINED_RACES.get(cmd.predefined_id)
        if race is None:
            raise GameError(
                400,
                PREDEFINED_RACE_UNKNOWN,
                f"Unknown predefined race: {cmd.predefined_id}",
            )
        selected_race = race.model_copy(deep=True)
    else:
        assert cmd.race is not None
        selected_race = cmd.race.model_copy(deep=True)

    validate_race(selected_race)
    ctx.race_by_username[username] = selected_race
