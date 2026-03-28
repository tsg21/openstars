"""Tests for local storage — write/read round-trips."""

import pytest

from openstars.engine.models import (
    Design,
    Fleet,
    FleetComposition,
    Galaxy,
    GalaxyMetadata,
    GalaxyPlanet,
    GameMeta,
    GlobalState,
    PlanetState,
    Player,
    PlayerCommands,
    PlayerState,
    Position,
    SetWaypointsCommand,
)
from openstars.storage.local import LocalStorage


@pytest.fixture
def storage(tmp_path):
    return LocalStorage(tmp_path)


@pytest.fixture
def sample_galaxy():
    return Galaxy(
        galaxy=GalaxyMetadata(name="Test Galaxy", size="small", seed=42),
        planets=[
            GalaxyPlanet(id="PLabc123", name="Sol", x=549755813888, y=549755813888),
            GalaxyPlanet(id="PLdef456", name="Alpha Centauri", x=550148141952, y=549755867136),
        ],
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
                scanner_range=150,
            )
        ],
        planets=[PlanetState(id="PLabc123", owner="tim", population=25000)],
        fleets=[
            Fleet(
                id="FLabc123",
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
                waypoints=[Position(x=550148141952, y=549755867136)],
            )
        ]
    )


def test_galaxy_round_trip(storage, sample_galaxy):
    storage.save_galaxy("game1", sample_galaxy)
    loaded = storage.load_galaxy("game1")
    assert loaded == sample_galaxy


def test_global_state_round_trip(storage, sample_global_state):
    storage.save_global_state("game1", 0, sample_global_state)
    loaded = storage.load_global_state("game1", 0)
    assert loaded == sample_global_state


def test_player_state_round_trip(storage, sample_player_state):
    storage.save_player_state("game1", "tim", 0, sample_player_state)
    loaded = storage.load_player_state("game1", "tim", 0)
    assert loaded == sample_player_state


def test_commands_round_trip(storage, sample_commands):
    storage.save_commands("game1", "tim", 0, sample_commands)
    loaded = storage.load_commands("game1", "tim", 0)
    assert loaded == sample_commands


def test_has_commands(storage, sample_commands):
    assert not storage.has_commands("game1", "tim", 0)
    storage.save_commands("game1", "tim", 0, sample_commands)
    assert storage.has_commands("game1", "tim", 0)


def test_list_games(storage, sample_galaxy):
    assert storage.list_games() == []
    storage.save_galaxy("game1", sample_galaxy)
    storage.save_game_meta("game1", {"name": "Game 1"})
    storage.save_galaxy("game2", sample_galaxy)
    storage.save_game_meta("game2", {"name": "Game 2"})
    assert storage.list_games() == ["game1", "game2"]


def test_game_meta_round_trip(storage):
    meta = {"name": "Test Game", "galaxy_size": "small", "players": ["tim", "matt"]}
    storage.save_game_meta("game1", meta)
    loaded = storage.load_game_meta("game1")
    assert loaded == meta


def test_load_missing_file_raises(storage):
    with pytest.raises(FileNotFoundError):
        storage.load_galaxy("nonexistent")
