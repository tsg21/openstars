"""Every player-scoped route rejects an unauthenticated caller (task step 4).

These deliberately do **not** use the shared ``client`` fixture: that fixture
overrides ``get_current_identity`` so the rest of the suite can keep addressing the
API with ``X-Player``, which would mask exactly the behaviour asserted here.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _setup(tmp_path, monkeypatch):
    monkeypatch.setenv("STORAGE_BACKEND", "local")
    monkeypatch.setenv("GAME_DATA_PATH", str(tmp_path))
    monkeypatch.setenv("GAME_DIRECTORY_BACKEND", "memory")
    monkeypatch.setenv("FIREBASE_PROJECT_ID", "test-project")
    from openstars.server.deps import get_game_directory, get_storage

    get_storage.cache_clear()
    get_game_directory.cache_clear()
    yield
    get_storage.cache_clear()
    get_game_directory.cache_clear()


@pytest.fixture
def raw_client():
    """A client with the real auth dependencies mounted."""
    from openstars.server.main import app

    return TestClient(app)


# (method, path) for one representative of each migrated route family.
ROUTES = [
    ("post", "/api/v1/games"),
    ("get", "/api/v1/games"),
    ("get", "/api/v1/games/g1"),
    ("get", "/api/v1/games/g1/turn-status"),
    ("get", "/api/v1/games/g1/galaxy"),
    ("get", "/api/v1/games/g1/state"),
    ("post", "/api/v1/games/g1/commands"),
    ("get", "/api/v1/games/g1/commands"),
    ("get", "/api/v1/games/g1/designs"),
    ("get", "/api/v1/games/g1/designs/reference-data"),
    ("get", "/api/v1/games/g1/designs/d1"),
    ("post", "/api/v1/games/g1/designs"),
    ("get", "/api/v1/games/g1/race"),
    ("post", "/api/v1/race/preview"),
    ("post", "/api/v1/auth/session"),
]


def _call(client, method, path, **kwargs):
    """TestClient.get() takes no body, so only send one on the methods that accept it."""
    if method == "post":
        kwargs["json"] = {}
    return getattr(client, method)(path, **kwargs)


@pytest.mark.parametrize(("method", "path"), ROUTES)
def test_route_requires_credentials(raw_client, method, path):
    resp = _call(raw_client, method, path)
    assert resp.status_code == 401, f"{method.upper()} {path} returned {resp.status_code}"
    assert resp.json()["error"]["code"] == "MISSING_CREDENTIALS"


@pytest.mark.parametrize(("method", "path"), ROUTES)
def test_route_rejects_x_player_as_identity(raw_client, method, path):
    """X-Player is an override request, never a credential (decision #2)."""
    resp = _call(raw_client, method, path, headers={"X-Player": "tim"})
    assert resp.status_code == 401, f"{method.upper()} {path} returned {resp.status_code}"


@pytest.mark.parametrize(("method", "path"), ROUTES)
def test_route_rejects_malformed_authorization(raw_client, method, path):
    resp = _call(raw_client, method, path, headers={"Authorization": "Token abc"})
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "MALFORMED_CREDENTIALS"


def test_predefined_races_stays_public(raw_client):
    """Static preset data has no player scope and was never header-gated."""
    resp = raw_client.get("/api/v1/race/predefined")
    assert resp.status_code == 200
