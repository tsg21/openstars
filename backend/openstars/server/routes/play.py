"""Player gameplay endpoints (PRD 09)."""

from fastapi import APIRouter, Depends, Header

from openstars.engine.fog import derive_player_state
from openstars.engine.models import (
    PlayerCommands,
    Position,
    SetWaypointsCommand,
)
from openstars.engine.resolve import resolve_turn
from openstars.server.deps import get_storage
from openstars.server.errors import error_response
from openstars.server.schemas import (
    ResolveResponse,
    SubmitCommandsRequest,
    SubmitCommandsResponse,
)
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


def _current_turn(storage: GameStorage, game_id: str) -> int:
    """Find the current turn."""
    turn = 0
    while True:
        try:
            storage.load_global_state(game_id, turn + 1)
            turn += 1
        except FileNotFoundError:
            break
    return turn


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
        turn = _current_turn(storage, game_id)

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

    current_turn = _current_turn(storage, game_id)
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

    # Build set of fleet IDs owned by this player
    owned_fleets = {f.id for f in global_state.fleets if f.owner == x_player}

    parsed_commands = []
    for cmd_dict in req.commands:
        cmd_type = cmd_dict.get("type")
        if cmd_type != "set_waypoints":
            return error_response(400, "UNKNOWN_COMMAND", f"Unknown command type: {cmd_type}")

        fleet_id = cmd_dict.get("fleet_id")
        if not fleet_id:
            return error_response(400, "MISSING_FLEET_ID", "Command missing fleet_id")
        if fleet_id not in owned_fleets:
            return error_response(
                400,
                "FLEET_NOT_OWNED",
                f"Fleet {fleet_id} is not owned by player {x_player}",
            )

        waypoints_raw = cmd_dict.get("waypoints", [])
        waypoints = []
        for wp in waypoints_raw:
            if not isinstance(wp, dict) or "x" not in wp or "y" not in wp:
                return error_response(400, "INVALID_WAYPOINT", "Waypoints must have x and y")
            wx, wy = wp["x"], wp["y"]
            if not isinstance(wx, int) or not isinstance(wy, int):
                return error_response(
                    400,
                    "INVALID_WAYPOINT",
                    "Waypoint coordinates must be integers",
                )
            if not (0 <= wx <= max_coord and 0 <= wy <= max_coord):
                return error_response(
                    400,
                    "WAYPOINT_OUT_OF_BOUNDS",
                    f"Waypoint ({wx}, {wy}) is outside galaxy bounds (0-{max_coord})",
                )
            waypoints.append(Position(x=wx, y=wy))

        parsed_commands.append(SetWaypointsCommand(fleet_id=fleet_id, waypoints=waypoints))

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

    current_turn = _current_turn(storage, game_id)

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
    """Trigger turn resolution."""
    meta, err = _validate_player(storage, game_id, x_player)
    if err:
        return err

    current_turn = _current_turn(storage, game_id)
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

    all_commands = {}
    for p in players:
        all_commands[p] = storage.load_commands(game_id, p, current_turn)

    # Resolve
    new_state = resolve_turn(global_state, galaxy, all_commands)
    new_turn = new_state.game.turn

    # Save new state. If another resolver already persisted this turn,
    # treat it as an expected race and return success idempotently.
    try:
        storage.save_global_state(game_id, new_turn, new_state)
    except FileExistsError:
        return ResolveResponse(turn=new_turn)

    # Derive and save player states
    for p in players:
        ps = derive_player_state(new_state, galaxy, p)
        storage.save_player_state(game_id, p, new_turn, ps)

    return ResolveResponse(turn=new_turn)
