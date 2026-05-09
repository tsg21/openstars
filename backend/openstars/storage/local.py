"""Local filesystem storage implementation."""

from pathlib import Path

from openstars.storage.base import GameStorage
from openstars.storage.compression import decode_json, encode_json


class LocalStorage(GameStorage):
    """Store game data as gzipped JSON files on the local filesystem.

    Layout mirrors GCS bucket layout from PRD 06.
    """

    def __init__(self, base_path: str | Path) -> None:
        self.base_path = Path(base_path).resolve()

    def _path_for(self, name: str) -> Path:
        path = (self.base_path / name).resolve()
        if self.base_path != path and self.base_path not in path.parents:
            raise ValueError(f"Path escapes storage directory: {name}")
        return path

    def _create_json_blob(self, name: str, data: str) -> None:
        path = self._path_for(name)
        if path.exists():
            raise FileExistsError(f"Object already exists: {name}")
        self._write(path, data)

    def _update_json_blob(self, name: str, data: str) -> None:
        self._write(self._path_for(name), data)

    def _load_json_blob(self, name: str) -> str:
        path = self._path_for(name)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        return decode_json(path.read_bytes())

    def _blob_exists(self, name: str) -> bool:
        return self._path_for(name).exists()

    def _list_blob_names(self) -> list[str]:
        if not self.base_path.exists():
            return []
        return sorted(
            path.relative_to(self.base_path).as_posix()
            for path in self.base_path.rglob("*")
            if path.is_file()
        )

    @staticmethod
    def _write(path: Path, data: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(encode_json(data))
