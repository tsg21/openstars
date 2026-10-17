"""Server tests for first-pass designer APIs."""

import os

import pytest

from openstars.engine.race.models import LRT
from openstars.engine.race.presets import default_race
from openstars.engine.research.costs import FIELDS
from openstars.server.deps import get_game_directory, get_storage


@pytest.fixture(autouse=True)
def _setup_storage(tmp_path):
    os.environ["STORAGE_BACKEND"] = "local"
    os.environ["GAME_DATA_PATH"] = str(tmp_path)
    os.environ["GAME_DIRECTORY_BACKEND"] = "memory"
    from openstars.server.deps import get_game_directory, get_storage

    get_storage.cache_clear()
    get_game_directory.cache_clear()
    yield
    os.environ.pop("STORAGE_BACKEND", None)
    os.environ.pop("GAME_DATA_PATH", None)
    os.environ.pop("GAME_DIRECTORY_BACKEND", None)
    get_storage.cache_clear()
    get_game_directory.cache_clear()


def _create_game(client):
    response = client.post(
        "/api/v1/games",
        json={"name": "Designer Game", "galaxy_size": "small", "players": ["tim", "matt"]},
        headers={"X-Player": "tim"},
    )
    assert response.status_code == 201
    return response.json()["game_id"]


def _set_player_catalogue_context(game_id: str, username: str, *, tech_level: int, lrts=()) -> None:
    storage = get_storage()
    turn = get_game_directory().get_game(game_id).current_turn
    state = storage.load_global_state(game_id, turn)
    player = next(player for player in state.players if player.username == username)
    player.research_state.levels = {field: tech_level for field in FIELDS}
    player.race = default_race().model_copy(update={"lrts": frozenset(lrts)})
    storage.update_global_state(game_id, turn, state)


def _valid_create_payload() -> dict:
    return {
        "name": "Long Range Scout",
        "hull": "scout",
        "components": [
            {
                "slot_number": 1,
                "component_id": "quick_jump_5",
                "component_count": 1,
            },
            {
                "slot_number": 2,
                "component_id": "bat_scanner",
                "component_count": 1,
            },
        ],
    }


def test_reference_data_fetch(client):
    game_id = _create_game(client)
    response = client.get(
        f"/api/v1/games/{game_id}/designs/reference-data?domain=ship",
        headers={"X-Player": "tim"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["domain"] == "ship"
    assert any(hull["id"] == "scout" for hull in body["hulls"])
    assert any(component["id"] == "quick_jump_5" for component in body["components"])
    assert any(component["id"] == "bat_scanner" for component in body["components"])
    assert not any(component["id"] == "trans_galactic_drive" for component in body["components"])
    assert not any(component["id"] == "rhino_scanner" for component in body["components"])


def test_reference_data_filters_prt_lrt_and_tech_requirements(client):
    game_id = _create_game(client)
    _set_player_catalogue_context(game_id, "tim", tech_level=26)

    response = client.get(
        f"/api/v1/games/{game_id}/designs/reference-data?domain=ship",
        headers={"X-Player": "tim"},
    )
    assert response.status_code == 200
    component_ids = {component["id"] for component in response.json()["components"]}
    hull_ids = {hull["id"] for hull in response.json()["hulls"]}
    assert "trans_galactic_drive" in component_ids
    assert "fuel_mizer" not in component_ids
    assert "mini_colony_ship" not in hull_ids

    _set_player_catalogue_context(
        game_id,
        "tim",
        tech_level=26,
        lrts=(LRT.IMPROVED_FUEL_EFFICIENCY,),
    )
    response = client.get(
        f"/api/v1/games/{game_id}/designs/reference-data?domain=ship",
        headers={"X-Player": "tim"},
    )
    assert response.status_code == 200
    component_ids = {component["id"] for component in response.json()["components"]}
    assert "fuel_mizer" in component_ids


def test_reference_data_fetch_starbase_domain(client):
    game_id = _create_game(client)
    response = client.get(
        f"/api/v1/games/{game_id}/designs/reference-data?domain=starbase",
        headers={"X-Player": "tim"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["domain"] == "starbase"
    assert body["hulls"]
    assert all(hull["hull"]["domain"] == "starbase" for hull in body["hulls"])
    assert any(hull["id"] == "orbital_fort" for hull in body["hulls"])


def test_reference_data_invalid_domain(client):
    game_id = _create_game(client)
    response = client.get(
        f"/api/v1/games/{game_id}/designs/reference-data?domain=invalid",
        headers={"X-Player": "tim"},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "UNSUPPORTED_DOMAIN"


def test_create_validation_failures(client):
    game_id = _create_game(client)
    # Missing required engine slot.
    invalid_payload = {
        "name": "Broken Scout",
        "hull": "scout",
        "components": [
            {
                "slot_number": 2,
                "component_id": "bat_scanner",
                "component_count": 1,
            }
        ],
    }
    response = client.post(
        f"/api/v1/games/{game_id}/designs",
        json=invalid_payload,
        headers={"X-Player": "tim"},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "REQUIRED_SLOT_MISSING"

    # Incompatible slot assignment.
    incompatible_payload = _valid_create_payload()
    incompatible_payload["components"][1]["component_id"] = "laser"
    response = client.post(
        f"/api/v1/games/{game_id}/designs",
        json=incompatible_payload,
        headers={"X-Player": "tim"},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "SLOT_INCOMPATIBLE_COMPONENT"

    # component_count exceeds slot capacity.
    too_many_payload = _valid_create_payload()
    too_many_payload["components"][0]["component_count"] = 2
    response = client.post(
        f"/api/v1/games/{game_id}/designs",
        json=too_many_payload,
        headers={"X-Player": "tim"},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "COMPONENT_COUNT_EXCEEDS_SLOT_CAPACITY"


def test_successful_design_creation_and_detail_shape(client):
    game_id = _create_game(client)
    create_response = client.post(
        f"/api/v1/games/{game_id}/designs",
        json=_valid_create_payload(),
        headers={"X-Player": "tim"},
    )
    assert create_response.status_code == 201
    created_design = create_response.json()["design"]
    assert created_design["owner"] == "tim"
    assert created_design["hull"] == "scout"
    assert created_design["fuel_capacity"] == 50
    assert created_design["scanner"]["normal"] == 0
    assert created_design["cost"]["resources"] > 0
    assert created_design["components"] == [
        {"slot_number": 1, "component_id": "quick_jump_5", "component_count": 1},
        {"slot_number": 2, "component_id": "bat_scanner", "component_count": 1},
    ]

    list_response = client.get(f"/api/v1/games/{game_id}/designs", headers={"X-Player": "tim"})
    assert list_response.status_code == 200
    list_body = list_response.json()
    assert "designs" in list_body
    assert any(item["id"] == created_design["id"] for item in list_body["designs"])
    listed_item = next(item for item in list_body["designs"] if item["id"] == created_design["id"])
    assert set(listed_item.keys()) == {"id", "name", "hull", "fuel_capacity", "cost"}

    detail_response = client.get(
        f"/api/v1/games/{game_id}/designs/{created_design['id']}",
        headers={"X-Player": "tim"},
    )
    assert detail_response.status_code == 200
    detail_body = detail_response.json()
    assert detail_body["design"]["id"] == created_design["id"]
    assert detail_body["design"]["scanner"]["normal"] == 0
    assert detail_body["design"]["cargo_capacity"] == 0
    assert detail_body["design"]["components"] == created_design["components"]
