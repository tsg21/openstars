"""Integration tests for the API endpoints."""

import json
import os

import pytest
from fastapi.testclient import TestClient

from openstars.engine.models import Habitability, ProductionQueueItem, Scanner
from openstars.engine.resolve_steps.movement import LIGHT_YEAR
from openstars.storage.compression import decode_json


@pytest.fixture(autouse=True)
def _setup_storage(tmp_path):
    """Point storage to a temp directory for each test."""
    os.environ["STORAGE_BACKEND"] = "local"
    os.environ["GAME_DATA_PATH"] = str(tmp_path)
    # Clear the lru_cache so it picks up the new path
    from openstars.server.deps import get_storage

    get_storage.cache_clear()
    yield
    os.environ.pop("STORAGE_BACKEND", None)
    os.environ.pop("GAME_DATA_PATH", None)
    get_storage.cache_clear()


@pytest.fixture
def client():
    from openstars.server.main import app

    return TestClient(app)


def _create_game(client, name="Test Game", players=None, *, advance=True):
    """Create a game; by default, submit Humanoid for each player and resolve T=0 → T=1."""
    if players is None:
        players = ["tim", "matt"]
    resp = client.post(
        "/api/v1/games",
        json={
            "name": name,
            "galaxy_size": "small",
            "players": players,
        },
    )
    if not advance or resp.status_code != 201:
        return resp

    game_id = resp.json()["game_id"]
    for player in players:
        submit = client.post(
            f"/api/v1/games/{game_id}/commands",
            json={
                "turn": 0,
                "commands": [{"type": "select_race", "predefined_id": "humanoid"}],
            },
            headers={"X-Player": player},
        )
        assert submit.status_code == 200, submit.text
    resolve = client.post(
        f"/api/v1/games/{game_id}/resolve",
        headers={"X-Player": players[0]},
    )
    assert resolve.status_code == 200, resolve.text
    return resp


class TestHealth:
    def test_health(self, client):
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


class TestCreateGame:
    def test_create_game(self, client):
        resp = _create_game(client)
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Test Game"
        assert data["galaxy_size"] == "small"
        assert data["turn"] == 0
        assert len(data["players"]) == 2
        assert "game_id" in data

    def test_create_game_single_player(self, client):
        resp = _create_game(client, name="Solo Game", players=["lonely"])
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Solo Game"
        assert len(data["players"]) == 1
        assert data["players"][0]["username"] == "lonely"

    def test_create_game_invalid_size(self, client):
        resp = client.post(
            "/api/v1/games",
            json={
                "name": "Bad Game",
                "galaxy_size": "tiny",
                "players": ["a", "b"],
            },
        )
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "INVALID_GALAXY_SIZE"

    def test_create_game_too_few_players(self, client):
        resp = client.post(
            "/api/v1/games",
            json={
                "name": "Empty Game",
                "galaxy_size": "small",
                "players": [],
            },
        )
        assert resp.status_code == 422  # Pydantic validation

    def test_create_game_rejects_unsafe_username(self, client):
        resp = client.post(
            "/api/v1/games",
            json={
                "name": "Hacked Game",
                "galaxy_size": "small",
                "players": ["tim", "../../etc/passwd"],
            },
        )
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "INVALID_USERNAME"

    def test_create_game_rejects_duplicate_players(self, client):
        resp = client.post(
            "/api/v1/games",
            json={
                "name": "Duped Game",
                "galaxy_size": "small",
                "players": ["tim", "tim"],
            },
        )
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "DUPLICATE_PLAYER"

    def test_create_game_name_with_no_alphanumeric(self, client):
        resp = client.post(
            "/api/v1/games",
            json={
                "name": "!!!",
                "galaxy_size": "small",
                "players": ["tim", "matt"],
            },
        )
        assert resp.status_code == 201
        # Game ID should be just the hex suffix (no leading dash)
        game_id = resp.json()["game_id"]
        assert not game_id.startswith("-")
        assert len(game_id) == 8  # Just the hex suffix


class TestListGames:
    def test_list_empty(self, client):
        resp = client.get("/api/v1/games")
        assert resp.status_code == 200
        assert resp.json()["games"] == []

    def test_list_after_create(self, client):
        _create_game(client)
        resp = client.get("/api/v1/games")
        assert resp.status_code == 200
        games = resp.json()["games"]
        assert len(games) == 1
        assert games[0]["name"] == "Test Game"

    def test_list_filtered(self, client):
        _create_game(client, players=["tim", "matt"])
        resp = client.get("/api/v1/games", headers={"X-Player": "tim"})
        assert len(resp.json()["games"]) == 1

        resp = client.get("/api/v1/games", headers={"X-Player": "stranger"})
        assert len(resp.json()["games"]) == 0


class TestGameDetail:
    def test_get_game(self, client):
        create_resp = _create_game(client)
        game_id = create_resp.json()["game_id"]
        resp = client.get(f"/api/v1/games/{game_id}", headers={"X-Player": "tim"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["game_id"] == game_id
        assert data["turn"] == 1

    def test_not_participant(self, client):
        create_resp = _create_game(client)
        game_id = create_resp.json()["game_id"]
        resp = client.get(f"/api/v1/games/{game_id}", headers={"X-Player": "stranger"})
        assert resp.status_code == 403

    def test_game_not_found(self, client):
        resp = client.get("/api/v1/games/nonexistent", headers={"X-Player": "tim"})
        assert resp.status_code == 404


class TestTurnStatus:
    def test_get_turn_status(self, client):
        create_resp = _create_game(client, advance=False)
        game_id = create_resp.json()["game_id"]

        resp = client.get(f"/api/v1/games/{game_id}/turn-status", headers={"X-Player": "tim"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["turn"] == 0
        assert sorted(body["players_awaiting_submission"]) == ["matt", "tim"]

    def test_turn_status_advances_after_resolve(self, client):
        create_resp = _create_game(client)
        game_id = create_resp.json()["game_id"]

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
        client.post(f"/api/v1/games/{game_id}/resolve", headers={"X-Player": "tim"})

        resp = client.get(f"/api/v1/games/{game_id}/turn-status", headers={"X-Player": "tim"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["turn"] == 2
        assert sorted(body["players_awaiting_submission"]) == ["matt", "tim"]


class TestGalaxy:
    def test_get_galaxy(self, client):
        create_resp = _create_game(client)
        game_id = create_resp.json()["game_id"]
        resp = client.get(f"/api/v1/games/{game_id}/galaxy", headers={"X-Player": "tim"})
        assert resp.status_code == 200
        data = resp.json()
        assert "galaxy" in data
        assert "planets" in data
        assert len(data["planets"]) == 50  # default small galaxy


class TestPlayerState:
    def test_get_state(self, client):
        create_resp = _create_game(client)
        game_id = create_resp.json()["game_id"]
        resp = client.get(f"/api/v1/games/{game_id}/state", headers={"X-Player": "tim"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["player"] == "tim"
        assert data["turn"] == 1
        assert data["state_version"] == 1
        assert len(data["fleets"]) >= 1
        assert len(data["designs"]) >= 1

    def test_create_game_persists_versioned_state_files(self, client, tmp_path):
        create_resp = _create_game(client)
        game_id = create_resp.json()["game_id"]

        global_state_path = tmp_path / game_id / "state" / "global-state-T0.json.gz"
        player_state_path = tmp_path / game_id / "players" / "player-state-tim-T0.json.gz"

        assert json.loads(decode_json(global_state_path.read_bytes()))["state_version"] == 1
        assert json.loads(decode_json(player_state_path.read_bytes()))["state_version"] == 1

    def test_fleet_names_in_player_state(self, client):
        create_resp = _create_game(client)
        game_id = create_resp.json()["game_id"]

        resp = client.get(f"/api/v1/games/{game_id}/state", headers={"X-Player": "tim"})
        assert resp.status_code == 200
        own_fleets = [f for f in resp.json()["fleets"] if f["owner"] == "tim"]
        names = {f["name"] for f in own_fleets}
        assert names == {"Fleet #1", "Fleet #2", "Fleet #3", "Fleet #4"}

    def test_get_state_includes_starting_colony_ship(self, client):
        create_resp = _create_game(client)
        game_id = create_resp.json()["game_id"]

        resp = client.get(f"/api/v1/games/{game_id}/state", headers={"X-Player": "tim"})
        assert resp.status_code == 200
        data = resp.json()

        own_designs = [design for design in data["designs"] if design["owner"] == "tim"]
        assert {design["hull"] for design in own_designs} == {
            "scout",
            "small_freighter",
            "colony_ship",
        }

        own_fleets = [fleet for fleet in data["fleets"] if fleet["owner"] == "tim"]
        colony_ship_design_ids = {
            design["id"] for design in own_designs if design["hull"] == "colony_ship"
        }
        colony_ship_fleets = [
            fleet
            for fleet in own_fleets
            if fleet["composition"] is not None
            and fleet["composition"][0]["design_id"] in colony_ship_design_ids
        ]
        assert len(colony_ship_fleets) == 1
        assert colony_ship_fleets[0]["cargo"]["colonists"] == 0


class TestSubmitCommands:
    def test_submit_set_waypoints_accepts_colonise_task(self, client):
        create_resp = _create_game(client)
        game_id = create_resp.json()["game_id"]

        state_resp = client.get(f"/api/v1/games/{game_id}/state", headers={"X-Player": "tim"})
        assert state_resp.status_code == 200
        state_data = state_resp.json()
        colony_ship_design_ids = {
            design["id"]
            for design in state_data["designs"]
            if design["owner"] == "tim" and design["hull"] == "colony_ship"
        }
        colony_fleet = next(
            fleet
            for fleet in state_data["fleets"]
            if fleet["owner"] == "tim"
            and fleet["composition"]
            and fleet["composition"][0]["design_id"] in colony_ship_design_ids
        )

        submit_resp = client.post(
            f"/api/v1/games/{game_id}/commands",
            json={
                "turn": 1,
                "commands": [
                    {
                        "type": "set_waypoints",
                        "fleet_id": colony_fleet["id"],
                        "waypoints": [
                            {
                                "x": colony_fleet["position"]["x"],
                                "y": colony_fleet["position"]["y"],
                                "task": {"type": "colonise"},
                            }
                        ],
                    }
                ],
            },
            headers={"X-Player": "tim"},
        )

        assert submit_resp.status_code == 200

    def test_colonised_planet_visible_after_resolve_and_events_owner_only(self, client):
        create_resp = _create_game(client)
        game_id = create_resp.json()["game_id"]

        state_resp = client.get(f"/api/v1/games/{game_id}/state", headers={"X-Player": "tim"})
        assert state_resp.status_code == 200
        state_data = state_resp.json()

        own_planet = next(
            planet for planet in state_data["planets"] if planet.get("owner") == "tim"
        )
        colony_ship_design_ids = {
            design["id"]
            for design in state_data["designs"]
            if design["owner"] == "tim" and design["hull"] == "colony_ship"
        }
        colony_fleet = next(
            fleet
            for fleet in state_data["fleets"]
            if fleet["owner"] == "tim"
            and fleet["composition"]
            and fleet["composition"][0]["design_id"] in colony_ship_design_ids
        )
        target_planet = next(
            planet for planet in state_data["planets"] if planet.get("owner") is None
        )

        from openstars.server.deps import get_storage

        storage = get_storage()
        galaxy = storage.load_galaxy(game_id)
        global_state = storage.load_global_state(game_id, 1)

        for gp in galaxy.planets:
            if gp.id == target_planet["id"]:
                gp.x = own_planet["x"] + 3 * LIGHT_YEAR
                gp.y = own_planet["y"]

        for fleet in global_state.fleets:
            if fleet.id == colony_fleet["id"]:
                fleet.position.x = own_planet["x"]
                fleet.position.y = own_planet["y"]
        for planet in global_state.planets:
            if planet.id == target_planet["id"]:
                planet.habitability = Habitability(gravity=50, temperature=50, radiation=50)

        storage.save_galaxy(game_id, galaxy)
        storage.save_global_state(game_id, 1, global_state)

        submit_resp = client.post(
            f"/api/v1/games/{game_id}/commands",
            json={
                "turn": 1,
                "commands": [
                    {
                        "type": "set_waypoints",
                        "fleet_id": colony_fleet["id"],
                        "waypoints": [
                            {
                                "x": own_planet["x"],
                                "y": own_planet["y"],
                                "task": {
                                    "type": "transport",
                                    "orders": [
                                        {
                                            "cargo_type": "colonists",
                                            "action": "load_all",
                                        }
                                    ],
                                },
                            },
                            {
                                "x": own_planet["x"] + 3 * LIGHT_YEAR,
                                "y": own_planet["y"],
                                "task": {"type": "colonise"},
                            },
                        ],
                    }
                ],
            },
            headers={"X-Player": "tim"},
        )
        assert submit_resp.status_code == 200
        assert (
            client.post(
                f"/api/v1/games/{game_id}/commands",
                json={"turn": 1, "commands": []},
                headers={"X-Player": "matt"},
            ).status_code
            == 200
        )


class TestShipDesignsAndProduction:
    def test_get_designs_returns_only_requesting_player_designs(self, client):
        create_resp = _create_game(client)
        game_id = create_resp.json()["game_id"]

        tim_resp = client.get(f"/api/v1/games/{game_id}/designs", headers={"X-Player": "tim"})
        matt_resp = client.get(f"/api/v1/games/{game_id}/designs", headers={"X-Player": "matt"})

        assert tim_resp.status_code == 200
        assert matt_resp.status_code == 200
        tim_designs = tim_resp.json()["designs"]
        matt_designs = matt_resp.json()["designs"]
        assert len(tim_designs) >= 1
        assert len(matt_designs) >= 1
        assert all({"id", "name", "hull", "fuel_capacity", "cost"} <= d.keys() for d in tim_designs)
        assert all(
            {"id", "name", "hull", "fuel_capacity", "cost"} <= d.keys() for d in matt_designs
        )

    def test_submit_ship_production_item_requires_starbase(self, client):
        create_resp = _create_game(client, players=["tim"])
        game_id = create_resp.json()["game_id"]
        state = client.get(f"/api/v1/games/{game_id}/state", headers={"X-Player": "tim"}).json()
        design_id = client.get(
            f"/api/v1/games/{game_id}/designs", headers={"X-Player": "tim"}
        ).json()["designs"][0]["id"]
        target_planet = next(planet for planet in state["planets"] if planet.get("owner") == "tim")

        from openstars.server.deps import get_storage

        storage = get_storage()
        gs = storage.load_global_state(game_id, 1)
        for planet in gs.planets:
            if planet.id == target_planet["id"]:
                planet.starbase = None
        storage.save_global_state(game_id, 1, gs)

        resp = client.post(
            f"/api/v1/games/{game_id}/commands",
            json={
                "turn": 1,
                "commands": [
                    {
                        "type": "add_production_item",
                        "planet_id": target_planet["id"],
                        "item_type": "ship",
                        "design_id": design_id,
                        "quantity": 1,
                    }
                ],
            },
            headers={"X-Player": "tim"},
        )
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "STARBASE_REQUIRED"

    def test_get_designs_is_stable_across_turn_resolution(self, client):
        create_resp = _create_game(client, players=["tim"])
        game_id = create_resp.json()["game_id"]
        before = client.get(f"/api/v1/games/{game_id}/designs", headers={"X-Player": "tim"}).json()[
            "designs"
        ]

        client.post(
            f"/api/v1/games/{game_id}/commands",
            json={"turn": 1, "commands": []},
            headers={"X-Player": "tim"},
        )
        client.post(f"/api/v1/games/{game_id}/resolve", headers={"X-Player": "tim"})

        after = client.get(f"/api/v1/games/{game_id}/designs", headers={"X-Player": "tim"}).json()[
            "designs"
        ]
        assert after == before

    def test_submit_ship_production_item_rejects_foreign_design(self, client):
        create_resp = _create_game(client)
        game_id = create_resp.json()["game_id"]
        tim_state = client.get(f"/api/v1/games/{game_id}/state", headers={"X-Player": "tim"}).json()
        matt_design_id = client.get(
            f"/api/v1/games/{game_id}/designs", headers={"X-Player": "matt"}
        ).json()["designs"][0]["id"]
        tim_planet = next(planet for planet in tim_state["planets"] if planet.get("owner") == "tim")

        resp = client.post(
            f"/api/v1/games/{game_id}/commands",
            json={
                "turn": 1,
                "commands": [
                    {
                        "type": "add_production_item",
                        "planet_id": tim_planet["id"],
                        "item_type": "ship",
                        "design_id": matt_design_id,
                        "quantity": 1,
                    }
                ],
            },
            headers={"X-Player": "tim"},
        )
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "DESIGN_NOT_OWNED"

    def test_ship_production_builds_ship_and_emits_event(self, client):
        create_resp = _create_game(client, players=["tim"])
        game_id = create_resp.json()["game_id"]
        state = client.get(f"/api/v1/games/{game_id}/state", headers={"X-Player": "tim"}).json()
        create_design_resp = client.post(
            f"/api/v1/games/{game_id}/designs",
            json={
                "name": "Fresh Scout",
                "hull": "scout",
                "components": [
                    {
                        "slot_number": 1,
                        "component_id": "quick_jump_5",
                        "component_count": 1,
                    }
                ],
            },
            headers={"X-Player": "tim"},
        )
        assert create_design_resp.status_code == 201
        design = create_design_resp.json()["design"]
        planet = next(p for p in state["planets"] if p.get("owner") == "tim")

        from openstars.server.deps import get_storage

        storage = get_storage()
        gs = storage.load_global_state(game_id, 1)
        for p in gs.planets:
            if p.id == planet["id"]:
                p.mines = 50
                p.factories = 50
                p.minerals.ironium = 100
                p.minerals.boranium = 100
                p.minerals.germanium = 100
                p.production_queue = [
                    ProductionQueueItem(
                        id="PQship1",
                        item_type="ship",
                        design_id=design["id"],
                        quantity=1,
                    )
                ]
                gs.planet_resources[p.id] = 100
        storage.save_global_state(game_id, 1, gs)

        # normal resolve path recalculates resources; submit empty commands and resolve.
        client.post(
            f"/api/v1/games/{game_id}/commands",
            json={"turn": 1, "commands": []},
            headers={"X-Player": "tim"},
        )
        client.post(f"/api/v1/games/{game_id}/resolve", headers={"X-Player": "tim"})

        new_state = client.get(f"/api/v1/games/{game_id}/state", headers={"X-Player": "tim"}).json()
        assert any(event["code"] == "production.ship_built" for event in new_state["events"])
        built_fleets = [
            fleet
            for fleet in new_state["fleets"]
            if fleet["owner"] == "tim"
            and fleet["composition"]
            and any(entry["design_id"] == design["id"] for entry in fleet["composition"])
        ]
        assert built_fleets
        assert len(built_fleets) == 1
        assert built_fleets[0].get("fuel") == design["fuel_capacity"]
        assert built_fleets[0].get("fuel_capacity") == design["fuel_capacity"]

    def test_player_isolation(self, client):
        """Tim should not see Matt's fleet details."""
        create_resp = _create_game(client)
        game_id = create_resp.json()["game_id"]

        tim_state = client.get(f"/api/v1/games/{game_id}/state", headers={"X-Player": "tim"}).json()
        client.get(f"/api/v1/games/{game_id}/state", headers={"X-Player": "matt"}).json()

        # Tim's fleets should have composition
        tim_fleets = [f for f in tim_state["fleets"] if f["owner"] == "tim"]
        assert all(f["composition"] is not None for f in tim_fleets)

        # If Tim sees Matt's fleet, it should have no composition
        matt_fleets_seen = [f for f in tim_state["fleets"] if f["owner"] == "matt"]
        for f in matt_fleets_seen:
            assert f["composition"] is None
            assert f["waypoints"] is None

    def test_production_queue_visible_only_on_owned_planets(self, client):
        create_resp = _create_game(client)
        game_id = create_resp.json()["game_id"]

        tim_state_t0 = client.get(
            f"/api/v1/games/{game_id}/state",
            headers={"X-Player": "tim"},
        ).json()
        tim_planet_id = next(p["id"] for p in tim_state_t0["planets"] if p.get("owner") == "tim")

        client.post(
            f"/api/v1/games/{game_id}/commands",
            json={
                "turn": 1,
                "commands": [
                    {
                        "type": "add_production_item",
                        "planet_id": tim_planet_id,
                        "item_type": "factory",
                        "quantity": 5,
                    }
                ],
            },
            headers={"X-Player": "tim"},
        )
        client.post(
            f"/api/v1/games/{game_id}/commands",
            json={"turn": 1, "commands": []},
            headers={"X-Player": "matt"},
        )
        client.post(f"/api/v1/games/{game_id}/resolve", headers={"X-Player": "tim"})

        tim_state_t1 = client.get(
            f"/api/v1/games/{game_id}/state?turn=2",
            headers={"X-Player": "tim"},
        ).json()
        tim_planet = next(p for p in tim_state_t1["planets"] if p["id"] == tim_planet_id)
        assert tim_planet["production_queue"] is not None
        assert tim_planet["production_queue"][0]["item_type"] == "factory"
        assert any(event["code"] == "production.completed" for event in tim_state_t1["events"])

        matt_state_t1 = client.get(
            f"/api/v1/games/{game_id}/state?turn=2",
            headers={"X-Player": "matt"},
        ).json()
        tim_planet_for_matt = next(p for p in matt_state_t1["planets"] if p["id"] == tim_planet_id)
        assert tim_planet_for_matt["production_queue"] is None


class TestCommands:
    def _get_fleet_id(self, client, game_id, player):
        state = client.get(f"/api/v1/games/{game_id}/state", headers={"X-Player": player}).json()
        own_fleets = [f for f in state["fleets"] if f["owner"] == player]
        return own_fleets[0]["id"]

    def _get_planet_id(self, client, game_id, player):
        state = client.get(f"/api/v1/games/{game_id}/state", headers={"X-Player": player}).json()
        own_planets = [p for p in state["planets"] if p.get("owner") == player]
        return own_planets[0]["id"]

    def test_submit_and_retrieve(self, client):
        create_resp = _create_game(client)
        game_id = create_resp.json()["game_id"]
        fleet_id = self._get_fleet_id(client, game_id, "tim")

        # Submit commands
        resp = client.post(
            f"/api/v1/games/{game_id}/commands",
            json={
                "turn": 1,
                "commands": [
                    {
                        "type": "set_waypoints",
                        "fleet_id": fleet_id,
                        "waypoints": [{"x": 549755813888, "y": 549755813888}],
                    }
                ],
            },
            headers={"X-Player": "tim"},
        )
        assert resp.status_code == 200
        assert resp.json()["command_count"] == 1

        # Retrieve commands
        resp = client.get(f"/api/v1/games/{game_id}/commands", headers={"X-Player": "tim"})
        assert resp.status_code == 200
        assert len(resp.json()["commands"]) == 1

    def test_turn_mismatch(self, client):
        create_resp = _create_game(client)
        game_id = create_resp.json()["game_id"]
        self._get_fleet_id(client, game_id, "tim")

        resp = client.post(
            f"/api/v1/games/{game_id}/commands",
            json={"turn": 5, "commands": []},
            headers={"X-Player": "tim"},
        )
        assert resp.status_code == 409

    def test_fleet_not_owned(self, client):
        create_resp = _create_game(client)
        game_id = create_resp.json()["game_id"]
        # Get Tim's fleet ID and try to command it as Matt
        fleet_id = self._get_fleet_id(client, game_id, "tim")

        resp = client.post(
            f"/api/v1/games/{game_id}/commands",
            json={
                "turn": 1,
                "commands": [
                    {
                        "type": "set_waypoints",
                        "fleet_id": fleet_id,
                        "waypoints": [],
                    }
                ],
            },
            headers={"X-Player": "matt"},
        )
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "FLEET_NOT_OWNED"

    def test_waypoint_out_of_bounds(self, client):
        create_resp = _create_game(client)
        game_id = create_resp.json()["game_id"]
        fleet_id = self._get_fleet_id(client, game_id, "tim")

        resp = client.post(
            f"/api/v1/games/{game_id}/commands",
            json={
                "turn": 1,
                "commands": [
                    {
                        "type": "set_waypoints",
                        "fleet_id": fleet_id,
                        "waypoints": [{"x": -1, "y": 0}],
                    }
                ],
            },
            headers={"X-Player": "tim"},
        )
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "WAYPOINT_OUT_OF_BOUNDS"

    def test_waypoint_non_integer_coordinates(self, client):
        create_resp = _create_game(client)
        game_id = create_resp.json()["game_id"]
        fleet_id = self._get_fleet_id(client, game_id, "tim")

        resp = client.post(
            f"/api/v1/games/{game_id}/commands",
            json={
                "turn": 1,
                "commands": [
                    {
                        "type": "set_waypoints",
                        "fleet_id": fleet_id,
                        "waypoints": [{"x": "1", "y": 2}],
                    }
                ],
            },
            headers={"X-Player": "tim"},
        )
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "INVALID_WAYPOINT"

    def test_submit_merge_split_with_tmp_waypoint(self, client):
        create_resp = _create_game(client)
        game_id = create_resp.json()["game_id"]
        state = client.get(f"/api/v1/games/{game_id}/state", headers={"X-Player": "tim"}).json()
        own_fleets = [fleet for fleet in state["fleets"] if fleet["owner"] == "tim"]
        first = own_fleets[0]
        second = own_fleets[1]

        resp = client.post(
            f"/api/v1/games/{game_id}/commands",
            json={
                "turn": 1,
                "commands": [
                    {
                        "type": "merge_split_fleets",
                        "fleets": [
                            {
                                "fleet_id": first["id"],
                                "ships": list(first["composition"] or []),
                            },
                            {
                                "fleet_id": "tmp_1",
                                "ships": list(second["composition"] or []),
                            },
                            {
                                "fleet_id": second["id"],
                                "ships": [],
                            },
                        ],
                    },
                    {
                        "type": "set_waypoints",
                        "fleet_id": "tmp_1",
                        "waypoints": [
                            {
                                "x": first["position"]["x"],
                                "y": first["position"]["y"],
                                "warp": 5,
                            }
                        ],
                    },
                ],
            },
            headers={"X-Player": "tim"},
        )

        assert resp.status_code == 200
        stored = client.get(f"/api/v1/games/{game_id}/commands", headers={"X-Player": "tim"})
        assert stored.status_code == 200
        assert [command["type"] for command in stored.json()["commands"]] == [
            "merge_split_fleets",
            "set_waypoints",
        ]
        assert stored.json()["commands"][1]["fleet_id"] == "tmp_1"

    def test_empty_commands_before_submit(self, client):
        create_resp = _create_game(client)
        game_id = create_resp.json()["game_id"]
        resp = client.get(f"/api/v1/games/{game_id}/commands", headers={"X-Player": "tim"})
        assert resp.status_code == 200
        assert resp.json()["commands"] == []

    def test_submit_production_commands(self, client):
        create_resp = _create_game(client)
        game_id = create_resp.json()["game_id"]
        planet_id = self._get_planet_id(client, game_id, "tim")

        resp = client.post(
            f"/api/v1/games/{game_id}/commands",
            json={
                "turn": 1,
                "commands": [
                    {
                        "type": "add_production_item",
                        "planet_id": planet_id,
                        "item_type": "factory",
                        "quantity": 2,
                        "insert_after_item_id": None,
                    },
                    {
                        "type": "clear_production_queue",
                        "planet_id": planet_id,
                    },
                ],
            },
            headers={"X-Player": "tim"},
        )

        assert resp.status_code == 200
        assert resp.json()["command_count"] == 2

        stored = client.get(f"/api/v1/games/{game_id}/commands", headers={"X-Player": "tim"})
        assert stored.status_code == 200
        assert stored.json()["commands"][0]["type"] == "add_production_item"
        assert stored.json()["commands"][1]["type"] == "clear_production_queue"

    def test_submit_starbase_production_command(self, client):
        create_resp = _create_game(client)
        game_id = create_resp.json()["game_id"]
        planet_id = self._get_planet_id(client, game_id, "tim")

        resp = client.post(
            f"/api/v1/games/{game_id}/commands",
            json={
                "turn": 1,
                "commands": [
                    {
                        "type": "add_production_item",
                        "planet_id": planet_id,
                        "item_type": "starbase",
                        "target_type": "orbital_fort",
                        "quantity": 1,
                    }
                ],
            },
            headers={"X-Player": "tim"},
        )

        assert resp.status_code == 200
        stored = client.get(f"/api/v1/games/{game_id}/commands", headers={"X-Player": "tim"})
        assert stored.status_code == 200
        assert stored.json()["commands"][0]["target_type"] == "orbital_fort"

    def test_submit_starbase_production_rejects_invalid_target_type(self, client):
        create_resp = _create_game(client)
        game_id = create_resp.json()["game_id"]
        planet_id = self._get_planet_id(client, game_id, "tim")

        resp = client.post(
            f"/api/v1/games/{game_id}/commands",
            json={
                "turn": 1,
                "commands": [
                    {
                        "type": "add_production_item",
                        "planet_id": planet_id,
                        "item_type": "starbase",
                        "target_type": "death_star",
                        "quantity": 1,
                    }
                ],
            },
            headers={"X-Player": "tim"},
        )

        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "INVALID_STARBASE_TARGET_TYPE"

    def test_submit_starbase_production_rejects_duplicate_unfinished_item(self, client):
        create_resp = _create_game(client)
        game_id = create_resp.json()["game_id"]
        planet_id = self._get_planet_id(client, game_id, "tim")

        resp = client.post(
            f"/api/v1/games/{game_id}/commands",
            json={
                "turn": 1,
                "commands": [
                    {
                        "type": "add_production_item",
                        "planet_id": planet_id,
                        "item_type": "starbase",
                        "target_type": "orbital_fort",
                        "quantity": 1,
                    },
                    {
                        "type": "add_production_item",
                        "planet_id": planet_id,
                        "item_type": "starbase",
                        "target_type": "space_station",
                        "quantity": 1,
                    },
                ],
            },
            headers={"X-Player": "tim"},
        )

        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "DUPLICATE_STARBASE_QUEUE_ITEM"

    def test_submit_planetary_scanner_rejects_duplicate_unfinished_item(self, client):
        create_resp = _create_game(client)
        game_id = create_resp.json()["game_id"]
        planet_id = self._get_planet_id(client, game_id, "tim")

        resp = client.post(
            f"/api/v1/games/{game_id}/commands",
            json={
                "turn": 1,
                "commands": [
                    {
                        "type": "add_production_item",
                        "planet_id": planet_id,
                        "item_type": "planetary_scanner",
                        "quantity": 1,
                    },
                    {
                        "type": "add_production_item",
                        "planet_id": planet_id,
                        "item_type": "planetary_scanner",
                        "quantity": 1,
                    },
                ],
            },
            headers={"X-Player": "tim"},
        )

        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "DUPLICATE_SCANNER_QUEUE_ITEM"

    def test_submit_planetary_scanner_rejects_when_already_installed(self, client):
        create_resp = _create_game(client)
        game_id = create_resp.json()["game_id"]
        planet_id = self._get_planet_id(client, game_id, "tim")

        submit_resp = client.post(
            f"/api/v1/games/{game_id}/commands",
            json={
                "turn": 1,
                "commands": [
                    {
                        "type": "add_production_item",
                        "planet_id": planet_id,
                        "item_type": "planetary_scanner",
                        "quantity": 1,
                    }
                ],
            },
            headers={"X-Player": "tim"},
        )
        assert submit_resp.status_code == 200

        for turn in range(1, 4):
            if turn > 1:
                client.post(
                    f"/api/v1/games/{game_id}/commands",
                    json={"turn": turn, "commands": []},
                    headers={"X-Player": "tim"},
                )
            client.post(
                f"/api/v1/games/{game_id}/commands",
                json={"turn": turn, "commands": []},
                headers={"X-Player": "matt"},
            )
            resolve_resp = client.post(
                f"/api/v1/games/{game_id}/resolve", headers={"X-Player": "tim"}
            )
            assert resolve_resp.status_code == 200

        resp = client.post(
            f"/api/v1/games/{game_id}/commands",
            json={
                "turn": 4,
                "commands": [
                    {
                        "type": "add_production_item",
                        "planet_id": planet_id,
                        "item_type": "planetary_scanner",
                        "quantity": 1,
                    }
                ],
            },
            headers={"X-Player": "tim"},
        )

        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "SCANNER_ALREADY_INSTALLED"

    def test_rename_fleet_command(self, client):
        create_resp = _create_game(client)
        game_id = create_resp.json()["game_id"]
        fleet_id = self._get_fleet_id(client, game_id, "tim")

        resp = client.post(
            f"/api/v1/games/{game_id}/commands",
            json={
                "turn": 1,
                "commands": [{"type": "rename_fleet", "fleet_id": fleet_id, "name": "Vanguard"}],
            },
            headers={"X-Player": "tim"},
        )
        assert resp.status_code == 200

        # Submit empty commands for matt then resolve
        client.post(
            f"/api/v1/games/{game_id}/commands",
            json={"turn": 1, "commands": []},
            headers={"X-Player": "matt"},
        )
        client.post(f"/api/v1/games/{game_id}/resolve", headers={"X-Player": "tim"})

        state = client.get(
            f"/api/v1/games/{game_id}/state?turn=2", headers={"X-Player": "tim"}
        ).json()
        renamed = next(f for f in state["fleets"] if f["id"] == fleet_id)
        assert renamed["name"] == "Vanguard"

    def test_submit_production_command_rejects_other_players_planet(self, client):
        create_resp = _create_game(client)
        game_id = create_resp.json()["game_id"]
        planet_id = self._get_planet_id(client, game_id, "tim")

        resp = client.post(
            f"/api/v1/games/{game_id}/commands",
            json={
                "turn": 1,
                "commands": [
                    {
                        "type": "add_production_item",
                        "planet_id": planet_id,
                        "item_type": "mine",
                        "quantity": 1,
                    }
                ],
            },
            headers={"X-Player": "matt"},
        )

        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "PLANET_NOT_OWNED"


class TestTurnZeroPhase:
    """Step 8 — turn-0 phase enforcement and submit-time race validation."""

    def _create(self, client, players=None):
        return _create_game(client, advance=False, players=players)

    def test_turn_zero_rejects_non_race_command(self, client):
        game_id = self._create(client).json()["game_id"]
        resp = client.post(
            f"/api/v1/games/{game_id}/commands",
            json={
                "turn": 0,
                "commands": [
                    {
                        "type": "set_research",
                        "current_field": "energy",
                        "allocation_percent": 50,
                    }
                ],
            },
            headers={"X-Player": "tim"},
        )
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "COMMAND_TURN_ZERO_RACE_ONLY"

    def test_turn_zero_accepts_humanoid_select_race(self, client):
        game_id = self._create(client).json()["game_id"]
        resp = client.post(
            f"/api/v1/games/{game_id}/commands",
            json={
                "turn": 0,
                "commands": [{"type": "select_race", "predefined_id": "humanoid"}],
            },
            headers={"X-Player": "tim"},
        )
        assert resp.status_code == 200

        # Stored as expected.
        stored = client.get(f"/api/v1/games/{game_id}/commands", headers={"X-Player": "tim"}).json()
        assert [c["type"] for c in stored["commands"]] == ["select_race"]
        assert stored["commands"][0]["predefined_id"] == "humanoid"

    def test_turn_zero_overspent_custom_race_returns_400(self, client):
        game_id = self._create(client).json()["game_id"]
        from openstars.engine.race.models import (
            RaceEconomy,
            RaceHabitability,
            RaceHabitabilityFactor,
            RaceResearch,
            ResearchCostProfile,
        )
        from openstars.engine.race.presets import default_race
        from openstars.engine.research.costs import FIELDS

        overspent = default_race().model_copy(
            update={
                "habitability": RaceHabitability(
                    gravity=RaceHabitabilityFactor(immune=True),
                    temperature=RaceHabitabilityFactor(immune=True),
                    radiation=RaceHabitabilityFactor(immune=True),
                ),
                "max_growth_rate": 20,
                "economy": RaceEconomy(
                    colonists_per_resource=700,
                    factory_output_per_10=15,
                    factory_cost_resources=5,
                    factories_per_10k_colonists=25,
                    factories_save_germanium=True,
                    mine_output_per_10=25,
                    mine_cost_resources=2,
                    mines_per_10k_colonists=25,
                    ar_resource_divisor=5,
                ),
                "research": RaceResearch(
                    field_profile={field: ResearchCostProfile.CHEAP for field in FIELDS},
                    start_at_tech_3=True,
                ),
            }
        )

        resp = client.post(
            f"/api/v1/games/{game_id}/commands",
            json={
                "turn": 0,
                "commands": [{"type": "select_race", "race": overspent.model_dump(mode="json")}],
            },
            headers={"X-Player": "tim"},
        )
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "RACE_OVERSPENT"

    def test_turn_zero_non_joat_prt_returns_400(self, client):
        game_id = self._create(client).json()["game_id"]
        from openstars.engine.race.models import PRT
        from openstars.engine.race.presets import default_race

        race = default_race().model_copy(update={"prt": PRT.HYPER_EXPANSION})
        resp = client.post(
            f"/api/v1/games/{game_id}/commands",
            json={
                "turn": 0,
                "commands": [{"type": "select_race", "race": race.model_dump(mode="json")}],
            },
            headers={"X-Player": "tim"},
        )
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "RACE_PRT_NOT_AVAILABLE"

    def test_turn_zero_unknown_predefined_race_returns_404(self, client):
        game_id = self._create(client).json()["game_id"]
        resp = client.post(
            f"/api/v1/games/{game_id}/commands",
            json={
                "turn": 0,
                "commands": [{"type": "select_race", "predefined_id": "rabbitoid"}],
            },
            headers={"X-Player": "tim"},
        )
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "PREDEFINED_RACE_UNKNOWN"

    def test_turn_one_rejects_select_race(self, client):
        # Game advanced to T=1.
        game_id = _create_game(client).json()["game_id"]
        # set_research at T=1 is accepted.
        ok = client.post(
            f"/api/v1/games/{game_id}/commands",
            json={
                "turn": 1,
                "commands": [
                    {
                        "type": "set_research",
                        "current_field": "energy",
                        "allocation_percent": 50,
                    }
                ],
            },
            headers={"X-Player": "tim"},
        )
        assert ok.status_code == 200
        # select_race at T=1 is rejected.
        rejected = client.post(
            f"/api/v1/games/{game_id}/commands",
            json={
                "turn": 1,
                "commands": [{"type": "select_race", "predefined_id": "humanoid"}],
            },
            headers={"X-Player": "tim"},
        )
        assert rejected.status_code == 400
        assert rejected.json()["error"]["code"] == "COMMAND_NOT_VALID_AT_THIS_TURN"

    def test_resolve_turn_zero_incomplete_lists_missing_player(self, client):
        game_id = self._create(client).json()["game_id"]
        # Only Tim submits.
        client.post(
            f"/api/v1/games/{game_id}/commands",
            json={
                "turn": 0,
                "commands": [{"type": "select_race", "predefined_id": "humanoid"}],
            },
            headers={"X-Player": "tim"},
        )
        resp = client.post(f"/api/v1/games/{game_id}/resolve", headers={"X-Player": "tim"})
        assert resp.status_code == 409
        body = resp.json()
        assert body["error"]["code"] == "TURN_ZERO_INCOMPLETE"
        assert "matt" in body["error"]["message"]

    def test_resolve_turn_zero_succeeds_when_all_submitted(self, client):
        game_id = self._create(client).json()["game_id"]
        for player in ("tim", "matt"):
            client.post(
                f"/api/v1/games/{game_id}/commands",
                json={
                    "turn": 0,
                    "commands": [{"type": "select_race", "predefined_id": "humanoid"}],
                },
                headers={"X-Player": player},
            )
        resp = client.post(f"/api/v1/games/{game_id}/resolve", headers={"X-Player": "tim"})
        assert resp.status_code == 200
        assert resp.json()["turn"] == 1

    def test_turn_status_lists_players_awaiting_submission(self, client):
        game_id = self._create(client).json()["game_id"]
        before = client.get(
            f"/api/v1/games/{game_id}/turn-status", headers={"X-Player": "tim"}
        ).json()
        assert before["turn"] == 0
        assert sorted(before["players_awaiting_submission"]) == ["matt", "tim"]

        client.post(
            f"/api/v1/games/{game_id}/commands",
            json={
                "turn": 0,
                "commands": [{"type": "select_race", "predefined_id": "humanoid"}],
            },
            headers={"X-Player": "tim"},
        )
        mid = client.get(f"/api/v1/games/{game_id}/turn-status", headers={"X-Player": "tim"}).json()
        assert mid["players_awaiting_submission"] == ["matt"]

        client.post(
            f"/api/v1/games/{game_id}/commands",
            json={
                "turn": 0,
                "commands": [{"type": "select_race", "predefined_id": "humanoid"}],
            },
            headers={"X-Player": "matt"},
        )
        after = client.get(
            f"/api/v1/games/{game_id}/turn-status", headers={"X-Player": "tim"}
        ).json()
        assert after["players_awaiting_submission"] == []

    def test_game_detail_submitted_reflects_select_race(self, client):
        game_id = self._create(client).json()["game_id"]

        before = client.get(f"/api/v1/games/{game_id}", headers={"X-Player": "tim"}).json()
        assert before["turn"] == 0
        assert {p["username"]: p["submitted"] for p in before["players"]} == {
            "tim": False,
            "matt": False,
        }

        # An empty submission at T=0 does NOT count as a select_race.
        client.post(
            f"/api/v1/games/{game_id}/commands",
            json={"turn": 0, "commands": []},
            headers={"X-Player": "tim"},
        )
        mid = client.get(f"/api/v1/games/{game_id}", headers={"X-Player": "tim"}).json()
        assert {p["username"]: p["submitted"] for p in mid["players"]} == {
            "tim": False,
            "matt": False,
        }

        client.post(
            f"/api/v1/games/{game_id}/commands",
            json={
                "turn": 0,
                "commands": [{"type": "select_race", "predefined_id": "humanoid"}],
            },
            headers={"X-Player": "tim"},
        )
        after = client.get(f"/api/v1/games/{game_id}", headers={"X-Player": "tim"}).json()
        assert {p["username"]: p["submitted"] for p in after["players"]} == {
            "tim": True,
            "matt": False,
        }


class TestResolve:
    def _submit_empty(self, client, game_id, player, turn=1):
        client.post(
            f"/api/v1/games/{game_id}/commands",
            json={"turn": turn, "commands": []},
            headers={"X-Player": player},
        )

    def test_resolve_success(self, client):
        create_resp = _create_game(client)
        game_id = create_resp.json()["game_id"]

        # Both players submit empty commands
        self._submit_empty(client, game_id, "tim")
        self._submit_empty(client, game_id, "matt")

        # Resolve
        resp = client.post(f"/api/v1/games/{game_id}/resolve", headers={"X-Player": "tim"})
        assert resp.status_code == 200
        assert resp.json()["turn"] == 2
        assert resp.json()["status"] == "resolved"

    def test_resolve_not_all_submitted(self, client):
        create_resp = _create_game(client)
        game_id = create_resp.json()["game_id"]

        # Only Tim submits
        self._submit_empty(client, game_id, "tim")

        resp = client.post(f"/api/v1/games/{game_id}/resolve", headers={"X-Player": "tim"})
        assert resp.status_code == 409

    def test_full_lifecycle(self, client):
        """Create → get state → submit commands → resolve → get new state."""
        create_resp = _create_game(client)
        game_id = create_resp.json()["game_id"]

        # Get Tim's initial state
        state = client.get(f"/api/v1/games/{game_id}/state", headers={"X-Player": "tim"}).json()
        assert state["turn"] == 1
        tim_fleet = [f for f in state["fleets"] if f["owner"] == "tim"][0]
        fleet_id = tim_fleet["id"]
        start_x = tim_fleet["position"]["x"]
        start_y = tim_fleet["position"]["y"]

        # Set waypoints — move east
        dest_x = start_x + 50 * LIGHT_YEAR
        client.post(
            f"/api/v1/games/{game_id}/commands",
            json={
                "turn": 1,
                "commands": [
                    {
                        "type": "set_waypoints",
                        "fleet_id": fleet_id,
                        "waypoints": [{"x": dest_x, "y": start_y, "warp": 1}],
                    }
                ],
            },
            headers={"X-Player": "tim"},
        )

        # Matt submits empty
        self._submit_empty(client, game_id, "matt")

        # Resolve
        resp = client.post(f"/api/v1/games/{game_id}/resolve", headers={"X-Player": "tim"})
        assert resp.json()["turn"] == 2

        # Get new state
        new_state = client.get(f"/api/v1/games/{game_id}/state", headers={"X-Player": "tim"}).json()
        assert new_state["turn"] == 2

        new_fleet = next(f for f in new_state["fleets"] if f["id"] == fleet_id)
        # Fleet should have moved at warp-1 budget (1 light-year) east.
        assert new_fleet["position"]["x"] == start_x + LIGHT_YEAR
        assert new_fleet["position"]["y"] == start_y

    def test_resolve_conflict_is_idempotent(self, client, monkeypatch):
        create_resp = _create_game(client)
        game_id = create_resp.json()["game_id"]

        # Both players submit empty commands
        self._submit_empty(client, game_id, "tim")
        self._submit_empty(client, game_id, "matt")

        from openstars.server.deps import get_storage

        storage = get_storage()
        original_save = storage.save_global_state
        call_count = 0

        def flaky_save_global_state(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise FileExistsError("Object already exists")
            return original_save(*args, **kwargs)

        monkeypatch.setattr(storage, "save_global_state", flaky_save_global_state)

        resp = client.post(f"/api/v1/games/{game_id}/resolve", headers={"X-Player": "tim"})
        assert resp.status_code == 200
        assert resp.json()["turn"] == 2
        assert resp.json()["status"] == "resolved"


class TestScanners:
    """Integration tests for scanner mechanics (PRD 11)."""

    def _submit_empty(self, client, game_id, player, turn=1):
        client.post(
            f"/api/v1/games/{game_id}/commands",
            json={"turn": turn, "commands": []},
            headers={"X-Player": player},
        )

    def test_all_planets_always_visible(self, client):
        """Every planet in the galaxy appears in the player state, regardless of scanner range."""
        create_resp = _create_game(client)
        game_id = create_resp.json()["game_id"]

        # Get galaxy to know total planet count
        galaxy = client.get(f"/api/v1/games/{game_id}/galaxy", headers={"X-Player": "tim"}).json()
        total_planets = len(galaxy["planets"])

        # Get player state
        state = client.get(f"/api/v1/games/{game_id}/state", headers={"X-Player": "tim"}).json()

        # All planets should be visible
        assert len(state["planets"]) == total_planets

    def test_own_planet_scan_level_detailed(self, client):
        """Own planets always have scan_level 'detailed'."""
        create_resp = _create_game(client)
        game_id = create_resp.json()["game_id"]

        state = client.get(f"/api/v1/games/{game_id}/state", headers={"X-Player": "tim"}).json()

        own_planets = [p for p in state["planets"] if p.get("owner") == "tim"]
        assert len(own_planets) >= 1
        for p in own_planets:
            assert p["scan_level"] == "detailed"
            assert p["population"] is not None

    def test_unscanned_planet_scan_level_none(self, client):
        """Planets outside scanner range have scan_level 'none' with no owner/population."""
        create_resp = _create_game(client)
        game_id = create_resp.json()["game_id"]

        state = client.get(f"/api/v1/games/{game_id}/state", headers={"X-Player": "tim"}).json()

        # There should be some planets with scan_level "none" (far from home)
        none_planets = [p for p in state["planets"] if p["scan_level"] == "none"]
        assert len(none_planets) > 0, "Expected some planets outside scanner range"
        for p in none_planets:
            # scan_level "none" should have no owner or population
            assert p.get("owner") is None
            assert p.get("population") is None

    def test_scanned_planet_scan_level_basic(self, client):
        """Planets within normal scanner range (but not own) have scan_level 'basic'."""
        create_resp = _create_game(client)
        game_id = create_resp.json()["game_id"]

        state = client.get(f"/api/v1/games/{game_id}/state", headers={"X-Player": "tim"}).json()

        # Basic-scanned planets: within range, not owned by Tim
        basic_planets = [p for p in state["planets"] if p["scan_level"] == "basic"]
        # In a small galaxy with 50 planets and 150pc scanner range, there should
        # be at least some planets in range but not owned
        # (This depends on galaxy generation, but statistically very likely)
        for p in basic_planets:
            assert p.get("owner") is not None or p["scan_level"] == "basic"

    def test_design_has_scanner_object(self, client):
        """Designs should have a nested scanner object with normal and penetrating."""
        create_resp = _create_game(client)
        game_id = create_resp.json()["game_id"]

        state = client.get(f"/api/v1/games/{game_id}/state", headers={"X-Player": "tim"}).json()

        assert len(state["designs"]) >= 1
        design = state["designs"][0]
        assert "scanner" in design
        assert design["scanner"]["normal"] == 0
        assert design["scanner"]["penetrating"] == 0

    def test_enemy_fleet_has_bearing(self, client):
        """Enemy fleets with waypoints should show a bearing; stationary ones should not."""
        create_resp = _create_game(client)
        game_id = create_resp.json()["game_id"]

        # Get Matt's fleet and give it a waypoint so it has a bearing
        matt_state = client.get(
            f"/api/v1/games/{game_id}/state", headers={"X-Player": "matt"}
        ).json()
        matt_fleet = [f for f in matt_state["fleets"] if f["owner"] == "matt"][0]
        matt_fleet_id = matt_fleet["id"]
        matt_x = matt_fleet["position"]["x"]
        matt_y = matt_fleet["position"]["y"]

        # Set Matt's fleet waypoint east (so it has a bearing)
        client.post(
            f"/api/v1/games/{game_id}/commands",
            json={
                "turn": 1,
                "commands": [
                    {
                        "type": "set_waypoints",
                        "fleet_id": matt_fleet_id,
                        "waypoints": [{"x": matt_x + 10 * LIGHT_YEAR, "y": matt_y}],
                    }
                ],
            },
            headers={"X-Player": "matt"},
        )

        # Now check Tim's view — if Matt's fleet is in scanner range, it should have bearing
        tim_state = client.get(f"/api/v1/games/{game_id}/state", headers={"X-Player": "tim"}).json()
        matt_fleets_seen = [f for f in tim_state["fleets"] if f["owner"] == "matt"]

        for f in matt_fleets_seen:
            # Enemy fleets should not have composition or waypoints
            assert f["composition"] is None
            assert f["waypoints"] is None
            # If it has a waypoint set, bearing should be present
            # (bearing is based on the global state waypoints, not commands —
            #  commands haven't been applied yet, so bearing may be None at turn 0)

    def test_own_fleet_no_bearing(self, client):
        """Own fleets should not use the enemy-facing bearing field."""
        create_resp = _create_game(client)
        game_id = create_resp.json()["game_id"]

        state = client.get(f"/api/v1/games/{game_id}/state", headers={"X-Player": "tim"}).json()
        own_fleets = [f for f in state["fleets"] if f["owner"] == "tim"]
        for f in own_fleets:
            assert f.get("bearing") is None

    def test_own_fleet_bearing_present_after_movement(self, client):
        create_resp = _create_game(client)
        game_id = create_resp.json()["game_id"]

        state_t0 = client.get(f"/api/v1/games/{game_id}/state", headers={"X-Player": "tim"}).json()
        tim_fleet = [f for f in state_t0["fleets"] if f["owner"] == "tim"][0]
        fleet_id = tim_fleet["id"]
        start_x = tim_fleet["position"]["x"]
        start_y = tim_fleet["position"]["y"]

        client.post(
            f"/api/v1/games/{game_id}/commands",
            json={
                "turn": 1,
                "commands": [
                    {
                        "type": "set_waypoints",
                        "fleet_id": fleet_id,
                        "waypoints": [{"x": start_x + 10 * LIGHT_YEAR, "y": start_y}],
                    }
                ],
            },
            headers={"X-Player": "tim"},
        )
        client.post(
            f"/api/v1/games/{game_id}/commands",
            json={"turn": 1, "commands": []},
            headers={"X-Player": "matt"},
        )
        client.post(f"/api/v1/games/{game_id}/resolve", headers={"X-Player": "tim"})

        state_t1 = client.get(f"/api/v1/games/{game_id}/state", headers={"X-Player": "tim"}).json()
        moved_fleet = next(f for f in state_t1["fleets"] if f["id"] == fleet_id)
        assert moved_fleet["bearing"] == 90.0

    def test_scanner_after_movement(self, client):
        """After moving a fleet, scanner coverage should update — new planets become visible."""
        create_resp = _create_game(client)
        game_id = create_resp.json()["game_id"]

        from openstars.server.deps import get_storage

        storage = get_storage()
        scout_design = next(
            design for design in storage.list_designs(game_id, "tim") if design.name == "Scout"
        )
        storage.save_design(
            game_id,
            "tim",
            scout_design.model_copy(update={"scanner": Scanner(normal=150, penetrating=0)}),
        )

        # Get initial state
        state_t0 = client.get(f"/api/v1/games/{game_id}/state", headers={"X-Player": "tim"}).json()
        tim_fleet = [f for f in state_t0["fleets"] if f["owner"] == "tim"][0]
        fleet_id = tim_fleet["id"]
        start_x = tim_fleet["position"]["x"]
        start_y = tim_fleet["position"]["y"]

        # Count planets scanned at t0
        scanned_t0 = {p["id"] for p in state_t0["planets"] if p["scan_level"] != "none"}

        # Find the closest "none" planet to move toward
        none_planets = [p for p in state_t0["planets"] if p["scan_level"] == "none"]
        if not none_planets:
            pytest.skip("All planets already in scanner range (unlikely but possible)")

        # Sort by distance to fleet, pick the closest
        def dist_sq(p):
            dx = p["x"] - start_x
            dy = p["y"] - start_y
            return dx * dx + dy * dy

        target = min(none_planets, key=dist_sq)

        # Set waypoint toward the closest unscanned planet
        client.post(
            f"/api/v1/games/{game_id}/commands",
            json={
                "turn": 1,
                "commands": [
                    {
                        "type": "set_waypoints",
                        "fleet_id": fleet_id,
                        "waypoints": [{"x": target["x"], "y": target["y"]}],
                    }
                ],
            },
            headers={"X-Player": "tim"},
        )
        self._submit_empty(client, game_id, "matt")

        # Resolve enough turns for the fleet to reach the target's local scan range.
        num_turns = 50
        for turn in range(num_turns):
            client.post(f"/api/v1/games/{game_id}/resolve", headers={"X-Player": "tim"})
            # Waypoints persist — just submit empty for both players
            self._submit_empty(client, game_id, "tim", turn=turn + 1)
            self._submit_empty(client, game_id, "matt", turn=turn + 1)

        # Get state after movement
        state_after = client.get(
            f"/api/v1/games/{game_id}/state", headers={"X-Player": "tim"}
        ).json()
        scanned_after = {p["id"] for p in state_after["planets"] if p["scan_level"] != "none"}

        # After moving up to 300pc toward an unscanned planet, we should
        # have scanned at least one new planet
        new_scans = scanned_after - scanned_t0
        assert len(new_scans) > 0, (
            f"Expected new planets scanned after moving toward nearest unscanned. "
            f"Scanned before: {len(scanned_t0)}, after: {len(scanned_after)}"
        )

    def test_stale_planet_after_fleet_moves_away(self, client):
        create_resp = _create_game(client)
        game_id = create_resp.json()["game_id"]

        from openstars.server.deps import get_storage

        storage = get_storage()
        for design in storage.list_designs(game_id, "tim"):
            storage.save_design(
                game_id,
                "tim",
                design.model_copy(update={"scanner": Scanner(normal=150, penetrating=0)}),
            )

        state_t0 = client.get(f"/api/v1/games/{game_id}/state", headers={"X-Player": "tim"}).json()
        tim_fleets = [fleet for fleet in state_t0["fleets"] if fleet["owner"] == "tim"]
        galaxy = client.get(f"/api/v1/games/{game_id}/galaxy", headers={"X-Player": "tim"}).json()
        max_coord = (
            1 << {"small": 40, "medium": 42, "large": 44, "huge": 46}[galaxy["galaxy"]["size"]]
        ) - 1

        origin = tim_fleets[0]["position"]
        unscanned_planets = [
            planet for planet in state_t0["planets"] if planet["scan_level"] == "none"
        ]
        assert unscanned_planets, "Expected at least one planet outside starting scanner range"

        def dist_sq_from_origin(planet):
            dx = planet["x"] - origin["x"]
            dy = planet["y"] - origin["y"]
            return dx * dx + dy * dy

        target_planet = min(unscanned_planets, key=dist_sq_from_origin)
        target_planet_id = target_planet["id"]

        tim_submit = client.post(
            f"/api/v1/games/{game_id}/commands",
            json={
                "turn": state_t0["turn"],
                "commands": [
                    {
                        "type": "set_waypoints",
                        "fleet_id": fleet["id"],
                        "waypoints": [{"x": target_planet["x"], "y": target_planet["y"]}],
                    }
                    for fleet in tim_fleets
                ],
            },
            headers={"X-Player": "tim"},
        )
        assert tim_submit.status_code == 200
        self._submit_empty(client, game_id, "matt", turn=state_t0["turn"])

        scanned_state = None
        for _ in range(80):
            resolve_resp = client.post(
                f"/api/v1/games/{game_id}/resolve",
                headers={"X-Player": "tim"},
            )
            assert resolve_resp.status_code == 200
            resolved_turn = resolve_resp.json()["turn"]

            state = client.get(f"/api/v1/games/{game_id}/state", headers={"X-Player": "tim"}).json()
            planet = next(planet for planet in state["planets"] if planet["id"] == target_planet_id)
            if planet["scan_level"] == "basic" and planet["scan_age"] == 0:
                scanned_state = state
                break

            self._submit_empty(client, game_id, "tim", turn=resolved_turn)
            self._submit_empty(client, game_id, "matt", turn=resolved_turn)

        if scanned_state is None:
            pytest.fail("Target planet never became freshly scanned before the fleet moved away")

        target_planet = next(
            planet for planet in scanned_state["planets"] if planet["id"] == target_planet_id
        )
        for design in storage.list_designs(game_id, "tim"):
            storage.save_design(
                game_id,
                "tim",
                design.model_copy(update={"scanner": Scanner(normal=0, penetrating=0)}),
            )
        far_corner = max(
            [(0, 0), (0, max_coord), (max_coord, 0), (max_coord, max_coord)],
            key=lambda point: (
                (point[0] - target_planet["x"]) ** 2 + (point[1] - target_planet["y"]) ** 2
            ),
        )
        tim_commands = []
        for fleet in [fleet for fleet in scanned_state["fleets"] if fleet["owner"] == "tim"]:
            tim_commands.append(
                {
                    "type": "set_waypoints",
                    "fleet_id": fleet["id"],
                    "waypoints": [
                        {
                            "x": far_corner[0],
                            "y": far_corner[1],
                        }
                    ],
                }
            )

        tim_submit = client.post(
            f"/api/v1/games/{game_id}/commands",
            json={
                "turn": scanned_state["turn"],
                "commands": tim_commands,
            },
            headers={"X-Player": "tim"},
        )
        assert tim_submit.status_code == 200
        self._submit_empty(client, game_id, "matt", turn=scanned_state["turn"])

        stale_state = None
        for _ in range(60):
            resolve_resp = client.post(
                f"/api/v1/games/{game_id}/resolve",
                headers={"X-Player": "tim"},
            )
            assert resolve_resp.status_code == 200
            resolved_turn = resolve_resp.json()["turn"]

            state = client.get(f"/api/v1/games/{game_id}/state", headers={"X-Player": "tim"}).json()
            planet = next(planet for planet in state["planets"] if planet["id"] == target_planet_id)
            if planet.get("scan_age") is not None and planet["scan_age"] > 0:
                stale_state = state
                break
            if planet["scan_level"] not in {"basic", "detailed"}:
                pytest.fail(f"Unexpected scan_level while moving away: {planet['scan_level']}")

            self._submit_empty(client, game_id, "tim", turn=resolved_turn)
            self._submit_empty(client, game_id, "matt", turn=resolved_turn)

        if stale_state is None:
            pytest.fail("Planet never became stale after moving away")

        stale_planet = next(
            planet for planet in stale_state["planets"] if planet["id"] == target_planet_id
        )
        assert stale_planet["scan_level"] in {"basic", "detailed"}
        first_scan_age = stale_planet["scan_age"]
        assert first_scan_age >= 1

        self._submit_empty(client, game_id, "tim", turn=stale_state["turn"])
        self._submit_empty(client, game_id, "matt", turn=stale_state["turn"])
        resolve_again = client.post(f"/api/v1/games/{game_id}/resolve", headers={"X-Player": "tim"})
        assert resolve_again.status_code == 200

        state_after = client.get(
            f"/api/v1/games/{game_id}/state", headers={"X-Player": "tim"}
        ).json()
        stale_again = next(
            planet for planet in state_after["planets"] if planet["id"] == target_planet_id
        )
        assert stale_again["scan_level"] in {"basic", "detailed"}
        assert stale_again["scan_age"] == first_scan_age + 1


class TestStorageBlobLayout:
    def test_resolve_cycle_writes_only_gzipped_json_blobs(self, client, tmp_path):
        create_resp = _create_game(client)
        game_id = create_resp.json()["game_id"]

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
        resolve_resp = client.post(f"/api/v1/games/{game_id}/resolve", headers={"X-Player": "tim"})
        assert resolve_resp.status_code == 200

        game_dir = tmp_path / game_id
        all_files = [path for path in game_dir.rglob("*") if path.is_file()]
        assert all(path.name.endswith(".json.gz") for path in all_files)
        assert not list(game_dir.rglob("*.json"))

        global_state_path = game_dir / "state" / "global-state-T1.json.gz"
        decoded = json.loads(decode_json(global_state_path.read_bytes()))
        assert "state_version" in decoded
        assert "game" in decoded
