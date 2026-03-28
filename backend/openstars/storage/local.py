"""Local filesystem storage implementation."""

import json
import re
from pathlib import Path

from openstars.engine.models import (
    Galaxy,
    GlobalState,
    PlayerCommands,
    PlayerState,
)
from openstars.storage.base import GameStorage

# Only allow safe characters in path segments (alphanumeric, hyphens, underscores, dots)
_SAFE_SEGMENT = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]*$")


class LocalStorage(GameStorage):
    """Store game data as JSON files on the local filesystem.

    Layout mirrors GCS bucket layout from PRD 06:
        {base_path}/{game_id}/galaxy.json
        {base_path}/{game_id}/state/global-state-T{N}.json
        {base_path}/{game_id}/players/player-state-{username}-T{N}.json
        {base_path}/{game_id}/commands/player-command-{username}-T{N}.json
        {base_path}/{game_id}/meta.json
    """

    def __init__(self, base_path: str | Path) -> None:
        self.base_path = Path(base_path).resolve()

    def _validate_segment(self, value: str, label: str) -> None:
        """Reject path segments that could escape the storage directory."""
        if not _SAFE_SEGMENT.match(value):
            raise ValueError(f"Unsafe {label}: {value!r}")

    def _safe_path(self, path: Path) -> Path:
        """Ensure the resolved path is contained within base_path."""
        resolved = path.resolve()
        if not str(resolved).startswith(str(self.base_path)):
            raise ValueError(f"Path escapes storage directory: {path}")
        return resolved

    def _game_dir(self, game_id: str) -> Path:
        self._validate_segment(game_id, "game_id")
        return self.base_path / game_id

    def _write_json(self, path: Path, data: str) -> None:
        self._safe_path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(data)

    def _read_json(self, path: Path) -> str:
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        return path.read_text()

    # --- Galaxy ---

    def save_galaxy(self, game_id: str, galaxy: Galaxy) -> None:
        path = self._game_dir(game_id) / "galaxy.json"
        self._write_json(path, galaxy.model_dump_json(indent=2))

    def load_galaxy(self, game_id: str) -> Galaxy:
        path = self._game_dir(game_id) / "galaxy.json"
        return Galaxy.model_validate_json(self._read_json(path))

    # --- Global state ---

    def save_global_state(self, game_id: str, turn: int, state: GlobalState) -> None:
        path = self._game_dir(game_id) / "state" / f"global-state-T{turn}.json"
        self._write_json(path, state.model_dump_json(indent=2))

    def load_global_state(self, game_id: str, turn: int) -> GlobalState:
        path = self._game_dir(game_id) / "state" / f"global-state-T{turn}.json"
        return GlobalState.model_validate_json(self._read_json(path))

    # --- Player state ---

    def save_player_state(
        self, game_id: str, username: str, turn: int, state: PlayerState
    ) -> None:
        self._validate_segment(username, "username")
        path = (
            self._game_dir(game_id) / "players" / f"player-state-{username}-T{turn}.json"
        )
        self._write_json(path, state.model_dump_json(indent=2))

    def load_player_state(self, game_id: str, username: str, turn: int) -> PlayerState:
        self._validate_segment(username, "username")
        path = (
            self._game_dir(game_id) / "players" / f"player-state-{username}-T{turn}.json"
        )
        return PlayerState.model_validate_json(self._read_json(path))

    # --- Commands ---

    def save_commands(
        self, game_id: str, username: str, turn: int, commands: PlayerCommands
    ) -> None:
        self._validate_segment(username, "username")
        path = (
            self._game_dir(game_id) / "commands" / f"player-command-{username}-T{turn}.json"
        )
        self._write_json(path, commands.model_dump_json(indent=2))

    def load_commands(self, game_id: str, username: str, turn: int) -> PlayerCommands:
        self._validate_segment(username, "username")
        path = (
            self._game_dir(game_id) / "commands" / f"player-command-{username}-T{turn}.json"
        )
        return PlayerCommands.model_validate_json(self._read_json(path))

    def has_commands(self, game_id: str, username: str, turn: int) -> bool:
        self._validate_segment(username, "username")
        path = (
            self._game_dir(game_id) / "commands" / f"player-command-{username}-T{turn}.json"
        )
        return path.exists()

    # --- Game listing and metadata ---

    def list_games(self) -> list[str]:
        if not self.base_path.exists():
            return []
        return [
            d.name
            for d in sorted(self.base_path.iterdir())
            if d.is_dir() and (d / "meta.json").exists()
        ]

    def save_game_meta(self, game_id: str, meta: dict) -> None:
        path = self._game_dir(game_id) / "meta.json"
        self._write_json(path, json.dumps(meta, indent=2, default=str))

    def load_game_meta(self, game_id: str) -> dict:
        path = self._game_dir(game_id) / "meta.json"
        return json.loads(self._read_json(path))
