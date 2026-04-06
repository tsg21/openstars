"""Tests for in-memory storage adapter."""

import json

import pytest

from openstars.engine.models import (
    Design,
    DesignCost,
    Fleet,
    FleetComposition,
    Galaxy,
    GalaxyMetadata,
    GalaxyPlanet,
    GameMeta,
    GlobalState,
    Minerals,
    PlanetState,
    Player,
    PlayerCommands,
    PlayerState,
    Position,
    Scanner,
    SetWaypointsCommand,
    Waypoint,
)
from openstars.storage.memory import MemoryStorage
from openstars.storage.state_versioning import UnsupportedStateVersionError


@pytest.fixture
def storage():
    return MemoryStorage()


@pytest.fixture
def sample_galaxy():
    return Galaxy(
        galaxy=GalaxyMetadata(name="Test Galaxy", size="small", seed=42),
        planets=[GalaxyPlanet(id="PLabc123", name="Sol", x=549755813888, y=549755813888)],
    )


@pytest.fixture
def sample_global_state():
    return GlobalState(
        game=GameMeta(seed=42, turn=0, next_id=10),
        players=[Player(username="tim", name="Tim's Empire")],
        designs=[
            Design(
                id="DEabc123",
                owner="tim",
                name="Scout",
                hull="scout",
                speed=6,
                scanner=Scanner(normal=150, penetrating=0),
                cost=DesignCost(resources=10, minerals=Minerals()),
            )
        ],
        planets=[PlanetState(id="PLabc123", owner="tim", population=25000)],
        fleets=[
            Fleet(
                id="FLabc123",
                name="Fleet #1",
                owner="tim",
                position=Position(x=549755813888, y=549755813888),
                composition=[FleetComposition(design_id="DEabc123", count=1)],
                waypoints=[],
            )
        ],
    )


@pytest.fixture
def sample_player_state():
    return PlayerState(
        player="tim",
        turn=0,
        planets=[],
        fleets=[],
        designs=[],
        events=[],
    )


@pytest.fixture
def sample_commands():
    return PlayerCommands(
        commands=[
            SetWaypointsCommand(
                fleet_id="FLabc123",
                waypoints=[Waypoint(x=550148141952, y=549755867136)],
            )
        ]
    )


def test_round_trips(
    storage, sample_galaxy, sample_global_state, sample_player_state, sample_commands
):
    storage.save_galaxy("game1", sample_galaxy)
    storage.save_global_state("game1", 0, sample_global_state)
    storage.save_player_state("game1", "tim", 0, sample_player_state)
    storage.save_commands("game1", "tim", 0, sample_commands)

    assert storage.load_galaxy("game1") == sample_galaxy
    assert storage.load_global_state("game1", 0) == sample_global_state
    assert storage.load_player_state("game1", "tim", 0) == sample_player_state
    assert storage.load_commands("game1", "tim", 0) == sample_commands


def test_saved_state_blobs_include_root_state_version(
    storage, sample_global_state, sample_player_state
):
    storage.save_global_state("game1", 0, sample_global_state)
    storage.save_player_state("game1", "tim", 0, sample_player_state)

    global_state_payload = json.loads(storage._objects["game1/state/global-state-T0.json"])
    player_state_payload = json.loads(storage._objects["game1/players/player-state-tim-T0.json"])

    assert global_state_payload["state_version"] == 1
    assert player_state_payload["state_version"] == 1


def test_load_global_state_rejects_missing_state_version(storage):
    storage._objects["game1/state/global-state-T0.json"] = json.dumps(
        {"game": {"seed": 1, "turn": 0, "next_id": 1}}
    )

    with pytest.raises(UnsupportedStateVersionError, match="missing required state_version"):
        storage.load_global_state("game1", 0)


def test_load_player_state_rejects_newer_state_version(storage):
    storage._objects["game1/players/player-state-tim-T0.json"] = json.dumps(
        {
            "state_version": 999,
            "player": "tim",
            "turn": 0,
            "planets": [],
            "fleets": [],
            "designs": [],
            "events": [],
        }
    )

    with pytest.raises(UnsupportedStateVersionError, match="newer than supported version"):
        storage.load_player_state("game1", "tim", 0)


def test_has_commands(storage, sample_commands):
    assert not storage.has_commands("game1", "tim", 0)

    storage.save_commands("game1", "tim", 0, sample_commands)

    assert storage.has_commands("game1", "tim", 0)


def test_list_games_and_meta(storage):
    storage.save_game_meta("game1", {"name": "Game 1"})
    storage.save_game_meta("game2", {"name": "Game 2"})

    assert storage.list_games() == ["game1", "game2"]
    assert storage.load_game_meta("game1") == {"name": "Game 1"}


def test_missing_object_raises(storage):
    with pytest.raises(FileNotFoundError):
        storage.load_galaxy("missing")


def test_rejects_unsafe_username(storage, sample_commands):
    with pytest.raises(ValueError, match="Unsafe username"):
        storage.save_commands("game1", "../tim", 0, sample_commands)
