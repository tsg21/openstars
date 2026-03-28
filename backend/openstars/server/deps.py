"""FastAPI dependency injection for storage."""

import os
from functools import lru_cache

from openstars.storage.base import GameStorage
from openstars.storage.local import LocalStorage


@lru_cache
def get_storage() -> GameStorage:
    """Get the configured storage backend."""
    base_path = os.environ.get("GAME_DATA_PATH", "./game-data")
    return LocalStorage(base_path)
