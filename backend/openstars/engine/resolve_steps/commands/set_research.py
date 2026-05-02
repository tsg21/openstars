"""Apply set_research command."""

from typing import Any

from openstars.engine.models import RESEARCH_FIELDS, SetResearchCommand
from openstars.engine.resolve_steps.commands.parsing import (
    CommandParseContext,
    register_command_parser,
)
from openstars.engine.turn_context import TurnContext
from openstars.server.errors import GameError


def parse_set_research_command(
    cmd_dict: dict[str, Any],
    ctx: CommandParseContext,
) -> SetResearchCommand:
    del ctx
    current_field = cmd_dict.get("current_field")
    next_field = cmd_dict.get("next_field")
    allocation_percent = cmd_dict.get("allocation_percent")
    if current_field is not None and current_field not in RESEARCH_FIELDS:
        raise GameError(400, "RESEARCH_FIELD_UNKNOWN", "Unknown research field")
    if next_field is not None and next_field not in RESEARCH_FIELDS:
        raise GameError(400, "RESEARCH_FIELD_UNKNOWN", "Unknown research field")
    if allocation_percent is not None and (
        not isinstance(allocation_percent, int)
        or allocation_percent < 0
        or allocation_percent > 100
    ):
        raise GameError(
            400,
            "RESEARCH_ALLOCATION_OUT_OF_RANGE",
            "allocation_percent must be in range 0..100",
        )

    payload: dict[str, Any] = {"type": "set_research"}
    if "current_field" in cmd_dict:
        payload["current_field"] = current_field
    if "next_field" in cmd_dict:
        payload["next_field"] = None if next_field is None else next_field
    if "allocation_percent" in cmd_dict:
        payload["allocation_percent"] = allocation_percent
    return SetResearchCommand.model_validate(payload)


register_command_parser("set_research", parse_set_research_command)


def apply_set_research_command(ctx: TurnContext, username: str, cmd: SetResearchCommand) -> None:
    if username not in ctx.research_state_by_username:
        raise GameError(400, "PLAYER_NOT_FOUND", f"Player {username} not found")

    state = ctx.research_state_by_username[username]
    if cmd.current_field is not None:
        if cmd.current_field not in RESEARCH_FIELDS:
            raise GameError(400, "RESEARCH_FIELD_UNKNOWN", "Unknown research field")
        state.current_field = cmd.current_field
    if cmd.next_field is not None:
        if cmd.next_field not in RESEARCH_FIELDS:
            raise GameError(400, "RESEARCH_FIELD_UNKNOWN", "Unknown research field")
        state.next_field = cmd.next_field
    elif "next_field" in cmd.model_fields_set:
        state.next_field = None

    if cmd.allocation_percent is not None:
        if cmd.allocation_percent < 0 or cmd.allocation_percent > 100:
            raise GameError(
                400,
                "RESEARCH_ALLOCATION_OUT_OF_RANGE",
                "allocation_percent must be 0..100",
            )
        state.allocation_percent = cmd.allocation_percent

    if state.current_field == state.next_field:
        state.next_field = None

    ctx.research_state_by_username[username] = state
