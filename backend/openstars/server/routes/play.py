"""Player gameplay endpoints (PRD 09)."""

import logging

from fastapi import APIRouter, Depends, Header
from fastapi.responses import JSONResponse

from openstars.engine.galaxy import GALAXY_SIZES
from openstars.engine.models import PlayerCommands
from openstars.engine.resolve_steps.commands.parsing import (
    CommandParseContext,
    parse_registered_command,
)
from openstars.game_directory.base import GameDirectory, GameNotFoundError
from openstars.server.deps import get_game_directory, get_storage
from openstars.server.errors import GameError, error_response
from openstars.server.log_context import game_id as game_id_log_context
from openstars.server.resolution import resolve_current_turn
from openstars.server.schemas import (
    SubmitCommandsRequest,
    SubmitCommandsResponse,
    TurnStatusResponse,
)
from openstars.server.turns import get_current_turn, player_submitted
from openstars.storage.base import GameStorage

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/games/{game_id}", tags=["play"])


def _validate_player(directory: GameDirectory, game_id: str, username: str):
    """Check game exists and player is a participant. Returns (summary, error_response)."""
    try:
        summary = directory.get_game(game_id)
    except GameNotFoundError:
        return None, error_response(404, "GAME_NOT_FOUND", f"Game {game_id!r} not found")

    if username not in summary.players:
        return None, error_response(
            403, "NOT_PARTICIPANT", "You are not a participant in this game"
        )

    return summary, None


@router.get("/turn-status")
async def get_turn_status(
    game_id: str,
    storage: GameStorage = Depends(get_storage),
    directory: GameDirectory = Depends(get_game_directory),
    x_player: str = Header(...),
) -> TurnStatusResponse:
    """Get the current turn number and the list of players still to submit."""
    summary, err = _validate_player(directory, game_id, x_player)
    if err:
        return err

    current_turn = get_current_turn(summary)
    awaiting = [
        p for p in summary.players if not player_submitted(storage, game_id, p, current_turn)
    ]
    return TurnStatusResponse(turn=current_turn, players_awaiting_submission=awaiting)


@router.get("/galaxy")
async def get_galaxy(
    game_id: str,
    storage: GameStorage = Depends(get_storage),
    directory: GameDirectory = Depends(get_game_directory),
    x_player: str = Header(...),
):
    """Get the static galaxy definition."""
    _, err = _validate_player(directory, game_id, x_player)
    if err:
        return err

    try:
        galaxy = storage.load_galaxy(game_id)
    except FileNotFoundError:
        return error_response(404, "GAME_NOT_FOUND", "Galaxy data not found")

    return galaxy.model_dump()


@router.get("/state")
async def get_state(
    game_id: str,
    turn: int | None = None,
    storage: GameStorage = Depends(get_storage),
    directory: GameDirectory = Depends(get_game_directory),
    x_player: str = Header(...),
):
    """Get the player's state for a given turn (default: current)."""
    summary, err = _validate_player(directory, game_id, x_player)
    if err:
        return err

    if turn is None:
        turn = get_current_turn(summary)

    try:
        ps = storage.load_player_state(game_id, x_player, turn)
    except FileNotFoundError:
        return error_response(404, "TURN_NOT_FOUND", f"State for turn {turn} not found")

    return ps.model_dump()


@router.post("/commands")
async def submit_commands(
    game_id: str,
    req: SubmitCommandsRequest,
    storage: GameStorage = Depends(get_storage),
    directory: GameDirectory = Depends(get_game_directory),
    x_player: str = Header(...),
):
    """Submit commands for the current turn. Auto-resolves if this is the last submission."""
    summary, err = _validate_player(directory, game_id, x_player)
    if err:
        return err

    current_turn = get_current_turn(summary)
    if req.turn != current_turn:
        return error_response(
            409,
            "TURN_MISMATCH",
            f"Submitted turn {req.turn} but current turn is {current_turn}",
        )

    # Phase enforcement (PRD 22): T=0 accepts only select_race; T>=1 rejects select_race.
    for cmd_dict in req.commands:
        cmd_type = cmd_dict.get("type") if isinstance(cmd_dict, dict) else None
        if current_turn == 0 and cmd_type != "select_race":
            return error_response(
                400,
                "COMMAND_TURN_ZERO_RACE_ONLY",
                f"At turn 0 only select_race commands are allowed; got {cmd_type!r}",
            )
        if current_turn >= 1 and cmd_type == "select_race":
            return error_response(
                400,
                "COMMAND_NOT_VALID_AT_THIS_TURN",
                f"select_race is only valid at turn 0; current turn is {current_turn}",
            )

    try:
        global_state = storage.load_global_state(game_id, current_turn)
    except FileNotFoundError:
        return error_response(404, "GAME_NOT_FOUND", "Game state not found")

    galaxy = storage.load_galaxy(game_id)
    max_coord = (1 << GALAXY_SIZES.get(galaxy.galaxy.size, 40)) - 1

    owned_fleets = {f.id for f in global_state.fleets if f.owner == x_player}
    owned_planets = {p.id: p for p in global_state.planets if p.owner == x_player}
    queue_state_by_planet = {
        planet_id: [item.model_copy(deep=True) for item in planet.production_queue]
        for planet_id, planet in owned_planets.items()
    }
    parse_ctx = CommandParseContext(
        username=x_player,
        owned_fleet_ids=owned_fleets,
        declared_tmp_fleet_ids=set(),
        max_coord=max_coord,
        owned_planets=owned_planets,
        queue_state_by_planet=queue_state_by_planet,
        player_design_ids={design.id for design in storage.list_designs(game_id, x_player)},
    )

    parsed_commands = []
    for cmd_dict in req.commands:
        try:
            parsed_command = parse_registered_command(cmd_dict, parse_ctx)
        except GameError as exc:
            return error_response(exc.status_code, exc.error_code, exc.error_message)
        parsed_commands.append(parsed_command)

    player_commands = PlayerCommands(commands=parsed_commands)
    storage.save_commands(game_id, x_player, current_turn, player_commands)

    # Compute which players have now submitted.
    players_submitted_list = [
        p for p in summary.players if player_submitted(storage, game_id, p, current_turn)
    ]
    directory.player_submitted(game_id, players_submitted_list)

    # Auto-resolve if all players have submitted.
    if set(players_submitted_list) >= set(summary.players):
        token = game_id_log_context.set(game_id)
        try:
            outcome = resolve_current_turn(storage, directory, game_id, summary)
        except Exception as exc:
            log.error("resolution.failed error=%s", exc)
            return JSONResponse(
                status_code=500,
                content={"error": {"code": "RESOLUTION_FAILED", "message": str(exc)}},
            )
        finally:
            game_id_log_context.reset(token)

        return SubmitCommandsResponse(
            turn=current_turn,
            command_count=len(parsed_commands),
            turn_resolved=True,
            new_turn=outcome.new_turn,
        )

    return SubmitCommandsResponse(
        turn=current_turn,
        command_count=len(parsed_commands),
        turn_resolved=False,
        new_turn=None,
    )


@router.get("/commands")
async def get_commands(
    game_id: str,
    storage: GameStorage = Depends(get_storage),
    directory: GameDirectory = Depends(get_game_directory),
    x_player: str = Header(...),
):
    """Get the player's submitted commands for the current turn."""
    summary, err = _validate_player(directory, game_id, x_player)
    if err:
        return err

    current_turn = get_current_turn(summary)

    try:
        cmds = storage.load_commands(game_id, x_player, current_turn)
    except FileNotFoundError:
        return {"turn": current_turn, "commands": []}

    return {"turn": current_turn, "commands": [c.model_dump() for c in cmds.commands]}
