"""Tests for the GCS storage adapter."""

import pytest

from openstars.engine.models import (
    Design,
    Fleet,
    FleetComposition,
    Galaxy,
    GalaxyMetadata,
    GameMeta,
    GlobalState,
    PlanetState,
    Player,
    PlayerCommands,
    PlayerState,
    Position,
    Scanner,
    SetWaypointsCommand,
)
from openstars.storage import gcs as gcs_module
from openstars.storage.gcs import GCSStorage


class FakeNotFound(Exception):
    pass


class FakePreconditionFailed(Exception):
    pass


class FakeBlobInfo:
    def __init__(self, name: str) -> None:
        self.name = name


class FakeBlob:
    def __init__(self, bucket, name: str) -> None:
        self.bucket = bucket
        self.name = name

    def upload_from_string(self, data: str, content_type: str, if_generation_match=None) -> None:
        existing = self.bucket.objects.get(self.name)
        if if_generation_match == 0 and existing is not None:
            raise FakePreconditionFailed(self.name)
        generation = 1 if existing is None else existing["generation"] + 1
        self.bucket.objects[self.name] = {
            "data": data,
            "content_type": content_type,
            "generation": generation,
        }

    def download_as_text(self) -> str:
        if self.name not in self.bucket.objects:
            raise FakeNotFound(self.name)
        return self.bucket.objects[self.name]["data"]

    def exists(self) -> bool:
        return self.name in self.bucket.objects


class FakeBucket:
    def __init__(self, name: str) -> None:
        self.name = name
        self.objects: dict[str, dict] = {}

    def blob(self, name: str) -> FakeBlob:
        return FakeBlob(self, name)


class FakeClient:
    buckets: dict[str, FakeBucket] = {}

    def bucket(self, name: str) -> FakeBucket:
        bucket = self.buckets.get(name)
        if bucket is None:
            bucket = FakeBucket(name)
            self.buckets[name] = bucket
        return bucket

    def list_blobs(self, bucket_name: str):
        bucket = self.bucket(bucket_name)
        return [FakeBlobInfo(name) for name in sorted(bucket.objects)]


@pytest.fixture(autouse=True)
def fake_gcs(monkeypatch):
    FakeClient.buckets = {}
    fake_storage_module = type("FakeStorageModule", (), {"Client": FakeClient})
    monkeypatch.setattr(gcs_module, "gcs_storage", fake_storage_module)
    monkeypatch.setattr(gcs_module, "NotFound", FakeNotFound)
    monkeypatch.setattr(gcs_module, "PreconditionFailed", FakePreconditionFailed)


@pytest.fixture
def storage():
    return GCSStorage("test-bucket")


@pytest.fixture
def sample_galaxy():
    return Galaxy(
        galaxy=GalaxyMetadata(name="Test Galaxy", size="small", seed=42),
        planets=[],
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


def test_global_state_create_only(storage, sample_global_state):
    storage.save_global_state("game1", 0, sample_global_state)

    with pytest.raises(FileExistsError):
        storage.save_global_state("game1", 0, sample_global_state)


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
    storage.save_galaxy("game1", sample_galaxy)
    storage.save_game_meta("game1", {"name": "Game 1"})
    storage.save_galaxy("game2", sample_galaxy)
    storage.save_game_meta("game2", {"name": "Game 2"})
    storage._write_json("nested/game3/meta.json", "{}")

    assert storage.list_games() == ["game1", "game2"]


def test_game_meta_round_trip(storage):
    meta = {"name": "Test Game", "galaxy_size": "small", "players": ["tim", "matt"]}
    storage.save_game_meta("game1", meta)

    loaded = storage.load_game_meta("game1")

    assert loaded == meta


def test_load_missing_file_raises(storage):
    with pytest.raises(FileNotFoundError):
        storage.load_galaxy("nonexistent")


def test_rejects_unsafe_username(storage, sample_commands):
    with pytest.raises(ValueError, match="Unsafe username"):
        storage.save_commands("game1", "../tim", 0, sample_commands)
