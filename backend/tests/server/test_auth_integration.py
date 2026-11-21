"""End-to-end coverage of the signed-in API surface (task step 8).

These drive the real auth dependencies over HTTP with only
``verify_id_token`` stubbed, so the route stack, the directory queries and the
override rules are all genuinely exercised. The `int_tests/` suite cannot cover
this today — its client sends `X-Player` and has no way to mint a Google ID
token without the auth emulator running.
"""

from datetime import UTC, datetime

import firebase_admin.auth
import pytest
from fastapi.testclient import TestClient

from openstars.game_directory.base import GameSummary

ALICE = {
    "uid": "uid-alice",
    "email": "alice@example.com",
    "email_verified": True,
    "name": "Alice",
}


@pytest.fixture(autouse=True)
def _setup(tmp_path, monkeypatch):
    monkeypatch.setenv("STORAGE_BACKEND", "local")
    monkeypatch.setenv("GAME_DATA_PATH", str(tmp_path))
    monkeypatch.setenv("GAME_DIRECTORY_BACKEND", "memory")
    monkeypatch.setenv("FIREBASE_PROJECT_ID", "test-project")
    from openstars.server.auth import firebase_app
    from openstars.server.deps import get_game_directory, get_storage

    get_storage.cache_clear()
    get_game_directory.cache_clear()
    firebase_app.cache_clear()
    monkeypatch.setattr(firebase_admin, "get_app", lambda: object())
    monkeypatch.setattr(firebase_admin, "initialize_app", lambda **kw: object())
    monkeypatch.setattr(firebase_admin.auth, "verify_id_token", lambda cred, *a, **kw: ALICE)
    monkeypatch.setattr(firebase_admin.auth, "set_custom_user_claims", lambda uid, claims: None)
    yield
    get_storage.cache_clear()
    get_game_directory.cache_clear()
    firebase_app.cache_clear()


@pytest.fixture
def client():
    """Real auth dependencies — deliberately not the shared X-Player fixture."""
    from openstars.server.main import app

    return TestClient(app)


AUTH = {"Authorization": "Bearer any-token"}


def _directory():
    from openstars.server.deps import get_game_directory

    return get_game_directory()


def _seed(game_id: str, players: list[str], *, override: bool):
    _directory().create_game(
        game_id,
        GameSummary.new(
            game_id=game_id,
            name=game_id,
            galaxy_size="small",
            seed=1,
            players=players,
            allow_player_override=override,
        ),
    )


def _seed_legacy(game_id: str, players: list[str]):
    """A document written before allow_player_override existed."""
    now = datetime.now(UTC)
    _directory().create_game(
        game_id,
        GameSummary.model_validate(
            {
                "game_id": game_id,
                "name": game_id,
                "galaxy_size": "small",
                "seed": 1,
                "players": players,
                "current_turn": 0,
                "players_submitted": [],
                "created_at": now,
                "updated_at": now,
            }
        ),
    )


class TestAuthenticatedListing:
    def test_lists_own_and_override_games(self, client):
        _seed("mine", ["alice@example.com"], override=False)
        _seed("shared", ["tim", "matt"], override=True)
        _seed("someone-elses", ["bob@example.com"], override=False)

        resp = client.get("/api/v1/games", headers=AUTH)

        assert resp.status_code == 200
        assert {g["game_id"] for g in resp.json()["games"]} == {"mine", "shared"}

    def test_flag_is_reported_per_game(self, client):
        _seed("mine", ["alice@example.com"], override=False)
        _seed("shared", ["tim"], override=True)

        by_id = {g["game_id"]: g for g in client.get("/api/v1/games", headers=AUTH).json()["games"]}

        assert by_id["mine"]["allow_player_override"] is False
        assert by_id["shared"]["allow_player_override"] is True


class TestOverrideEnforcement:
    def test_override_honoured_on_an_override_game(self, client):
        _seed("shared", ["tim", "matt"], override=True)

        resp = client.get("/api/v1/games/shared", headers={**AUTH, "X-Player": "matt"})

        assert resp.status_code == 200

    def test_override_rejected_on_a_strict_game(self, client):
        _seed("strict", ["tim", "matt"], override=False)

        resp = client.get("/api/v1/games/strict", headers={**AUTH, "X-Player": "matt"})

        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "OVERRIDE_NOT_ALLOWED"

    def test_override_rejected_for_a_non_participant(self, client):
        _seed("shared", ["tim"], override=True)

        resp = client.get("/api/v1/games/shared", headers={**AUTH, "X-Player": "nobody"})

        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "NOT_PARTICIPANT"

    def test_verified_identity_must_be_a_participant(self, client):
        _seed("strict", ["bob@example.com"], override=False)

        resp = client.get("/api/v1/games/strict", headers=AUTH)

        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "NOT_PARTICIPANT"


class TestLegacyGamesRemainReachable:
    """Decision #8: documents predating the field keep working.

    This is the regression the model default of True exists to prevent, and the
    most likely thing to break.
    """

    def test_legacy_game_is_listed_for_its_participant(self, client):
        _seed_legacy("legacy", ["alice@example.com"])

        games = client.get("/api/v1/games", headers=AUTH).json()["games"]

        assert [g["game_id"] for g in games] == ["legacy"]
        # No stored field means the model default applies.
        assert games[0]["allow_player_override"] is True

    def test_legacy_game_is_joinable(self, client):
        _seed_legacy("legacy", ["alice@example.com"])

        resp = client.get("/api/v1/games/legacy", headers=AUTH)

        assert resp.status_code == 200
        assert resp.json()["game_id"] == "legacy"

    def test_legacy_game_accepts_an_override(self, client):
        """Reading True from the default means the override path stays open."""
        _seed_legacy("legacy", ["tim", "matt"])

        resp = client.get("/api/v1/games/legacy", headers={**AUTH, "X-Player": "matt"})

        assert resp.status_code == 200


class TestSessionEstablishesClaims:
    def test_session_returns_the_games_that_gate_firestore_reads(self, client):
        _seed("mine", ["alice@example.com"], override=False)

        resp = client.post("/api/v1/auth/session", headers=AUTH)

        assert resp.status_code == 200
        body = resp.json()
        assert body["username"] == "alice@example.com"
        assert body["games"] == ["mine"]
