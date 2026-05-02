"""Game management endpoints (PRD 09)."""

import logging
import re
import secrets
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Header

from openstars.engine.create_game import create_initial_state
from openstars.engine.fog import derive_player_state
from openstars.engine.galaxy import generate_galaxy
from openstars.server.deps import get_storage
from openstars.server.errors import error_response
from openstars.server.schemas import (
    CreateGameRequest,
    CreateGameResponse,
    GameDetail,
    GameListResponse,
    GameSummary,
    PlayerInfo,
    PlayerSubmissionInfo,
)
from openstars.server.turns import get_current_turn, player_submitted
from openstars.storage.base import GameStorage

router = APIRouter(prefix="/api/v1/games", tags=["games"])
log = logging.getLogger(__name__)

# Usernames must be safe for filesystem paths and URL segments
_USERNAME_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]*$")


def _validate_usernames(players: list[str]):
    """Reject usernames with unsafe characters."""
    for p in players:
        if not _USERNAME_RE.match(p) or len(p) > 64:
            return error_response(
                400,
                "INVALID_USERNAME",
                f"Username {p!r} contains invalid characters (alphanumeric, ., -, _ only)",
            )
    return None


def _slugify(name: str) -> str:
    """Create a URL-friendly slug from a game name."""
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    suffix = secrets.token_hex(4)
    if not slug:
        return suffix
    return f"{slug}-{suffix}"


@router.post("", status_code=201)
async def create_game(
    req: CreateGameRequest,
    storage: GameStorage = Depends(get_storage),
):
    """Create a new game."""
    valid_sizes = {"small", "medium", "large", "huge"}
    if req.galaxy_size not in valid_sizes:
        return error_response(400, "INVALID_GALAXY_SIZE", f"Must be one of: {valid_sizes}")

    if len(req.players) < 1:
        return error_response(400, "TOO_FEW_PLAYERS", "At least 1 player required")

    err = _validate_usernames(req.players)
    if err:
        return err

    if len(set(req.players)) != len(req.players):
        return error_response(400, "DUPLICATE_PLAYER", "Player usernames must be unique")

    game_id = _slugify(req.name)
    galaxy_seed = hash(game_id) & 0xFFFFFFFF
    game_seed = (galaxy_seed * 31 + 7) & 0xFFFFFFFF
    log.debug(
        "create_game: game_id=%s name=%r galaxy_size=%s players=%s galaxy_seed=%d game_seed=%d",
        game_id,
        req.name,
        req.galaxy_size,
        req.players,
        galaxy_seed,
        game_seed,
    )

    # Generate galaxy
    galaxy = generate_galaxy(req.name, req.galaxy_size, galaxy_seed)

    # Create initial state
    state, starting_designs = create_initial_state(galaxy, req.players, game_seed)

    # Derive player states
    for player in state.players:
        ps = derive_player_state(
            state,
            galaxy,
            player.username,
            starting_designs,
            previous_player_state=None,
        )
        storage.save_player_state(game_id, player.username, 0, ps)

    # Persist everything
    storage.save_galaxy(game_id, galaxy)
    storage.save_global_state(game_id, 0, state)

    created_at = datetime.now(UTC)
    storage.save_game_meta(
        game_id,
        {
            "name": req.name,
            "galaxy_size": req.galaxy_size,
            "seed": game_seed,
            "players": [p.username for p in state.players],
            "current_turn": 0,
            "created_at": created_at.isoformat(),
        },
    )

    return CreateGameResponse(
        game_id=game_id,
        name=req.name,
        galaxy_size=req.galaxy_size,
        turn=0,
        players=[PlayerInfo(username=p.username, name=p.name) for p in state.players],
        created_at=created_at,
    )


@router.get("")
async def list_games(
    storage: GameStorage = Depends(get_storage),
    x_player: str | None = Header(None),
):
    """List games, optionally filtered to a player."""
    game_ids = storage.list_games()
    games = []
    for gid in game_ids:
        try:
            meta = storage.load_game_meta(gid)
        except FileNotFoundError:
            continue

        players = meta.get("players", [])
        if x_player and x_player not in players:
            continue

        # Check current turn
        try:
            state = storage.load_global_state(gid, get_current_turn(storage, gid, meta))
            turn = state.game.turn
        except FileNotFoundError:
            turn = 0

        # Check submission status
        all_submitted = all(player_submitted(storage, gid, p, turn) for p in players)

        games.append(
            GameSummary(
                game_id=gid,
                name=meta["name"],
                galaxy_size=meta["galaxy_size"],
                turn=turn,
                players=players,
                all_turns_submitted=all_submitted,
                created_at=meta.get("created_at", ""),
            )
        )

    return GameListResponse(games=games)


@router.get("/{game_id}")
async def get_game(
    game_id: str,
    storage: GameStorage = Depends(get_storage),
    x_player: str = Header(...),
):
    """Get game detail with per-player submission status."""
    try:
        meta = storage.load_game_meta(game_id)
    except FileNotFoundError:
        return error_response(404, "GAME_NOT_FOUND", f"Game {game_id!r} not found")

    players = meta.get("players", [])
    if x_player not in players:
        return error_response(403, "NOT_PARTICIPANT", "You are not a participant in this game")

    turn = get_current_turn(storage, game_id, meta)

    player_info = []
    for p in players:
        submitted = player_submitted(storage, game_id, p, turn)
        player_info.append(
            PlayerSubmissionInfo(
                username=p,
                name=p,
                submitted=submitted,
            )
        )

    return GameDetail(
        game_id=game_id,
        name=meta["name"],
        galaxy_size=meta["galaxy_size"],
        turn=turn,
        players=player_info,
        created_at=meta.get("created_at", ""),
    )
