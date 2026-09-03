"""Session endpoint — maintains the Firestore `games` custom claim.

This is not API authorisation.  Every endpoint authorises via the bearer token
(PRD 50 § Authentication); this endpoint exists because Firestore security rules
run inside Firestore and cannot call the API, so the `games` custom claim is the
only way to gate document reads.
"""

import json
import logging

from fastapi import APIRouter, Depends

from openstars.game_directory.base import GameDirectory
from openstars.server.auth import firebase_app, get_current_identity, get_verified_token
from openstars.server.deps import get_game_directory

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
log = logging.getLogger(__name__)

# Fetch up to this many games from the directory before byte-based clipping.
_GAMES_FETCH_LIMIT = 200
# Firebase ID-token custom claims hard limit is 1 000 bytes; leave a small margin.
_CLAIMS_BYTE_LIMIT = 960


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


@router.post("/session")
async def session(
    token: dict = Depends(get_verified_token),
    email: str = Depends(get_current_identity),
    directory: GameDirectory = Depends(get_game_directory),
) -> dict:
    """Refresh the caller's `games` custom claim so Firestore rules admit their games.

    The claim is written against the uid from the *verified* token, never against a
    client-supplied string.  Claims only reach the client in tokens minted after this
    write, so the caller must force an ID-token refresh once this returns.

    Both dependencies are declared because the uid comes from the raw claims while the
    identity rules live in ``get_current_identity``; FastAPI caches ``get_verified_token``
    within a request, so the token is verified exactly once.
    """
    import firebase_admin.auth

    firebase_app()

    summaries = directory.list_games_for_player(email, limit=_GAMES_FETCH_LIMIT)
    all_game_ids = [s.game_id for s in summaries]
    game_ids = _fit_game_ids(all_game_ids)

    if len(game_ids) < len(all_game_ids):
        log.warning(
            "auth_session.games_truncated player=%s kept=%d total=%d byte_limit=%d",
            email,
            len(game_ids),
            len(all_game_ids),
            _CLAIMS_BYTE_LIMIT,
        )

    firebase_admin.auth.set_custom_user_claims(token["uid"], {"games": game_ids})

    return {"username": email, "display_name": token.get("name"), "games": game_ids}
