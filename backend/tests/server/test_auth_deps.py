"""Unit tests for the bearer-token auth dependencies (task step 2)."""

from datetime import UTC, datetime

import firebase_admin.auth
import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from openstars.game_directory.base import GameSummary
from openstars.server.auth import (
    GamePlayer,
    firebase_app,
    get_current_identity,
    get_game_player,
)
from openstars.server.errors import GameError

VALID_TOKEN = {
    "uid": "google-uid-1",
    "email": "alice@example.com",
    "email_verified": True,
    "name": "Alice",
}


@pytest.fixture(autouse=True)
def _setup(tmp_path, monkeypatch):
    monkeypatch.setenv("STORAGE_BACKEND", "memory")
    monkeypatch.setenv("GAME_DIRECTORY_BACKEND", "memory")
    monkeypatch.setenv("FIREBASE_PROJECT_ID", "test-project")
    from openstars.server.deps import get_game_directory, get_storage

    get_storage.cache_clear()
    get_game_directory.cache_clear()
    firebase_app.cache_clear()
    monkeypatch.setattr(firebase_admin, "get_app", lambda: object())
    monkeypatch.setattr(firebase_admin, "initialize_app", lambda **kw: object())
    yield
    get_storage.cache_clear()
    get_game_directory.cache_clear()
    firebase_app.cache_clear()


@pytest.fixture
def app() -> FastAPI:
    """A throwaway app exposing the real dependencies over HTTP."""
    api = FastAPI()

    from openstars.server.main import game_error_handler

    api.add_exception_handler(GameError, game_error_handler)

    @api.get("/identity")
    async def identity(who: str = Depends(get_current_identity)) -> dict:
        return {"identity": who}

    @api.get("/games/{game_id}/player")
    async def game_player(context: GamePlayer = Depends(get_game_player)) -> dict:
        return {"player": context.player, "game_id": context.summary.game_id}

    return api


@pytest.fixture
def client(app) -> TestClient:
    return TestClient(app)


def _patch_verify(monkeypatch, result):
    """Patch verify_id_token to return *result*, or raise it when it is an exception."""

    def _verify(credential, *args, **kwargs):
        if isinstance(result, Exception):
            raise result
        return result

    monkeypatch.setattr(firebase_admin.auth, "verify_id_token", _verify)


def _bearer(token: str = "any-token") -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _make_game(
    game_id: str,
    players: list[str],
    *,
    allow_player_override: bool = False,
) -> GameSummary:
    from openstars.server.deps import get_game_directory

    now = datetime.now(UTC)
    summary = GameSummary(
        game_id=game_id,
        name=game_id,
        galaxy_size="small",
        seed=1,
        players=players,
        current_turn=0,
        players_submitted=[],
        created_at=now,
        updated_at=now,
        allow_player_override=allow_player_override,
    )
    get_game_directory().create_game(game_id, summary)
    return summary


class TestGetCurrentIdentity:
    def test_valid_token_yields_email(self, client, monkeypatch):
        _patch_verify(monkeypatch, VALID_TOKEN)
        resp = client.get("/identity", headers=_bearer())
        assert resp.status_code == 200
        assert resp.json() == {"identity": "alice@example.com"}

    def test_missing_header_is_401(self, client, monkeypatch):
        _patch_verify(monkeypatch, VALID_TOKEN)
        resp = client.get("/identity")
        assert resp.status_code == 401
        assert resp.json()["error"]["code"] == "MISSING_CREDENTIALS"

    @pytest.mark.parametrize(
        "header",
        ["", "Bearer", "Bearer ", "Basic abc123", "abc123"],
    )
    def test_malformed_header_is_401(self, client, monkeypatch, header):
        _patch_verify(monkeypatch, VALID_TOKEN)
        resp = client.get("/identity", headers={"Authorization": header})
        assert resp.status_code == 401
        assert resp.json()["error"]["code"] in {"MISSING_CREDENTIALS", "MALFORMED_CREDENTIALS"}

    def test_invalid_token_is_401(self, client, monkeypatch):
        _patch_verify(monkeypatch, firebase_admin.auth.InvalidIdTokenError("nope"))
        resp = client.get("/identity", headers=_bearer())
        assert resp.status_code == 401
        assert resp.json()["error"]["code"] == "TOKEN_INVALID"

    def test_value_error_from_sdk_is_401_not_500(self, client, monkeypatch):
        _patch_verify(monkeypatch, ValueError("not a JWT"))
        resp = client.get("/identity", headers=_bearer())
        assert resp.status_code == 401
        assert resp.json()["error"]["code"] == "TOKEN_INVALID"

    def test_expired_token_is_401_with_distinct_code(self, client, monkeypatch):
        _patch_verify(monkeypatch, firebase_admin.auth.ExpiredIdTokenError("old", None))
        resp = client.get("/identity", headers=_bearer())
        assert resp.status_code == 401
        assert resp.json()["error"]["code"] == "TOKEN_EXPIRED"

    def test_revoked_token_is_401_with_distinct_code(self, client, monkeypatch):
        _patch_verify(monkeypatch, firebase_admin.auth.RevokedIdTokenError("gone"))
        resp = client.get("/identity", headers=_bearer())
        assert resp.status_code == 401
        assert resp.json()["error"]["code"] == "TOKEN_REVOKED"

    def test_token_without_email_is_401(self, client, monkeypatch):
        _patch_verify(monkeypatch, {"uid": "u1", "email_verified": True})
        resp = client.get("/identity", headers=_bearer())
        assert resp.status_code == 401
        assert resp.json()["error"]["code"] == "NO_VERIFIED_EMAIL"

    def test_token_with_unverified_email_is_401(self, client, monkeypatch):
        _patch_verify(monkeypatch, {"uid": "u1", "email": "a@b.com", "email_verified": False})
        resp = client.get("/identity", headers=_bearer())
        assert resp.status_code == 401
        assert resp.json()["error"]["code"] == "NO_VERIFIED_EMAIL"


class TestGetGamePlayer:
    def test_identity_is_the_effective_player(self, client, monkeypatch):
        _patch_verify(monkeypatch, VALID_TOKEN)
        _make_game("g1", ["alice@example.com", "bob@example.com"])
        resp = client.get("/games/g1/player", headers=_bearer())
        assert resp.status_code == 200
        assert resp.json() == {"player": "alice@example.com", "game_id": "g1"}

    def test_unknown_game_is_404(self, client, monkeypatch):
        _patch_verify(monkeypatch, VALID_TOKEN)
        resp = client.get("/games/missing/player", headers=_bearer())
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "GAME_NOT_FOUND"

    def test_404_takes_precedence_over_participant_check(self, client, monkeypatch):
        """A non-participant asking for a game that does not exist gets 404, not 403."""
        _patch_verify(monkeypatch, VALID_TOKEN)
        resp = client.get(
            "/games/missing/player",
            headers={**_bearer(), "X-Player": "someone-else"},
        )
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "GAME_NOT_FOUND"

    def test_identity_not_a_participant_is_403(self, client, monkeypatch):
        _patch_verify(monkeypatch, VALID_TOKEN)
        _make_game("g1", ["bob@example.com"])
        resp = client.get("/games/g1/player", headers=_bearer())
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "NOT_PARTICIPANT"

    def test_unauthenticated_request_is_401(self, client, monkeypatch):
        _patch_verify(monkeypatch, VALID_TOKEN)
        _make_game("g1", ["alice@example.com"])
        resp = client.get("/games/g1/player")
        assert resp.status_code == 401

    def test_override_honoured_on_override_game(self, client, monkeypatch):
        _patch_verify(monkeypatch, VALID_TOKEN)
        _make_game("g1", ["tim", "matt"], allow_player_override=True)
        resp = client.get("/games/g1/player", headers={**_bearer(), "X-Player": "matt"})
        assert resp.status_code == 200
        assert resp.json()["player"] == "matt"

    def test_override_rejected_on_non_override_game(self, client, monkeypatch):
        """Even when the target is a participant, a game without the flag says no."""
        _patch_verify(monkeypatch, VALID_TOKEN)
        _make_game("g1", ["alice@example.com", "matt"], allow_player_override=False)
        resp = client.get("/games/g1/player", headers={**_bearer(), "X-Player": "matt"})
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "OVERRIDE_NOT_ALLOWED"

    def test_override_rejected_for_non_participant(self, client, monkeypatch):
        _patch_verify(monkeypatch, VALID_TOKEN)
        _make_game("g1", ["tim", "matt"], allow_player_override=True)
        resp = client.get("/games/g1/player", headers={**_bearer(), "X-Player": "eve"})
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "NOT_PARTICIPANT"

    def test_override_naming_the_caller_is_not_an_override(self, client, monkeypatch):
        """X-Player equal to the verified identity asks for nothing, so the flag is irrelevant."""
        _patch_verify(monkeypatch, VALID_TOKEN)
        _make_game("g1", ["alice@example.com"], allow_player_override=False)
        resp = client.get(
            "/games/g1/player",
            headers={**_bearer(), "X-Player": "alice@example.com"},
        )
        assert resp.status_code == 200
        assert resp.json()["player"] == "alice@example.com"

    def test_override_still_requires_a_valid_token(self, client, monkeypatch):
        _patch_verify(monkeypatch, firebase_admin.auth.InvalidIdTokenError("nope"))
        _make_game("g1", ["tim", "matt"], allow_player_override=True)
        resp = client.get("/games/g1/player", headers={**_bearer(), "X-Player": "matt"})
        assert resp.status_code == 401


class TestGameSummaryOverrideDefaults:
    def test_missing_field_defaults_to_true(self):
        """Documents written before the field existed must stay reachable."""
        now = datetime.now(UTC)
        summary = GameSummary.model_validate(
            {
                "game_id": "legacy",
                "name": "Legacy",
                "galaxy_size": "small",
                "seed": 1,
                "players": ["tim"],
                "current_turn": 0,
                "players_submitted": [],
                "created_at": now,
                "updated_at": now,
            }
        )
        assert summary.allow_player_override is True

    def test_new_defaults_to_false(self):
        summary = GameSummary.new("g", "G", "small", 1, ["tim"])
        assert summary.allow_player_override is False

    def test_new_honours_explicit_flag(self):
        summary = GameSummary.new("g", "G", "small", 1, ["tim"], allow_player_override=True)
        assert summary.allow_player_override is True
