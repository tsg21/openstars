"""Apply set_research command."""

from openstars.engine.models import RESEARCH_FIELDS, SetResearchCommand
from openstars.engine.turn_context import TurnContext
from openstars.server.errors import GameError


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
