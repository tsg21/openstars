"""Unit tests for POST /api/v1/auth/session."""

import json

import firebase_admin.auth
import pytest
from fastapi.testclient import TestClient

VALID_TOKEN = {
    "uid": "google-uid-1",
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
    yield
    get_storage.cache_clear()
    get_game_directory.cache_clear()
    firebase_app.cache_clear()


@pytest.fixture
def client():
    from openstars.server.main import app

    return TestClient(app)


def _patch_verify(monkeypatch, result):
    """Patch verify_id_token to return *result*, or raise it when it is an exception."""

    def _verify(credential, *args, **kwargs):
        if isinstance(result, Exception):
            raise result
        return result

    monkeypatch.setattr(firebase_admin.auth, "verify_id_token", _verify)


def _patch_claims(monkeypatch) -> list[dict]:
    """Capture set_custom_user_claims calls instead of hitting Firebase."""
    calls: list[dict] = []

    def _set(uid, claims):
        calls.append({"uid": uid, "claims": claims})

    monkeypatch.setattr(firebase_admin.auth, "set_custom_user_claims", _set)
    return calls


def _auth(token: str = "any-token") -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


class TestFitGameIds:
    """Unit tests for the byte-based _fit_game_ids helper."""

    def test_empty_list(self):
        from openstars.server.routes.auth import _fit_game_ids

        assert _fit_game_ids([]) == []

    def test_all_ids_fit(self):
        from openstars.server.routes.auth import _fit_game_ids

        ids = ["g1", "g2", "g3"]
        assert _fit_game_ids(ids) == ids

    def test_result_never_exceeds_byte_limit(self):
        from openstars.server.routes.auth import _fit_game_ids

        ids = [f"game-{i}" for i in range(200)]
        result = _fit_game_ids(ids, byte_limit=960)
        payload = json.dumps({"games": result}, separators=(",", ":")).encode()
        assert len(payload) <= 960

    def test_one_more_would_exceed_limit(self):
        """The entry just beyond the returned prefix must push the payload over the limit."""
        from openstars.server.routes.auth import _fit_game_ids

        ids = [f"game-{i}" for i in range(200)]
        result = _fit_game_ids(ids, byte_limit=960)
        # If all ids fit, there is no "one more" to check.
        if len(result) < len(ids):
            next_id = ids[len(result)]
            over = json.dumps({"games": result + [next_id]}, separators=(",", ":")).encode()
            assert len(over) > 960

    def test_truncates_by_bytes_not_count(self):
        """Long IDs cause truncation even when item count is small."""
        from openstars.server.routes.auth import _fit_game_ids

        # Each ID is 200 bytes; even 5 of them (+ JSON wrapper) exceed 960 bytes.
        long_ids = ["x" * 200 for _ in range(5)]
        result = _fit_game_ids(long_ids, byte_limit=960)
        assert len(result) < 5


class TestFirebaseTokenEndpointRemoved:
    def test_firebase_token_endpoint_is_gone(self, client):
        """Decision #3: the custom-token mint manufactured identity and was removed."""
        resp = client.post("/api/v1/auth/firebase-token", headers=_auth())
        assert resp.status_code == 404


class TestSessionEndpoint:
    def test_valid_token_writes_claims_against_verified_uid(self, client, monkeypatch):
        _patch_verify(monkeypatch, VALID_TOKEN)
        calls = _patch_claims(monkeypatch)

        resp = client.post("/api/v1/auth/session", headers=_auth())

        assert resp.status_code == 200
        assert len(calls) == 1
        # The uid is the Firebase-generated one from the token, not the email.
        assert calls[0]["uid"] == "google-uid-1"
        assert calls[0]["claims"] == {"games": []}

    def test_response_carries_identity_and_games(self, client, monkeypatch):
        _patch_verify(monkeypatch, VALID_TOKEN)
        calls = _patch_claims(monkeypatch)

        from openstars.game_directory.base import GameSummary
        from openstars.server.deps import get_game_directory

        directory = get_game_directory()
        directory.create_game(
            "g1",
            GameSummary.new(
                game_id="g1",
                name="G",
                galaxy_size="small",
                seed=1,
                players=["alice@example.com"],
            ),
        )

        resp = client.post("/api/v1/auth/session", headers=_auth())

        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == "alice@example.com"
        assert data["display_name"] == "Alice"
        assert data["games"] == ["g1"]
        assert calls[0]["claims"] == {"games": ["g1"]}

    def test_player_in_no_games_returns_empty_list(self, client, monkeypatch):
        _patch_verify(monkeypatch, VALID_TOKEN)
        calls = _patch_claims(monkeypatch)

        resp = client.post("/api/v1/auth/session", headers=_auth())

        assert resp.status_code == 200
        assert resp.json()["games"] == []
        assert calls[0]["claims"]["games"] == []

    def test_token_without_name_claim_yields_null_display_name(self, client, monkeypatch):
        _patch_verify(
            monkeypatch,
            {"uid": "u", "email": "bob@example.com", "email_verified": True},
        )
        _patch_claims(monkeypatch)

        resp = client.post("/api/v1/auth/session", headers=_auth())

        assert resp.status_code == 200
        assert resp.json()["display_name"] is None

    def test_missing_authorization_header_returns_401(self, client, monkeypatch):
        calls = _patch_claims(monkeypatch)

        resp = client.post("/api/v1/auth/session")

        assert resp.status_code == 401
        assert resp.json()["error"]["code"] == "MISSING_CREDENTIALS"
        assert calls == []

    def test_invalid_token_returns_401_and_writes_no_claims(self, client, monkeypatch):
        _patch_verify(monkeypatch, firebase_admin.auth.InvalidIdTokenError("bad token"))
        calls = _patch_claims(monkeypatch)

        resp = client.post("/api/v1/auth/session", headers=_auth())

        assert resp.status_code == 401
        assert resp.json()["error"]["code"] == "TOKEN_INVALID"
        assert calls == []

    def test_expired_token_returns_401_and_writes_no_claims(self, client, monkeypatch):
        _patch_verify(
            monkeypatch,
            firebase_admin.auth.ExpiredIdTokenError("expired", cause=None),
        )
        calls = _patch_claims(monkeypatch)

        resp = client.post("/api/v1/auth/session", headers=_auth())

        assert resp.status_code == 401
        assert resp.json()["error"]["code"] == "TOKEN_EXPIRED"
        assert calls == []

    def test_token_without_verified_email_returns_401(self, client, monkeypatch):
        _patch_verify(monkeypatch, {"uid": "u", "email": "x@example.com"})
        calls = _patch_claims(monkeypatch)

        resp = client.post("/api/v1/auth/session", headers=_auth())

        assert resp.status_code == 401
        assert resp.json()["error"]["code"] == "NO_VERIFIED_EMAIL"
        assert calls == []

    def test_truncation_warning_logged_at_limit(self, client, monkeypatch, caplog):
        import logging

        _patch_verify(monkeypatch, VALID_TOKEN)
        calls = _patch_claims(monkeypatch)

        from openstars.game_directory.base import GameSummary
        from openstars.server.deps import get_game_directory

        directory = get_game_directory()
        for i in range(200):
            directory.create_game(
                f"game-{i}",
                GameSummary.new(
                    game_id=f"game-{i}",
                    name=f"Game {i}",
                    galaxy_size="small",
                    seed=i,
                    players=["alice@example.com"],
                ),
            )

        with caplog.at_level(logging.WARNING, logger="openstars.server.routes.auth"):
            resp = client.post("/api/v1/auth/session", headers=_auth())

        assert resp.status_code == 200
        assert any("truncated" in r.message for r in caplog.records)
        # The written claim is the clipped list, not the full 200.
        assert len(calls[0]["claims"]["games"]) < 200
