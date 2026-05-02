"""Apply select-race command."""

from typing import Any

from openstars.engine.models import SelectRaceCommand
from openstars.engine.race.costs import RaceValidationError, validate_race
from openstars.engine.race.presets import PREDEFINED_RACES
from openstars.engine.resolve_steps.commands.parsing import (
    CommandParseContext,
    register_command_parser,
)
from openstars.engine.turn_context import TurnContext
from openstars.server.errors import GameError

PREDEFINED_RACE_UNKNOWN = "PREDEFINED_RACE_UNKNOWN"
RACE_REVALIDATION_FAILED = "RACE_REVALIDATION_FAILED"


def parse_select_race_command(
    cmd_dict: dict[str, Any],
    ctx: CommandParseContext,
) -> SelectRaceCommand:
    del ctx
    try:
        cmd = SelectRaceCommand.model_validate(cmd_dict)
    except ValueError as exc:
        raise GameError(400, "INVALID_SELECT_RACE", str(exc)) from exc

    if cmd.predefined_id is not None:
        if cmd.predefined_id not in PREDEFINED_RACES:
            raise GameError(
                400,
                PREDEFINED_RACE_UNKNOWN,
                f"Unknown predefined race: {cmd.predefined_id}",
            )
        return cmd

    assert cmd.race is not None
    try:
        validate_race(cmd.race)
    except RaceValidationError as exc:
        raise GameError(400, exc.code, exc.detail) from exc
    return cmd


register_command_parser("select_race", parse_select_race_command)


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
