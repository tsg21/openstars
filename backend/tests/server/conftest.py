"""Shared server-test fixtures.

Every player-scoped endpoint now derives identity from a verified bearer token
(task step 4).  The existing suite predates that and addresses the API with an
``X-Player`` header, so the ``client`` fixture here overrides
:func:`get_current_identity` to read that header back.

Two consequences worth knowing:

* Because identity *is* the ``X-Player`` value under this fixture, the header can
  never name somebody else, so ``get_game_player`` never takes its override branch
  and ``allow_player_override`` is never consulted.  That is decision #9, and it is
  what keeps these tests working against games that default to strict.
* The override deliberately raises the same 401 as the real dependency when the
  header is absent, rather than letting FastAPI emit a 422.  A test that forgets
  the header should fail the way an unauthenticated caller does.

Tests that need to exercise the *real* auth path must not use this fixture —
see ``test_auth_deps.py`` (its own throwaway app) and ``test_auth_routes.py``
(a local ``client`` fixture that shadows this one).
"""

import pytest
from fastapi import Header
from fastapi.testclient import TestClient

from openstars.server.auth import get_current_identity
from openstars.server.errors import GameError


def _identity_from_header(x_player: str | None = Header(None)) -> str:
    if x_player is None:
        raise GameError(
            401, "MISSING_CREDENTIALS", "Authorization header with a bearer token is required"
        )
    return x_player


@pytest.fixture
def client():
    """A TestClient whose identity comes from the X-Player header."""
    from openstars.server.main import app

    app.dependency_overrides[get_current_identity] = _identity_from_header
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(get_current_identity, None)
