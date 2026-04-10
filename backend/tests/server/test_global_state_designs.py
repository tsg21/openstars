"""Design registry helpers and legacy global-state payload handling."""

import os

import pytest
from fastapi.testclient import TestClient

from openstars.engine.models import Design, DesignCost, GlobalState, Minerals, Scanner
from openstars.server.game_designs import list_all_designs_for_players
from openstars.storage.state_versioning import upgrade_global_state_payload


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


def test_upgrade_global_state_payload_strips_legacy_designs():
    payload = {
        "state_version": 1,
        "game": {"seed": 1, "turn": 0, "next_id": 1},
        "players": [],
        "designs": [{"id": "DE1", "bogus": True}],
        "planets": [],
        "fleets": [],
    }
    upgraded = upgrade_global_state_payload(payload)
    assert "designs" not in upgraded
    GlobalState.model_validate(upgraded)


def test_list_all_designs_for_players_merges_registry(client):
    from openstars.server.deps import get_storage

    create = client.post(
        "/api/v1/games",
        json={
            "name": "Design list game",
            "galaxy_size": "small",
            "players": ["tim"],
        },
    )
    assert create.status_code == 201
    game_id = create.json()["game_id"]

    storage = get_storage()
    extra = Design(
        id="DEXTRA01",
        owner="tim",
        name="Extra",
        hull="scout",
        mass=12,
        fuel_usage=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        fuel_capacity=100,
        scanner=Scanner(normal=0, penetrating=0),
        cargo_capacity=0,
        cost=DesignCost(resources=1, minerals=Minerals()),
    )
    storage.save_design(game_id, "tim", extra)

    merged = list_all_designs_for_players(storage, game_id, ["tim"])
    assert any(d.id == "DEXTRA01" for d in merged)
