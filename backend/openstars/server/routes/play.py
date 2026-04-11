"""Player gameplay endpoints (PRD 09)."""

from fastapi import APIRouter, Depends, Header

from openstars.engine.fog import derive_player_state
from openstars.engine.models import (
    PlayerCommands,
)
from openstars.engine.resolve import resolve_turn
from openstars.engine.resolve_steps.commands.jettison_cargo import parse_jettison_cargo_command
from openstars.engine.resolve_steps.commands.merge_split_fleets import (
    parse_merge_split_fleets_command,
)
from openstars.engine.resolve_steps.commands.production import parse_production_command
from openstars.engine.resolve_steps.commands.rename_fleet import parse_rename_fleet_command
from openstars.engine.resolve_steps.commands.set_waypoints import parse_set_waypoints_command
from openstars.server.deps import get_storage
from openstars.server.errors import GameError, error_response
from openstars.server.game_designs import list_all_designs_for_players
from openstars.server.log_context import game_id as game_id_log_context
from openstars.server.schemas import (
    ResolveResponse,
    SubmitCommandsRequest,
    SubmitCommandsResponse,
    TurnStatusResponse,
)
from openstars.server.turns import get_current_turn
from openstars.storage.base import GameStorage

router = APIRouter(prefix="/api/v1/games/{game_id}", tags=["play"])


def _validate_player(storage: GameStorage, game_id: str, username: str):
    """Check game exists and player is a participant. Returns (meta, error_response)."""
    try:
        meta = storage.load_game_meta(game_id)
    except FileNotFoundError:
        return None, error_response(404, "GAME_NOT_FOUND", f"Game {game_id!r} not found")

    if username not in meta.get("players", []):
        return None, error_response(
            403, "NOT_PARTICIPANT", "You are not a participant in this game"
        )

    return meta, None


@router.get("/turn-status")
async def get_turn_status(
    game_id: str,
    storage: GameStorage = Depends(get_storage),
    x_player: str = Header(...),
):
    """Get the current turn number using lightweight metadata."""
    meta, err = _validate_player(storage, game_id, x_player)
    if err:
        return err

    return TurnStatusResponse(turn=get_current_turn(storage, game_id, meta))


@router.get("/galaxy")
async def get_galaxy(
    game_id: str,
    storage: GameStorage = Depends(get_storage),
    x_player: str = Header(...),
):
    """Get the static galaxy definition."""
    meta, err = _validate_player(storage, game_id, x_player)
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
    x_player: str = Header(...),
):
    """Get the player's state for a given turn (default: current)."""
    meta, err = _validate_player(storage, game_id, x_player)
    if err:
        return err

    if turn is None:
        turn = get_current_turn(storage, game_id, meta)

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
    x_player: str = Header(...),
):
    """Submit commands for the current turn."""
    meta, err = _validate_player(storage, game_id, x_player)
    if err:
        return err

    current_turn = get_current_turn(storage, game_id, meta)
    if req.turn != current_turn:
        return error_response(
            409,
            "TURN_MISMATCH",
            f"Submitted turn {req.turn} but current turn is {current_turn}",
        )

    # Parse and validate commands
    try:
        global_state = storage.load_global_state(game_id, current_turn)
    except FileNotFoundError:
        return error_response(404, "GAME_NOT_FOUND", "Game state not found")

    # Load galaxy for bounds checking
    galaxy = storage.load_galaxy(game_id)
    from openstars.engine.galaxy import GALAXY_SIZES

    max_coord = (1 << GALAXY_SIZES.get(galaxy.galaxy.size, 40)) - 1

    # Build owned entity lookups for command validation.
    owned_fleets = {f.id for f in global_state.fleets if f.owner == x_player}
    owned_planets = {p.id: p for p in global_state.planets if p.owner == x_player}
    queue_state_by_planet = {
        planet_id: [item.model_copy(deep=True) for item in planet.production_queue]
        for planet_id, planet in owned_planets.items()
    }
    declared_tmp_fleet_ids: set[str] = set()
    player_design_ids = {design.id for design in storage.list_designs(game_id, x_player)}

    parsed_commands = []
    for cmd_dict in req.commands:
        cmd_type = cmd_dict.get("type")
        try:
            if cmd_type == "set_waypoints":
                parsed_command = parse_set_waypoints_command(
                    cmd_dict,
                    x_player,
                    owned_fleets,
                    declared_tmp_fleet_ids,
                    max_coord,
                )
            elif cmd_type == "jettison_cargo":
                parsed_command = parse_jettison_cargo_command(
                    cmd_dict,
                    x_player,
                    owned_fleets,
                    declared_tmp_fleet_ids,
                )
            elif cmd_type == "rename_fleet":
                parsed_command = parse_rename_fleet_command(
                    cmd_dict,
                    x_player,
                    owned_fleets,
                    declared_tmp_fleet_ids,
                )
            elif cmd_type == "merge_split_fleets":
                parsed_command, new_tmp_ids = parse_merge_split_fleets_command(
                    cmd_dict,
                    x_player,
                    owned_fleets,
                    declared_tmp_fleet_ids,
                )
                declared_tmp_fleet_ids.update(new_tmp_ids)
            else:
                parsed_command = parse_production_command(
                    cmd_dict,
                    x_player,
                    owned_planets,
                    queue_state_by_planet,
                    player_design_ids,
                )
        except GameError as exc:
            return error_response(exc.status_code, exc.error_code, exc.error_message)

        parsed_commands.append(parsed_command)

    player_commands = PlayerCommands(commands=parsed_commands)
    storage.save_commands(game_id, x_player, current_turn, player_commands)

    return SubmitCommandsResponse(
        turn=current_turn,
        command_count=len(parsed_commands),
    )


@router.get("/commands")
async def get_commands(
    game_id: str,
    storage: GameStorage = Depends(get_storage),
    x_player: str = Header(...),
):
    """Get the player's submitted commands for the current turn."""
    meta, err = _validate_player(storage, game_id, x_player)
    if err:
        return err

    current_turn = get_current_turn(storage, game_id, meta)

    try:
        cmds = storage.load_commands(game_id, x_player, current_turn)
    except FileNotFoundError:
        return {"turn": current_turn, "commands": []}

    return {"turn": current_turn, "commands": [c.model_dump() for c in cmds.commands]}


@router.post("/resolve")
async def resolve(
    game_id: str,
    storage: GameStorage = Depends(get_storage),
    x_player: str = Header(...),
):
    token = game_id_log_context.set(game_id)
    try:
        """Trigger turn resolution."""
        meta, err = _validate_player(storage, game_id, x_player)
        if err:
            return err

        current_turn = get_current_turn(storage, game_id, meta)
        players = meta.get("players", [])

        # Check all players have submitted
        for p in players:
            if not storage.has_commands(game_id, p, current_turn):
                return error_response(
                    409,
                    "NOT_ALL_SUBMITTED",
                    f"Not all players have submitted commands (waiting for: {p})",
                )

        # Load current state and all commands
        global_state = storage.load_global_state(game_id, current_turn)
        galaxy = storage.load_galaxy(game_id)
        designs = list_all_designs_for_players(storage, game_id, players)

        all_commands = {}
        for p in players:
            all_commands[p] = storage.load_commands(game_id, p, current_turn)

        # Resolve
        new_state = resolve_turn(global_state, galaxy, all_commands, designs)
        new_turn = new_state.game.turn

        # Save new state. If another resolver already persisted this turn,
        # treat it as an expected race and return success idempotently.
        try:
            storage.save_global_state(game_id, new_turn, new_state)
        except FileExistsError:
            current_meta = storage.load_game_meta(game_id)
            if int(current_meta.get("current_turn", 0)) < new_turn:
                current_meta["current_turn"] = new_turn
                storage.save_game_meta(game_id, current_meta)
            return ResolveResponse(turn=new_turn)

        # Derive and save player states
        for p in players:
            ps = derive_player_state(new_state, galaxy, p, designs)
            storage.save_player_state(game_id, p, new_turn, ps)

        meta["current_turn"] = new_turn
        storage.save_game_meta(game_id, meta)

        return ResolveResponse(turn=new_turn)
    finally:
        game_id_log_context.reset(token)
