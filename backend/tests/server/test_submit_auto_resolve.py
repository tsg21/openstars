"""Unit tests for the auto-resolve flow in POST /commands (Step 3)."""

from datetime import UTC, datetime

import pytest

from openstars.game_directory.base import GameSummary


def _summary(game_id: str = "g1", players: list[str] | None = None, turn: int = 0) -> GameSummary:
    now = datetime.now(UTC)
    return GameSummary(
        game_id=game_id,
        name="Test",
        galaxy_size="small",
        seed=42,
        players=players or ["tim", "matt"],
        current_turn=turn,
        players_submitted=[],
        created_at=now,
        updated_at=now,
    )


@pytest.fixture(autouse=True)
def _setup(tmp_path, monkeypatch):
    """Local storage + in-memory directory for each test."""
    monkeypatch.setenv("STORAGE_BACKEND", "local")
    monkeypatch.setenv("GAME_DATA_PATH", str(tmp_path))
    monkeypatch.setenv("GAME_DIRECTORY_BACKEND", "memory")
    from openstars.server.deps import get_game_directory, get_storage

    get_storage.cache_clear()
    get_game_directory.cache_clear()
    yield
    get_storage.cache_clear()
    get_game_directory.cache_clear()


def _create_game(client, players=("tim", "matt")):
    """POST /games and advance through T=0 race selection (auto-resolves to T=1)."""
    resp = client.post(
        "/api/v1/games",
        json={"name": "Test Game", "galaxy_size": "small", "players": list(players)},
        headers={"X-Player": players[0]},
    )
    assert resp.status_code == 201
    game_id = resp.json()["game_id"]
    for p in players:
        r = client.post(
            f"/api/v1/games/{game_id}/commands",
            json={"turn": 0, "commands": [{"type": "select_race", "predefined_id": "humanoid"}]},
            headers={"X-Player": p},
        )
        assert r.status_code == 200
    return game_id


class TestAutoResolveUnit:
    def test_partial_submit_returns_not_resolved(self, client):
        game_id = _create_game(client)
        resp = client.post(
            f"/api/v1/games/{game_id}/commands",
            json={"turn": 1, "commands": []},
            headers={"X-Player": "tim"},
        )
        assert resp.status_code == 200
        assert resp.json()["turn_resolved"] is False
        assert resp.json()["new_turn"] is None

    def test_last_submit_returns_resolved_with_new_turn(self, client):
        game_id = _create_game(client)
        client.post(
            f"/api/v1/games/{game_id}/commands",
            json={"turn": 1, "commands": []},
            headers={"X-Player": "tim"},
        )
        resp = client.post(
            f"/api/v1/games/{game_id}/commands",
            json={"turn": 1, "commands": []},
            headers={"X-Player": "matt"},
        )
        assert resp.status_code == 200
        assert resp.json()["turn_resolved"] is True
        assert resp.json()["new_turn"] == 2

    def test_last_submit_advances_directory_turn(self, client):
        game_id = _create_game(client)
        from openstars.server.deps import get_game_directory

        directory = get_game_directory()
        assert directory.get_game(game_id).current_turn == 1

        client.post(
            f"/api/v1/games/{game_id}/commands",
            json={"turn": 1, "commands": []},
            headers={"X-Player": "tim"},
        )
        client.post(
            f"/api/v1/games/{game_id}/commands",
            json={"turn": 1, "commands": []},
            headers={"X-Player": "matt"},
        )
        assert directory.get_game(game_id).current_turn == 2
        assert directory.get_game(game_id).players_submitted == []

    def test_directory_player_submitted_called_on_each_submit(self, client):
        game_id = _create_game(client)
        from openstars.server.deps import get_game_directory

        directory = get_game_directory()

        client.post(
            f"/api/v1/games/{game_id}/commands",
            json={"turn": 1, "commands": []},
            headers={"X-Player": "tim"},
        )
        assert "tim" in directory.get_game(game_id).players_submitted

    def test_idempotent_resubmit_does_not_advance_turn(self, client):
        game_id = _create_game(client)
        from openstars.server.deps import get_game_directory

        directory = get_game_directory()

        client.post(
            f"/api/v1/games/{game_id}/commands",
            json={"turn": 1, "commands": []},
            headers={"X-Player": "tim"},
        )
        # Resubmit — still only tim submitted, turn does not advance.
        client.post(
            f"/api/v1/games/{game_id}/commands",
            json={"turn": 1, "commands": []},
            headers={"X-Player": "tim"},
        )
        assert directory.get_game(game_id).current_turn == 1

    def test_turn_zero_auto_resolves_on_last_race_select(self, client):
        resp = client.post(
            "/api/v1/games",
            json={"name": "T0 Game", "galaxy_size": "small", "players": ["tim", "matt"]},
            headers={"X-Player": "tim"},
        )
        assert resp.status_code == 201
        game_id = resp.json()["game_id"]

        client.post(
            f"/api/v1/games/{game_id}/commands",
            json={"turn": 0, "commands": [{"type": "select_race", "predefined_id": "humanoid"}]},
            headers={"X-Player": "tim"},
        )
        last = client.post(
            f"/api/v1/games/{game_id}/commands",
            json={"turn": 0, "commands": [{"type": "select_race", "predefined_id": "humanoid"}]},
            headers={"X-Player": "matt"},
        )
        assert last.json()["turn_resolved"] is True
        assert last.json()["new_turn"] == 1

    def test_resolution_failure_returns_500_with_code(self, client, monkeypatch):
        game_id = _create_game(client)

        def boom(*args, **kwargs):
            raise RuntimeError("engine on fire")

        monkeypatch.setattr("openstars.server.routes.play.resolve_current_turn", boom)

        client.post(
            f"/api/v1/games/{game_id}/commands",
            json={"turn": 1, "commands": []},
            headers={"X-Player": "tim"},
        )
        resp = client.post(
            f"/api/v1/games/{game_id}/commands",
            json={"turn": 1, "commands": []},
            headers={"X-Player": "matt"},
        )
        assert resp.status_code == 500
        assert resp.json()["error"]["code"] == "RESOLUTION_FAILED"

    def test_resolve_endpoint_returns_404(self, client):
        game_id = _create_game(client)
        resp = client.post(f"/api/v1/games/{game_id}/resolve", headers={"X-Player": "tim"})
        assert resp.status_code == 404
