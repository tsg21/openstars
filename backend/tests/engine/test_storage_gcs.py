"""Tests for the GCS storage adapter."""

import json

import pytest

from openstars.combat.altair.models import AltairCombatConfig, BattleEndEvent, CombatLog
from openstars.engine.models import (
    Design,
    DesignCost,
    Fleet,
    FleetComposition,
    Galaxy,
    GalaxyMetadata,
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
from openstars.storage import gcs as gcs_module
from openstars.storage.compression import decode_json
from openstars.storage.gcs import GCSStorage
from openstars.storage.state_versioning import UnsupportedStateVersionError


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
        self.content_encoding = None

    def upload_from_string(self, data: bytes, content_type: str, if_generation_match=None) -> None:
        existing = self.bucket.objects.get(self.name)
        if if_generation_match == 0 and existing is not None:
            raise FakePreconditionFailed(self.name)
        generation = 1 if existing is None else existing["generation"] + 1
        self.bucket.objects[self.name] = {
            "data": data,
            "content_type": content_type,
            "content_encoding": self.content_encoding,
            "generation": generation,
        }

    def download_as_bytes(self, raw_download: bool = False) -> bytes:
        if self.name not in self.bucket.objects:
            raise FakeNotFound(self.name)
        obj = self.bucket.objects[self.name]
        if raw_download or obj["content_encoding"] != "gzip":
            return obj["data"]
        return decode_json(obj["data"]).encode("utf-8")

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


def test_saved_state_blobs_include_root_state_version(
    storage, sample_global_state, sample_player_state
):
    storage.save_global_state("game1", 0, sample_global_state)
    storage.save_player_state("game1", "tim", 0, sample_player_state)

    bucket = storage.bucket
    global_state_payload = json.loads(
        decode_json(bucket.objects["game1/state/global-state-T0.json.gz"]["data"])
    )
    player_state_payload = json.loads(
        decode_json(bucket.objects["game1/players/player-state-tim-T0.json.gz"]["data"])
    )

    assert global_state_payload["state_version"] == 1
    assert player_state_payload["state_version"] == 1


def test_load_global_state_rejects_missing_state_version(storage):
    storage._update_json_blob(
        "game1/state/global-state-T0.json.gz",
        json.dumps({"game": {"seed": 1, "turn": 0, "next_id": 1}}),
    )

    with pytest.raises(UnsupportedStateVersionError, match="missing required state_version"):
        storage.load_global_state("game1", 0)


def test_load_player_state_rejects_newer_state_version(storage):
    storage._update_json_blob(
        "game1/players/player-state-tim-T0.json.gz",
        json.dumps(
            {
                "state_version": 999,
                "player": "tim",
                "turn": 0,
                "planets": [],
                "fleets": [],
                "designs": [],
                "events": [],
            }
        ),
    )

    with pytest.raises(UnsupportedStateVersionError, match="newer than supported version"):
        storage.load_player_state("game1", "tim", 0)


def test_commands_round_trip(storage, sample_commands):
    storage.save_commands("game1", "tim", 0, sample_commands)

    loaded = storage.load_commands("game1", "tim", 0)

    assert loaded == sample_commands


def test_has_commands(storage, sample_commands):
    assert not storage.has_commands("game1", "tim", 0)

    storage.save_commands("game1", "tim", 0, sample_commands)

    assert storage.has_commands("game1", "tim", 0)


def test_load_missing_file_raises(storage):
    with pytest.raises(FileNotFoundError):
        storage.load_galaxy("nonexistent")


def test_rejects_unsafe_username(storage, sample_commands):
    with pytest.raises(ValueError, match="Unsafe username"):
        storage.save_commands("game1", "../tim", 0, sample_commands)


def test_design_round_trip(storage):
    design = Design(
        id="DEdesign1",
        owner="tim",
        name="Long Range Scout",
        hull="scout",
        mass=12,
        fuel_usage=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        fuel_capacity=100,
        scanner=Scanner(normal=120, penetrating=0),
        cargo_capacity=0,
        cost=DesignCost(resources=20, minerals=Minerals(ironium=4, boranium=0, germanium=2)),
    )
    storage.save_design("game1", "tim", design)
    loaded = storage.load_design("game1", "tim", "DEdesign1")
    assert loaded == design
    listed = storage.list_designs("game1", "tim")
    assert listed == [design]


def test_combat_log_round_trip(storage):
    log = CombatLog(config=AltairCombatConfig(), events=[BattleEndEvent(reason="done")])
    storage.save_combat_log("game1", "BTabc123", log)

    loaded = storage.load_combat_log("game1", "BTabc123")
    assert loaded == log
    assert storage.list_combat_logs("game1") == ["BTabc123"]


def test_saved_global_state_blob_is_gzip_without_content_encoding(storage, sample_global_state):
    storage.save_global_state("game1", 0, sample_global_state)
    obj = storage.bucket.objects["game1/state/global-state-T0.json.gz"]
    assert obj["content_type"] == "application/gzip"
    assert obj["content_encoding"] is None
    assert obj["data"].startswith(b"\x1f\x8b")
