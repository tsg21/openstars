"""Local filesystem storage implementation."""

import json
import re
from pathlib import Path

from openstars.combat.altair.models import CombatLog
from openstars.engine.models import Design, Galaxy, GlobalState, PlayerCommands, PlayerState
from openstars.storage.base import GameStorage
from openstars.storage.compression import BLOB_SUFFIX, decode_json, encode_json
from openstars.storage.paths import game_object_name, validate_segment
from openstars.storage.state_versioning import (
    load_state_payload,
    upgrade_global_state_payload,
    upgrade_player_state_payload,
)


class LocalStorage(GameStorage):
    """Store game data as JSON files on the local filesystem.

    Layout mirrors GCS bucket layout from PRD 06:
        {base_path}/{game_id}/galaxy.json.gz
        {base_path}/{game_id}/state/global-state-T{N}.json.gz
        {base_path}/{game_id}/players/player-state-{username}-T{N}.json.gz
        {base_path}/{game_id}/commands/player-command-{username}-T{N}.json.gz
        {base_path}/{game_id}/meta.json.gz
    """

    def __init__(self, base_path: str | Path) -> None:
        self.base_path = Path(base_path).resolve()

    def _safe_path(self, path: Path) -> Path:
        """Ensure the resolved path is contained within base_path."""
        resolved = path.resolve()
        if not str(resolved).startswith(str(self.base_path)):
            raise ValueError(f"Path escapes storage directory: {path}")
        return resolved

    def _game_dir(self, game_id: str) -> Path:
        return self.base_path / game_object_name(game_id)

    def _write_blob(self, path: Path, data: str) -> None:
        self._safe_path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(encode_json(data))

    def _read_blob(self, path: Path) -> str:
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        return decode_json(path.read_bytes())

    # --- Galaxy ---

    def save_galaxy(self, game_id: str, galaxy: Galaxy) -> None:
        path = self._game_dir(game_id) / f"galaxy{BLOB_SUFFIX}"
        self._write_blob(path, galaxy.model_dump_json(indent=2))

    def load_galaxy(self, game_id: str) -> Galaxy:
        path = self._game_dir(game_id) / f"galaxy{BLOB_SUFFIX}"
        return Galaxy.model_validate_json(self._read_blob(path))

    # --- Global state ---

    def save_global_state(self, game_id: str, turn: int, state: GlobalState) -> None:
        path = self._game_dir(game_id) / "state" / f"global-state-T{turn}.json.gz"
        self._write_blob(path, state.model_dump_json(indent=2))

    def load_global_state(self, game_id: str, turn: int) -> GlobalState:
        path = self._game_dir(game_id) / "state" / f"global-state-T{turn}.json.gz"
        payload = load_state_payload(self._read_blob(path))
        return GlobalState.model_validate(upgrade_global_state_payload(payload))

    # --- Player state ---

    def save_player_state(self, game_id: str, username: str, turn: int, state: PlayerState) -> None:
        validate_segment(username, "username")
        path = self._game_dir(game_id) / "players" / f"player-state-{username}-T{turn}.json.gz"
        self._write_blob(path, state.model_dump_json(indent=2))

    def load_player_state(self, game_id: str, username: str, turn: int) -> PlayerState:
        validate_segment(username, "username")
        path = self._game_dir(game_id) / "players" / f"player-state-{username}-T{turn}.json.gz"
        payload = load_state_payload(self._read_blob(path))
        return PlayerState.model_validate(upgrade_player_state_payload(payload))

    # --- Commands ---

    def save_commands(
        self, game_id: str, username: str, turn: int, commands: PlayerCommands
    ) -> None:
        validate_segment(username, "username")
        path = self._game_dir(game_id) / "commands" / f"player-command-{username}-T{turn}.json.gz"
        self._write_blob(path, commands.model_dump_json(indent=2))

    def load_commands(self, game_id: str, username: str, turn: int) -> PlayerCommands:
        validate_segment(username, "username")
        path = self._game_dir(game_id) / "commands" / f"player-command-{username}-T{turn}.json.gz"
        return PlayerCommands.model_validate_json(self._read_blob(path))

    def has_commands(self, game_id: str, username: str, turn: int) -> bool:
        validate_segment(username, "username")
        path = self._game_dir(game_id) / "commands" / f"player-command-{username}-T{turn}.json.gz"
        return path.exists()

    # --- Game listing and metadata ---

    def list_games(self) -> list[str]:
        if not self.base_path.exists():
            return []
        return [
            d.name
            for d in sorted(self.base_path.iterdir())
            if d.is_dir() and (d / "meta.json.gz").exists()
        ]

    def save_game_meta(self, game_id: str, meta: dict) -> None:
        path = self._game_dir(game_id) / "meta.json.gz"
        self._write_blob(path, json.dumps(meta, indent=2, default=str))

    def load_game_meta(self, game_id: str) -> dict:
        path = self._game_dir(game_id) / "meta.json.gz"
        return json.loads(self._read_blob(path))

    def save_design(self, game_id: str, username: str, design: Design) -> None:
        validate_segment(username, "username")
        path = self._game_dir(game_id) / "designs" / username / f"{design.id}.json.gz"
        self._write_blob(path, design.model_dump_json(indent=2))

    def load_design(self, game_id: str, username: str, design_id: str) -> Design:
        validate_segment(username, "username")
        validate_segment(design_id, "design_id")
        path = self._game_dir(game_id) / "designs" / username / f"{design_id}.json.gz"
        return Design.model_validate_json(self._read_blob(path))

    def list_designs(self, game_id: str, username: str) -> list[Design]:
        validate_segment(username, "username")
        directory = self._game_dir(game_id) / "designs" / username
        if not directory.exists():
            return []
        design_files = sorted(
            path
            for path in directory.iterdir()
            if path.is_file() and path.name.endswith(BLOB_SUFFIX)
        )
        return [Design.model_validate_json(self._read_blob(path)) for path in design_files]

    def save_combat_log(self, game_id: str, battle_id: str, log: CombatLog) -> None:
        validate_segment(battle_id, "battle_id")
        if not self._ENTITY_ID_RE.fullmatch(battle_id):
            raise ValueError(f"Unsafe battle_id: {battle_id!r}")
        path = self._game_dir(game_id) / "combat" / f"{battle_id}.json.gz"
        self._write_blob(path, log.model_dump_json(indent=2))

    def load_combat_log(self, game_id: str, battle_id: str) -> CombatLog:
        validate_segment(battle_id, "battle_id")
        path = self._game_dir(game_id) / "combat" / f"{battle_id}.json.gz"
        return CombatLog.model_validate_json(self._read_blob(path))

    def list_combat_logs(self, game_id: str) -> list[str]:
        directory = self._game_dir(game_id) / "combat"
        if not directory.exists():
            return []
        return sorted(
            path.name.removesuffix(BLOB_SUFFIX)
            for path in directory.iterdir()
            if path.is_file() and path.name.endswith(BLOB_SUFFIX)
        )

    _ENTITY_ID_RE = re.compile(r"^[A-Z]{2}[0-9a-z]{6}$")
