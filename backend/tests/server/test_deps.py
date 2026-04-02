"""Tests for storage backend dependency wiring."""

import os

import pytest

from openstars.server.deps import get_storage
from openstars.storage.local import LocalStorage
from openstars.storage.memory import MemoryStorage


@pytest.fixture(autouse=True)
def clear_storage_env():
    get_storage.cache_clear()
    original = {
        "STORAGE_BACKEND": os.environ.pop("STORAGE_BACKEND", None),
        "GAME_DATA_PATH": os.environ.pop("GAME_DATA_PATH", None),
        "GCS_BUCKET_NAME": os.environ.pop("GCS_BUCKET_NAME", None),
    }
    yield
    get_storage.cache_clear()
    for key, value in original.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


def test_get_storage_requires_backend():
    with pytest.raises(RuntimeError, match="STORAGE_BACKEND must be set"):
        get_storage()


def test_get_storage_rejects_unknown_backend():
    os.environ["STORAGE_BACKEND"] = "mystery"

    with pytest.raises(RuntimeError, match="Unsupported STORAGE_BACKEND"):
        get_storage()


def test_get_storage_local(tmp_path):
    os.environ["STORAGE_BACKEND"] = "local"
    os.environ["GAME_DATA_PATH"] = str(tmp_path)

    storage = get_storage()

    assert isinstance(storage, LocalStorage)
    assert storage.base_path == tmp_path.resolve()


def test_get_storage_gcs_requires_bucket():
    os.environ["STORAGE_BACKEND"] = "gcs"

    with pytest.raises(RuntimeError, match="GCS_BUCKET_NAME must be set"):
        get_storage()


def test_get_storage_memory():
    os.environ["STORAGE_BACKEND"] = "memory"

    storage = get_storage()

    assert isinstance(storage, MemoryStorage)
