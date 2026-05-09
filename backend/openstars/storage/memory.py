"""In-memory storage implementation for tests."""

from openstars.storage.base import GameStorage


class MemoryStorage(GameStorage):
    """Store game objects in memory for the lifetime of a process."""

    def __init__(self) -> None:
        self._objects: dict[str, str] = {}

    def _create_json_blob(self, name: str, data: str) -> None:
        if name in self._objects:
            raise FileExistsError(f"Object already exists: {name}")
        self._objects[name] = data

    def _update_json_blob(self, name: str, data: str) -> None:
        self._objects[name] = data

    def _load_json_blob(self, name: str) -> str:
        if name not in self._objects:
            raise FileNotFoundError(f"Object not found: {name}")
        return self._objects[name]

    def _blob_exists(self, name: str) -> bool:
        return name in self._objects

    def _list_blob_names(self) -> list[str]:
        return sorted(self._objects)
