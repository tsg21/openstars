"""Unit tests for POST /api/v1/auth/firebase-token."""

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _setup(tmp_path, monkeypatch):
    monkeypatch.setenv("STORAGE_BACKEND", "local")
    monkeypatch.setenv("GAME_DATA_PATH", str(tmp_path))
    monkeypatch.setenv("GAME_DIRECTORY_BACKEND", "memory")
    monkeypatch.setenv("FIREBASE_PROJECT_ID", "test-project")
    from openstars.server.deps import get_game_directory, get_storage
    from openstars.server.routes.auth import _firebase_app

    get_storage.cache_clear()
    get_game_directory.cache_clear()
    _firebase_app.cache_clear()
    yield
    get_storage.cache_clear()
    get_game_directory.cache_clear()
    _firebase_app.cache_clear()


@pytest.fixture
def client():
    from openstars.server.main import app

    return TestClient(app)


def _patch_firebase(monkeypatch, token_return=b"mock-token"):
    """Patch firebase_admin so tests don't need a real SDK init."""
    mock_app = MagicMock()
    monkeypatch.setattr("firebase_admin.get_app", lambda: mock_app)
    monkeypatch.setattr("firebase_admin.initialize_app", lambda **kw: mock_app)
    monkeypatch.setattr(
        "firebase_admin.auth.create_custom_token", lambda uid, developer_claims: token_return
    )
    return mock_app


class TestFirebaseTokenEndpoint:
    def test_missing_x_player_returns_422(self, client, monkeypatch):
        _patch_firebase(monkeypatch)
        resp = client.post("/api/v1/auth/firebase-token")
        assert resp.status_code == 422

    def test_returns_token_and_expires_at(self, client, monkeypatch):
        _patch_firebase(monkeypatch, token_return=b"test-jwt")
        resp = client.post("/api/v1/auth/firebase-token", headers={"X-Player": "tim"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["token"] == "test-jwt"
        # expires_at should be an ISO-8601 string ~1 hour from now
        expires = datetime.fromisoformat(data["expires_at"])
        diff = expires - datetime.now(UTC)
        assert 3500 < diff.total_seconds() < 3700

    def test_create_custom_token_called_with_correct_args(self, client, monkeypatch):
        calls = []

        def fake_create(uid, developer_claims):
            calls.append({"uid": uid, "claims": developer_claims})
            return b"tok"

        mock_app = MagicMock()
        monkeypatch.setattr("firebase_admin.get_app", lambda: mock_app)
        monkeypatch.setattr("firebase_admin.initialize_app", lambda **kw: mock_app)
        monkeypatch.setattr("firebase_admin.auth.create_custom_token", fake_create)

        # Create a game so the player has one entry
        client.post(
            "/api/v1/games",
            json={"name": "G", "galaxy_size": "small", "players": ["tim"]},
        )
        resp = client.post("/api/v1/auth/firebase-token", headers={"X-Player": "tim"})
        assert resp.status_code == 200

        assert len(calls) == 1
        assert calls[0]["uid"] == "tim"
        assert len(calls[0]["claims"]["games"]) == 1

    def test_no_games_returns_empty_list(self, client, monkeypatch):
        calls = []

        def fake_create(uid, developer_claims):
            calls.append(developer_claims)
            return b"tok"

        mock_app = MagicMock()
        monkeypatch.setattr("firebase_admin.get_app", lambda: mock_app)
        monkeypatch.setattr("firebase_admin.initialize_app", lambda **kw: mock_app)
        monkeypatch.setattr("firebase_admin.auth.create_custom_token", fake_create)

        resp = client.post("/api/v1/auth/firebase-token", headers={"X-Player": "nobody"})
        assert resp.status_code == 200
        assert calls[0]["games"] == []

    def test_string_token_returned_as_is(self, client, monkeypatch):
        """Tokens that come back as str (not bytes) are passed through unchanged."""
        _patch_firebase(monkeypatch, token_return="already-a-string")
        resp = client.post("/api/v1/auth/firebase-token", headers={"X-Player": "tim"})
        assert resp.json()["token"] == "already-a-string"

    def test_truncation_warning_logged_at_limit(self, client, monkeypatch, caplog):
        import logging

        mock_app = MagicMock()
        monkeypatch.setattr("firebase_admin.get_app", lambda: mock_app)
        monkeypatch.setattr("firebase_admin.initialize_app", lambda **kw: mock_app)
        monkeypatch.setattr(
            "firebase_admin.auth.create_custom_token", lambda uid, developer_claims: b"t"
        )

        # Inject 200 fake game summaries into the directory
        from datetime import UTC, datetime

        from openstars.game_directory.base import GameSummary
        from openstars.server.deps import get_game_directory

        directory = get_game_directory()
        now = datetime.now(UTC)
        for i in range(200):
            directory.create_game(
                f"game-{i}",
                GameSummary(
                    game_id=f"game-{i}",
                    name=f"Game {i}",
                    galaxy_size="small",
                    seed=i,
                    players=["tim"],
                    current_turn=0,
                    players_submitted=[],
                    created_at=now,
                    updated_at=now,
                ),
            )

        with caplog.at_level(logging.WARNING, logger="openstars.server.routes.auth"):
            resp = client.post("/api/v1/auth/firebase-token", headers={"X-Player": "tim"})

        assert resp.status_code == 200
        assert any("truncated" in r.message for r in caplog.records)
