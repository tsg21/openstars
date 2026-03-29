"""Google Cloud Storage implementation."""

import json

from openstars.engine.models import (
    Galaxy,
    GlobalState,
    PlayerCommands,
    PlayerState,
)
from openstars.storage.base import GameStorage
from openstars.storage.paths import game_object_name, validate_segment

try:
    from google.api_core.exceptions import NotFound, PreconditionFailed
    from google.cloud import storage as gcs_storage
except ImportError:  # pragma: no cover - exercised via configuration tests instead
    gcs_storage = None

    class NotFound(Exception):
        """Fallback exception used when google-cloud-storage is unavailable."""

    class PreconditionFailed(Exception):
        """Fallback exception used when google-cloud-storage is unavailable."""


class GCSStorage(GameStorage):
    """Store game data as JSON blobs in a Google Cloud Storage bucket."""

    def __init__(self, bucket_name: str) -> None:
        if not bucket_name:
            raise ValueError("GCS bucket name is required")
        if gcs_storage is None:
            raise RuntimeError("google-cloud-storage is not installed")
        self.bucket_name = bucket_name
        self.client = gcs_storage.Client()
        self.bucket = self.client.bucket(bucket_name)

    def _blob(self, name: str):
        return self.bucket.blob(name)

    def _write_json(self, name: str, data: str, *, create_only: bool = False) -> None:
        blob = self._blob(name)
        try:
            if create_only:
                blob.upload_from_string(
                    data,
                    content_type="application/json",
                    if_generation_match=0,
                )
            else:
                blob.upload_from_string(data, content_type="application/json")
        except PreconditionFailed as exc:
            raise FileExistsError(f"Object already exists: {name}") from exc

    def _read_json(self, name: str) -> str:
        blob = self._blob(name)
        try:
            return blob.download_as_text()
        except NotFound as exc:
            raise FileNotFoundError(f"Object not found: {name}") from exc

    def _exists(self, name: str) -> bool:
        return self._blob(name).exists()

    def save_galaxy(self, game_id: str, galaxy: Galaxy) -> None:
        name = game_object_name(game_id, "galaxy.json")
        self._write_json(name, galaxy.model_dump_json(indent=2))

    def load_galaxy(self, game_id: str) -> Galaxy:
        name = game_object_name(game_id, "galaxy.json")
        return Galaxy.model_validate_json(self._read_json(name))

    def save_global_state(self, game_id: str, turn: int, state: GlobalState) -> None:
        name = game_object_name(game_id, "state", f"global-state-T{turn}.json")
        self._write_json(name, state.model_dump_json(indent=2), create_only=True)

    def load_global_state(self, game_id: str, turn: int) -> GlobalState:
        name = game_object_name(game_id, "state", f"global-state-T{turn}.json")
        return GlobalState.model_validate_json(self._read_json(name))

    def save_player_state(self, game_id: str, username: str, turn: int, state: PlayerState) -> None:
        validate_segment(username, "username")
        name = game_object_name(game_id, "players", f"player-state-{username}-T{turn}.json")
        self._write_json(name, state.model_dump_json(indent=2))

    def load_player_state(self, game_id: str, username: str, turn: int) -> PlayerState:
        validate_segment(username, "username")
        name = game_object_name(game_id, "players", f"player-state-{username}-T{turn}.json")
        return PlayerState.model_validate_json(self._read_json(name))

    def save_commands(
        self, game_id: str, username: str, turn: int, commands: PlayerCommands
    ) -> None:
        validate_segment(username, "username")
        name = game_object_name(game_id, "commands", f"player-command-{username}-T{turn}.json")
        self._write_json(name, commands.model_dump_json(indent=2))

    def load_commands(self, game_id: str, username: str, turn: int) -> PlayerCommands:
        validate_segment(username, "username")
        name = game_object_name(game_id, "commands", f"player-command-{username}-T{turn}.json")
        return PlayerCommands.model_validate_json(self._read_json(name))

    def has_commands(self, game_id: str, username: str, turn: int) -> bool:
        validate_segment(username, "username")
        name = game_object_name(game_id, "commands", f"player-command-{username}-T{turn}.json")
        return self._exists(name)

    def list_games(self) -> list[str]:
        game_ids = set()
        for blob in self.client.list_blobs(self.bucket_name):
            name = blob.name.rstrip("/")
            if not name.endswith("/meta.json"):
                continue
            game_id = name[: -len("/meta.json")]
            if "/" in game_id:
                continue
            validate_segment(game_id, "game_id")
            game_ids.add(game_id)
        return sorted(game_ids)

    def save_game_meta(self, game_id: str, meta: dict) -> None:
        name = game_object_name(game_id, "meta.json")
        self._write_json(name, json.dumps(meta, indent=2, default=str))

    def load_game_meta(self, game_id: str) -> dict:
        name = game_object_name(game_id, "meta.json")
        return json.loads(self._read_json(name))
