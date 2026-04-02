"""FastAPI dependency injection for storage."""

import os
from functools import lru_cache

from openstars.storage.base import GameStorage
from openstars.storage.gcs import GCSStorage
from openstars.storage.local import LocalStorage
from openstars.storage.memory import MemoryStorage


@lru_cache
def get_storage() -> GameStorage:
    """Get the configured storage backend."""
    backend = os.environ.get("STORAGE_BACKEND")
    if not backend:
        raise RuntimeError("STORAGE_BACKEND must be set to 'local', 'memory', or 'gcs'")

    if backend == "local":
        base_path = os.environ.get("GAME_DATA_PATH", "./game-data")
        return LocalStorage(base_path)

    if backend == "memory":
        return MemoryStorage()

    if backend == "gcs":
        bucket_name = os.environ.get("GCS_BUCKET_NAME")
        if not bucket_name:
            raise RuntimeError("GCS_BUCKET_NAME must be set when STORAGE_BACKEND=gcs")
        return GCSStorage(bucket_name)

    raise RuntimeError(f"Unsupported STORAGE_BACKEND: {backend!r}")
