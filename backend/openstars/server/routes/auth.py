"""Firebase custom-token endpoint."""

import json
import logging
from datetime import UTC, datetime, timedelta
from functools import lru_cache

from fastapi import APIRouter, Depends, Header

from openstars.game_directory.base import GameDirectory
from openstars.server.deps import get_game_directory

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
log = logging.getLogger(__name__)

# Fetch up to this many games from the directory before byte-based clipping.
_GAMES_FETCH_LIMIT = 200
# Firebase ID-token custom claims hard limit is 1 000 bytes; leave a small margin.
_CLAIMS_BYTE_LIMIT = 960
_TOKEN_TTL = timedelta(hours=1)


def _fit_game_ids(game_ids: list[str], byte_limit: int = _CLAIMS_BYTE_LIMIT) -> list[str]:
    """Return the longest prefix of *game_ids* whose serialised claims payload fits in *byte_limit*.

    Count-based truncation is unreliable: even a handful of long IDs can push the
    ``{"games": [...]}`` payload over Firebase's 1 000-byte custom-claims limit, breaking
    token minting for that player.  Measuring bytes directly prevents the failure mode.
    """
    result: list[str] = []
    for game_id in game_ids:
        candidate = result + [game_id]
        if len(json.dumps({"games": candidate}, separators=(",", ":")).encode()) > byte_limit:
            break
        result = candidate
    return result


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

    summaries = directory.list_games_for_player(x_player, limit=_GAMES_FETCH_LIMIT)
    all_game_ids = [s.game_id for s in summaries]
    game_ids = _fit_game_ids(all_game_ids)

    if len(game_ids) < len(all_game_ids):
        log.warning(
            "firebase_token.games_truncated player=%s kept=%d total=%d byte_limit=%d",
            x_player,
            len(game_ids),
            len(all_game_ids),
            _CLAIMS_BYTE_LIMIT,
        )

    token_bytes = firebase_admin.auth.create_custom_token(
        uid=x_player,
        developer_claims={"games": game_ids},
    )
    token = token_bytes.decode() if isinstance(token_bytes, bytes) else token_bytes
    expires_at = (datetime.now(UTC) + _TOKEN_TTL).isoformat()

    return {"token": token, "expires_at": expires_at}
