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

    # -- 14. Economy fields present on own planet at turn 0 --

    def test_14_home_planet_economy_at_turn_0(self):
        # Re-fetch turn-0 state isn't possible post-resolve, so we check turn-1
        # state — the home planet fields should always be present for own planets.
        r = requests.get(
            f"{API}/games/{self.game_id}/state",
            headers={"X-Player": PLAYER_1},
        )
        assert r.status_code == 200
        planets = r.json()["planets"]

        own = next((p for p in planets if p.get("owner") == PLAYER_1), None)
        assert own is not None, "Own planet not found in player state"
        assert own["scan_level"] == "detailed"

        # Concentrations must be present and in valid range
        concs = own.get("concentrations")
        assert concs is not None, "concentrations missing from own planet"
        for mineral in ("ironium", "boranium", "germanium"):
            assert 1 <= concs[mineral] <= 200, f"{mineral} concentration out of range"

        # Home planet concentrations must all be >= 30
        for mineral in ("ironium", "boranium", "germanium"):
            assert concs[mineral] >= 30, f"Home planet {mineral} concentration below floor"

        # Surface minerals present (300 kT each at start, may have grown via mining)
        minerals = own.get("minerals")
        assert minerals is not None, "minerals missing from own planet"
        for mineral in ("ironium", "boranium", "germanium"):
            assert minerals[mineral] >= 300, f"Surface {mineral} below initial 300 kT"

        # Resources must be a positive integer
        assert own.get("resources") is not None, "resources missing from own planet"
        assert own["resources"] > 0

        # mining_rate present (may be zero if mines=0 after a future test extension)
        assert own.get("mining_rate") is not None, "mining_rate missing from own planet"

    # -- 15. Economy fields absent on unscanned planets --

    def test_15_unscanned_planets_have_no_economy(self):
        r = requests.get(
            f"{API}/games/{self.game_id}/state",
            headers={"X-Player": PLAYER_1},
        )
        assert r.status_code == 200
        planets = r.json()["planets"]

        unscanned = [p for p in planets if p["scan_level"] == "none"]
        for p in unscanned:
            assert p.get("concentrations") is None
            assert p.get("minerals") is None
            assert p.get("resources") is None
            assert p.get("mining_rate") is None
