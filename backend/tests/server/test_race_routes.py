import os

import pytest
from fastapi.testclient import TestClient

from openstars.engine.race.models import (
    PRT,
    Race,
    RaceEconomy,
    RaceHabitability,
    RaceHabitabilityFactor,
    RaceResearch,
    ResearchCostProfile,
)
from openstars.engine.race.presets import default_race
from openstars.engine.research.costs import FIELDS


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


def _create_game(client: TestClient, players: list[str] | None = None) -> str:
    if players is None:
        players = ["tim", "matt"]
    response = client.post(
        "/api/v1/games",
        json={"name": "Race Game", "galaxy_size": "small", "players": players},
    )
    assert response.status_code == 201
    return response.json()["game_id"]


def _valid_custom_race() -> Race:
    return default_race().model_copy(
        update={
            "name": "Custom",
            "plural_name": "Customs",
            "emblem": 1,
            "max_growth_rate": 14,
        }
    )


def _overspent_race() -> Race:
    return default_race().model_copy(
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


def test_race_preview_returns_cost_breakdown_without_persisting(client: TestClient) -> None:
    race = _valid_custom_race()

    response = client.post(
        "/api/v1/race/preview",
        json={"race": race.model_dump(mode="json")},
        headers={"X-Player": "tim"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["points_left"] > 0


def test_race_preview_overspent_race_returns_negative_cost_breakdown(client: TestClient) -> None:
    response = client.post(
        "/api/v1/race/preview",
        json={"race": _overspent_race().model_dump(mode="json")},
        headers={"X-Player": "tim"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["points_left"] < 0


def test_race_preview_unavailable_prt_returns_cost_breakdown(client: TestClient) -> None:
    race = default_race().model_copy(update={"prt": PRT.SPACE_DEMOLITION})

    response = client.post(
        "/api/v1/race/preview",
        json={"race": race.model_dump(mode="json")},
        headers={"X-Player": "tim"},
    )

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body["prt"], int)


def test_get_game_race_returns_null_then_saved_selection(client: TestClient) -> None:
    game_id = _create_game(client)

    before = client.get(f"/api/v1/games/{game_id}/race", headers={"X-Player": "tim"})
    assert before.status_code == 200
    assert before.json() == {"race": None, "cost_breakdown": None}

    submit = client.post(
        f"/api/v1/games/{game_id}/commands",
        json={"turn": 0, "commands": [{"type": "select_race", "predefined_id": "humanoid"}]},
        headers={"X-Player": "tim"},
    )
    assert submit.status_code == 200

    after = client.get(f"/api/v1/games/{game_id}/race", headers={"X-Player": "tim"})
    assert after.status_code == 200
    body = after.json()
    assert body["race"]["name"] == "Humanoid"
    assert body["cost_breakdown"]["total"] == 28  # JOAT PRT cost


def test_get_game_race_rejects_non_player(client: TestClient) -> None:
    game_id = _create_game(client, players=["tim"])

    response = client.get(f"/api/v1/games/{game_id}/race", headers={"X-Player": "matt"})

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "NOT_PLAYER"


def test_predefined_races_returns_humanoid_only(client: TestClient) -> None:
    response = client.get("/api/v1/race/predefined")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": "humanoid",
            "race": default_race().model_dump(mode="json"),
        }
    ]
