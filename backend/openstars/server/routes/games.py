"""Game management endpoints (PRD 09)."""

import logging
import re
import secrets
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Header

from openstars.engine.create_game import create_initial_state
from openstars.engine.fog import derive_player_state
from openstars.engine.galaxy import generate_galaxy
from openstars.game_directory.base import GameDirectory, GameNotFoundError, GameSummary
from openstars.server.deps import get_game_directory, get_storage
from openstars.server.errors import error_response
from openstars.server.schemas import (
    CreateGameRequest,
    CreateGameResponse,
    GameDetail,
    GameListResponse,
    PlayerInfo,
    PlayerSubmissionInfo,
)
from openstars.server.schemas import (
    GameSummary as GameSummarySchema,
)
from openstars.server.turns import get_current_turn
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
    directory: GameDirectory = Depends(get_game_directory),
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

    try:
        storage.create_global_state(game_id, 0, state)
    except FileExistsError:
        return error_response(409, "GAME_ALREADY_EXISTS", f"Game {game_id!r} already exists")

    # Persist everything else after game-id reservation succeeds
    storage.save_galaxy(game_id, galaxy)

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

    created_at = datetime.now(UTC)
    summary = GameSummary(
        game_id=game_id,
        name=req.name,
        galaxy_size=req.galaxy_size,
        seed=game_seed,
        players=[p.username for p in state.players],
        current_turn=0,
        players_submitted=[],
        created_at=created_at,
        updated_at=created_at,
    )

    # GCS writes are durable — now write Firestore. On failure, GCS blobs are orphaned
    # (invisible to users) and can be reconciled by a cleanup pass.
    try:
        directory.create_game(game_id, summary)
    except Exception as exc:
        log.error(
            "create_game.firestore_failed game_id=%s error=%s (GCS blobs orphaned)", game_id, exc
        )
        return error_response(500, "DIRECTORY_WRITE_FAILED", "Failed to register game")

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
    directory: GameDirectory = Depends(get_game_directory),
    x_player: str | None = Header(None),
):
    """List games, optionally filtered to a player."""
    if x_player:
        summaries = directory.list_games_for_player(x_player)
    else:
        summaries = directory.list_all_games()

    games = [
        GameSummarySchema(
            game_id=s.game_id,
            name=s.name,
            galaxy_size=s.galaxy_size,
            turn=s.current_turn,
            players=s.players,
            all_turns_submitted=s.all_turns_submitted,
            created_at=s.created_at,
        )
        for s in summaries
    ]
    return GameListResponse(games=games)


@router.get("/{game_id}")
async def get_game(
    game_id: str,
    storage: GameStorage = Depends(get_storage),
    directory: GameDirectory = Depends(get_game_directory),
    x_player: str = Header(...),
):
    """Get game detail with per-player submission status."""
    try:
        summary = directory.get_game(game_id)
    except GameNotFoundError:
        return error_response(404, "GAME_NOT_FOUND", f"Game {game_id!r} not found")

    if x_player not in summary.players:
        return error_response(403, "NOT_PARTICIPANT", "You are not a participant in this game")

    turn = get_current_turn(summary)

    player_info = [
        PlayerSubmissionInfo(
            username=p,
            name=p,
            submitted=p in summary.players_submitted,
        )
        for p in summary.players
    ]

    return GameDetail(
        game_id=game_id,
        name=summary.name,
        galaxy_size=summary.galaxy_size,
        turn=turn,
        players=player_info,
        created_at=summary.created_at,
    )
