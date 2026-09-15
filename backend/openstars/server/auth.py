"""Bearer-token authentication dependencies (PRD 50 § Authentication).

Identity is taken from a verified Google ID token, never from a client-supplied
string.  ``X-Player`` survives only as an *override request* on games that carry
``allow_player_override`` — see :func:`get_game_player`.
"""

from functools import lru_cache
from typing import NamedTuple

from fastapi import Depends, Header

from openstars.game_directory.base import GameDirectory, GameNotFoundError, GameSummary
from openstars.server.deps import get_game_directory
from openstars.server.errors import GameError


@lru_cache
def firebase_app():
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


def _bearer_token(authorization: str | None) -> str:
    """Extract the bearer credential from an ``Authorization`` header value."""
    if not authorization:
        raise GameError(
            401, "MISSING_CREDENTIALS", "Authorization header with a bearer token is required"
        )

    scheme, _, credential = authorization.partition(" ")
    if scheme.lower() != "bearer" or not credential.strip():
        raise GameError(
            401, "MALFORMED_CREDENTIALS", "Authorization header must be 'Bearer <id-token>'"
        )
    return credential.strip()


def get_verified_token(authorization: str | None = Header(None)) -> dict:
    """Verify the caller's Google ID token and return its decoded claims.

    Every failure mode is a 401 — a bad credential is never a server error.
    """
    import firebase_admin.auth

    credential = _bearer_token(authorization)
    firebase_app()

    try:
        # check_revoked is deliberately off: it costs a round-trip to the Firebase
        # user record on every request. RevokedIdTokenError is still handled so
        # that turning it on stays a one-line change.
        return firebase_admin.auth.verify_id_token(credential)
    except firebase_admin.auth.ExpiredIdTokenError as exc:
        raise GameError(401, "TOKEN_EXPIRED", "ID token has expired") from exc
    except firebase_admin.auth.RevokedIdTokenError as exc:
        raise GameError(401, "TOKEN_REVOKED", "ID token has been revoked") from exc
    except (firebase_admin.auth.InvalidIdTokenError, ValueError) as exc:
        raise GameError(401, "TOKEN_INVALID", "ID token could not be verified") from exc


def get_current_identity(token: dict = Depends(get_verified_token)) -> str:
    """Return the caller's verified email — the player identity for the whole API."""
    email = token.get("email")
    if not email or not token.get("email_verified"):
        raise GameError(401, "NO_VERIFIED_EMAIL", "ID token carries no verified email address")
    return email


class GamePlayer(NamedTuple):
    """Resolved game context for a player-scoped route."""

    summary: GameSummary
    player: str


def get_game_player(
    game_id: str,
    identity: str = Depends(get_current_identity),
    x_player: str | None = Header(None),
    directory: GameDirectory = Depends(get_game_directory),
) -> GamePlayer:
    """Resolve the effective player for a game-scoped route.

    Without an override header the effective player is the verified identity.  An
    ``X-Player`` header naming someone else is honoured only when the game carries
    ``allow_player_override`` *and* the requested player is a participant; anything
    else is a 403 rather than a silent fall-back to the caller's own identity.
    """
    try:
        summary = directory.get_game(game_id)
    except GameNotFoundError as exc:
        raise GameError(404, "GAME_NOT_FOUND", f"Game {game_id!r} not found") from exc

    if x_player is not None and x_player != identity:
        if not summary.allow_player_override:
            raise GameError(
                403,
                "OVERRIDE_NOT_ALLOWED",
                f"Game {game_id!r} does not allow playing as another player",
            )
        if x_player not in summary.players:
            raise GameError(
                403, "NOT_PARTICIPANT", f"{x_player!r} is not a participant in this game"
            )
        return GamePlayer(summary, x_player)

    if identity not in summary.players:
        raise GameError(403, "NOT_PARTICIPANT", "You are not a participant in this game")

    return GamePlayer(summary, identity)
