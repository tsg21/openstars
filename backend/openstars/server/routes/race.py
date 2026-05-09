"""Race design endpoints."""

from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel

from openstars.engine.models import SelectRaceCommand
from openstars.engine.race.costs import race_cost_breakdown
from openstars.engine.race.models import Race
from openstars.engine.race.presets import PREDEFINED_RACES
from openstars.server.deps import get_storage
from openstars.server.errors import error_response
from openstars.server.turns import get_current_turn
from openstars.storage.base import GameStorage

router = APIRouter(prefix="/api/v1", tags=["race"])


class RacePreviewRequest(BaseModel):
    race: Race


def _race_from_select_command(command: SelectRaceCommand) -> Race:
    if command.predefined_id is not None:
        return PREDEFINED_RACES[command.predefined_id].model_copy(deep=True)
    assert command.race is not None
    return command.race.model_copy(deep=True)


def _last_saved_race_selection(
    storage: GameStorage, game_id: str, username: str, turn: int
) -> Race | None:
    try:
        commands = storage.load_commands(game_id, username, turn)
    except FileNotFoundError:
        return None

    selected_race = None
    for command in commands.commands:
        if isinstance(command, SelectRaceCommand):
            selected_race = _race_from_select_command(command)
    return selected_race


@router.post("/race/preview")
async def preview_race(req: RacePreviewRequest, x_player: str = Header(...)):
    """Return the cost breakdown for a draft custom race."""
    del x_player
    breakdown = race_cost_breakdown(req.race)
    return breakdown


@router.get("/games/{game_id}/race")
async def get_game_race(
    game_id: str,
    storage: GameStorage = Depends(get_storage),
    x_player: str = Header(...),
):
    """Return the caller's saved race selection for this game."""
    try:
        meta = storage.load_game_meta(game_id)
    except FileNotFoundError:
        return error_response(404, "GAME_NOT_FOUND", f"Game {game_id!r} not found")

    if x_player not in meta.get("players", []):
        return error_response(403, "NOT_PLAYER", "You are not a player in this game")

    current_turn = get_current_turn(storage, game_id, meta)
    if current_turn == 0:
        race = _last_saved_race_selection(storage, game_id, x_player, current_turn)
    else:
        try:
            global_state = storage.load_global_state(game_id, current_turn)
        except FileNotFoundError:
            return error_response(404, "TURN_NOT_FOUND", f"State for turn {current_turn} not found")
        player = next(
            (player for player in global_state.players if player.username == x_player),
            None,
        )
        race = player.race if player is not None else None

    if race is None:
        return {"race": None, "cost_breakdown": None}

    return {
        "race": race.model_dump(mode="json"),
        "cost_breakdown": race_cost_breakdown(race).model_dump(),
    }


@router.get("/race/predefined")
async def list_predefined_races():
    """Return the static predefined race records."""
    return [
        {"id": race_id, "race": race.model_dump(mode="json")}
        for race_id, race in PREDEFINED_RACES.items()
    ]
