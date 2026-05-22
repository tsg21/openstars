"""Firebase custom-token endpoint."""

import logging
from datetime import UTC, datetime, timedelta
from functools import lru_cache

from fastapi import APIRouter, Depends, Header

from openstars.game_directory.base import GameDirectory
from openstars.server.deps import get_game_directory

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
log = logging.getLogger(__name__)

_GAMES_LIMIT = 200
_TOKEN_TTL = timedelta(hours=1)


@lru_cache
def _firebase_app():
    """Initialise the default Firebase app once per process."""
    import os

    import firebase_admin

    project_id = os.environ.get("FIREBASE_PROJECT_ID")
    if not project_id:
        raise RuntimeError("FIREBASE_PROJECT_ID must be set")

    options = {"projectId": project_id}
    try:
        return firebase_admin.get_app()
    except ValueError:
        return firebase_admin.initialize_app(options=options)


@router.post("/firebase-token")
async def firebase_token(
    x_player: str = Header(...),
    directory: GameDirectory = Depends(get_game_directory),
):
    """Mint a Firebase custom token for the caller, with a `games` claim."""
    import firebase_admin.auth

    _firebase_app()

    summaries = directory.list_games_for_player(x_player, limit=_GAMES_LIMIT)
    game_ids = [s.game_id for s in summaries]

    if len(game_ids) == _GAMES_LIMIT:
        log.warning("firebase_token.games_truncated player=%s limit=%d", x_player, _GAMES_LIMIT)

    token_bytes = firebase_admin.auth.create_custom_token(
        uid=x_player,
        developer_claims={"games": game_ids},
    )
    token = token_bytes.decode() if isinstance(token_bytes, bytes) else token_bytes
    expires_at = (datetime.now(UTC) + _TOKEN_TTL).isoformat()

    return {"token": token, "expires_at": expires_at}
