"""Server tests for first-pass designer APIs."""

import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _setup_storage(tmp_path):
    os.environ["STORAGE_BACKEND"] = "local"
    os.environ["GAME_DATA_PATH"] = str(tmp_path)
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


def _create_game(client):
    response = client.post(
        "/api/v1/games",
        json={"name": "Designer Game", "galaxy_size": "small", "players": ["tim", "matt"]},
    )
    assert response.status_code == 201
    return response.json()["game_id"]


def _valid_create_payload() -> dict:
    return {
        "name": "Long Range Scout",
        "hull": "scout",
        "components": [
            {
                "slot_number": 1,
                "component_id": "trans_galactic_drive",
                "component_count": 1,
            },
            {
                "slot_number": 2,
                "component_id": "rhino_scanner",
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
    assert any(component["id"] == "trans_galactic_drive" for component in body["components"])


def test_create_validation_failures(client):
    game_id = _create_game(client)
    # Missing required engine slot.
    invalid_payload = {
        "name": "Broken Scout",
        "hull": "scout",
        "components": [
            {
                "slot_number": 2,
                "component_id": "rhino_scanner",
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
    incompatible_payload["components"][1]["component_id"] = "laser_mk1"
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
    assert created_design["scanner"]["normal"] == 120
    assert created_design["cost"]["resources"] > 0

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
    assert detail_body["design"]["scanner"]["normal"] == 120
    assert detail_body["design"]["cargo_capacity"] == 0
