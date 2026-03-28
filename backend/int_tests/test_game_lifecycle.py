"""Integration test: full game lifecycle over the running backend container.

Covers: create game → get galaxy → get state → submit commands → resolve turn.
"""

import os
import time

import requests

BASE_URL = os.environ.get("API_URL", "http://localhost:8080")
API = f"{BASE_URL}/api/v1"

PLAYER_1 = "alice"
PLAYER_2 = "bob"


def wait_for_backend(timeout: int = 30):
    """Block until the backend health endpoint responds."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = requests.get(f"{API}/health", timeout=2)
            if r.status_code == 200:
                return
        except requests.ConnectionError:
            pass
        time.sleep(1)
    raise TimeoutError(f"Backend not ready after {timeout}s")


class TestGameLifecycle:
    """Walk through a full game turn."""

    game_id: str = ""

    @classmethod
    def setup_class(cls):
        wait_for_backend()

    # -- 1. Create game --

    def test_01_create_game(self):
        r = requests.post(
            f"{API}/games",
            json={
                "name": "Integration Test Game",
                "galaxy_size": "small",
                "players": [PLAYER_1, PLAYER_2],
            },
        )
        assert r.status_code == 201, f"Create failed: {r.status_code} {r.text}"
        body = r.json()
        assert body["name"] == "Integration Test Game"
        assert body["turn"] == 0
        assert len(body["players"]) == 2
        assert body["game_id"]
        # Store for subsequent tests
        TestGameLifecycle.game_id = body["game_id"]

    # -- 2. List games --

    def test_02_list_games(self):
        r = requests.get(f"{API}/games")
        assert r.status_code == 200
        games = r.json()["games"]
        assert any(g["game_id"] == self.game_id for g in games)

    # -- 3. Get game detail --

    def test_03_get_game_detail(self):
        r = requests.get(
            f"{API}/games/{self.game_id}",
            headers={"X-Player": PLAYER_1},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["turn"] == 0
        assert len(body["players"]) == 2
        # Nobody has submitted yet
        for p in body["players"]:
            assert p["submitted"] is False

    # -- 4. Get galaxy --

    def test_04_get_galaxy(self):
        r = requests.get(
            f"{API}/games/{self.game_id}/galaxy",
            headers={"X-Player": PLAYER_1},
        )
        assert r.status_code == 200
        body = r.json()
        assert "planets" in body
        assert len(body["planets"]) > 0
        assert "galaxy" in body
        assert body["galaxy"]["size"] == "small"

    # -- 5. Get player state (turn 0) --

    def test_05_get_player_state(self):
        r = requests.get(
            f"{API}/games/{self.game_id}/state",
            headers={"X-Player": PLAYER_1},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["turn"] == 0
        assert len(body["fleets"]) > 0
        assert len(body["planets"]) > 0
        # Store a fleet ID for commands
        TestGameLifecycle.fleet_id = body["fleets"][0]["id"]
        TestGameLifecycle.fleet_pos = body["fleets"][0]["position"]

    # -- 6. Both players forbidden from seeing each other's state --

    def test_06_non_participant_rejected(self):
        r = requests.get(
            f"{API}/games/{self.game_id}/state",
            headers={"X-Player": "eve"},
        )
        assert r.status_code == 403

    # -- 7. Submit commands (player 1: set waypoints) --

    def test_07_submit_commands_player1(self):
        # Move fleet slightly from its current position
        pos = self.fleet_pos
        target_x = pos["x"] + 1000
        target_y = pos["y"] + 1000

        r = requests.post(
            f"{API}/games/{self.game_id}/commands",
            headers={"X-Player": PLAYER_1},
            json={
                "turn": 0,
                "commands": [
                    {
                        "type": "set_waypoints",
                        "fleet_id": self.fleet_id,
                        "waypoints": [{"x": target_x, "y": target_y}],
                    }
                ],
            },
        )
        assert r.status_code == 200, f"Submit failed: {r.status_code} {r.text}"
        body = r.json()
        assert body["command_count"] == 1

    # -- 8. Get submitted commands back --

    def test_08_get_commands(self):
        r = requests.get(
            f"{API}/games/{self.game_id}/commands",
            headers={"X-Player": PLAYER_1},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["turn"] == 0
        assert len(body["commands"]) == 1

    # -- 9. Resolve fails if not all submitted --

    def test_09_resolve_fails_not_all_submitted(self):
        r = requests.post(
            f"{API}/games/{self.game_id}/resolve",
            headers={"X-Player": PLAYER_1},
        )
        assert r.status_code == 409
        assert r.json()["error"]["code"] == "NOT_ALL_SUBMITTED"

    # -- 10. Submit commands (player 2: empty) --

    def test_10_submit_commands_player2(self):
        r = requests.post(
            f"{API}/games/{self.game_id}/commands",
            headers={"X-Player": PLAYER_2},
            json={
                "turn": 0,
                "commands": [],
            },
        )
        assert r.status_code == 200

    # -- 11. Resolve succeeds --

    def test_11_resolve_turn(self):
        r = requests.post(
            f"{API}/games/{self.game_id}/resolve",
            headers={"X-Player": PLAYER_1},
        )
        assert r.status_code == 200, f"Resolve failed: {r.status_code} {r.text}"
        body = r.json()
        assert body["turn"] == 1
        assert body["status"] == "resolved"

    # -- 12. Verify turn advanced --

    def test_12_state_after_resolve(self):
        r = requests.get(
            f"{API}/games/{self.game_id}/state",
            headers={"X-Player": PLAYER_1},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["turn"] == 1

    # -- 13. Game detail shows turn 1, no submissions --

    def test_13_game_detail_after_resolve(self):
        r = requests.get(
            f"{API}/games/{self.game_id}",
            headers={"X-Player": PLAYER_1},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["turn"] == 1
        for p in body["players"]:
            assert p["submitted"] is False
