"""Google Cloud Storage implementation."""

import json

from openstars.combat.altair.models import CombatLog
from openstars.engine.models import (
    Design,
    Galaxy,
    GlobalState,
    PlayerCommands,
    PlayerState,
)
from openstars.storage.base import GameStorage
from openstars.storage.compression import decode_json, encode_json
from openstars.storage.paths import game_object_name, validate_segment
from openstars.storage.state_versioning import (
    load_state_payload,
    upgrade_global_state_payload,
    upgrade_player_state_payload,
)

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

    def _write_blob(self, name: str, data: str, *, create_only: bool = False) -> None:
        blob = self._blob(name)
        try:
            if create_only:
                blob.upload_from_string(
                    encode_json(data),
                    content_type="application/json",
                    content_encoding="gzip",
                    if_generation_match=0,
                )
            else:
                blob.upload_from_string(
                    encode_json(data),
                    content_type="application/json",
                    content_encoding="gzip",
                )
        except PreconditionFailed as exc:
            raise FileExistsError(f"Object already exists: {name}") from exc

    def _read_blob(self, name: str) -> str:
        blob = self._blob(name)
        try:
            # download_as_bytes returns raw gzip data for explicit adapter decoding.
            return decode_json(blob.download_as_bytes())
        except NotFound as exc:
            raise FileNotFoundError(f"Object not found: {name}") from exc

    def _exists(self, name: str) -> bool:
        return self._blob(name).exists()

    def save_galaxy(self, game_id: str, galaxy: Galaxy) -> None:
        name = game_object_name(game_id, "galaxy.json.gz")
        self._write_blob(name, galaxy.model_dump_json(indent=2))

    def load_galaxy(self, game_id: str) -> Galaxy:
        name = game_object_name(game_id, "galaxy.json.gz")
        return Galaxy.model_validate_json(self._read_blob(name))

    def save_global_state(self, game_id: str, turn: int, state: GlobalState) -> None:
        name = game_object_name(game_id, "state", f"global-state-T{turn}.json.gz")
        self._write_blob(name, state.model_dump_json(indent=2), create_only=True)

    def load_global_state(self, game_id: str, turn: int) -> GlobalState:
        name = game_object_name(game_id, "state", f"global-state-T{turn}.json.gz")
        payload = load_state_payload(self._read_blob(name))
        return GlobalState.model_validate(upgrade_global_state_payload(payload))

    def save_player_state(self, game_id: str, username: str, turn: int, state: PlayerState) -> None:
        validate_segment(username, "username")
        name = game_object_name(game_id, "players", f"player-state-{username}-T{turn}.json.gz")
        self._write_blob(name, state.model_dump_json(indent=2))

    def load_player_state(self, game_id: str, username: str, turn: int) -> PlayerState:
        validate_segment(username, "username")
        name = game_object_name(game_id, "players", f"player-state-{username}-T{turn}.json.gz")
        payload = load_state_payload(self._read_blob(name))
        return PlayerState.model_validate(upgrade_player_state_payload(payload))

    def save_commands(
        self, game_id: str, username: str, turn: int, commands: PlayerCommands
    ) -> None:
        validate_segment(username, "username")
        name = game_object_name(game_id, "commands", f"player-command-{username}-T{turn}.json.gz")
        self._write_blob(name, commands.model_dump_json(indent=2))

    def load_commands(self, game_id: str, username: str, turn: int) -> PlayerCommands:
        validate_segment(username, "username")
        name = game_object_name(game_id, "commands", f"player-command-{username}-T{turn}.json.gz")
        return PlayerCommands.model_validate_json(self._read_blob(name))

    def has_commands(self, game_id: str, username: str, turn: int) -> bool:
        validate_segment(username, "username")
        name = game_object_name(game_id, "commands", f"player-command-{username}-T{turn}.json.gz")
        return self._exists(name)

    def list_games(self) -> list[str]:
        game_ids = set()
        for blob in self.client.list_blobs(self.bucket_name):
            name = blob.name.rstrip("/")
            if not name.endswith("/meta.json.gz"):
                continue
            game_id = name[: -len("/meta.json.gz")]
            if "/" in game_id:
                continue
            validate_segment(game_id, "game_id")
            game_ids.add(game_id)
        return sorted(game_ids)

    def save_game_meta(self, game_id: str, meta: dict) -> None:
        name = game_object_name(game_id, "meta.json.gz")
        self._write_blob(name, json.dumps(meta, indent=2, default=str))

    def load_game_meta(self, game_id: str) -> dict:
        name = game_object_name(game_id, "meta.json.gz")
        return json.loads(self._read_blob(name))

    def save_design(self, game_id: str, username: str, design: Design) -> None:
        validate_segment(username, "username")
        name = game_object_name(game_id, "designs", username, f"{design.id}.json.gz")
        self._write_blob(name, design.model_dump_json(indent=2))

    def load_design(self, game_id: str, username: str, design_id: str) -> Design:
        validate_segment(username, "username")
        validate_segment(design_id, "design_id")
        name = game_object_name(game_id, "designs", username, f"{design_id}.json.gz")
        return Design.model_validate_json(self._read_blob(name))

    def list_designs(self, game_id: str, username: str) -> list[Design]:
        validate_segment(username, "username")
        prefix = game_object_name(game_id, "designs", username) + "/"
        design_ids: list[str] = []
        for blob in self.client.list_blobs(self.bucket_name):
            name = blob.name.rstrip("/")
            if not name.startswith(prefix) or not name.endswith(".json.gz"):
                continue
            basename = name[len(prefix) :]
            if "/" in basename:
                continue
            design_ids.append(basename.removesuffix(".json.gz"))
        return [self.load_design(game_id, username, design_id) for design_id in sorted(design_ids)]

    def save_combat_log(self, game_id: str, battle_id: str, log: CombatLog) -> None:
        validate_segment(battle_id, "battle_id")
        name = game_object_name(game_id, "combat", f"{battle_id}.json.gz")
        self._write_blob(name, log.model_dump_json(indent=2))

    def load_combat_log(self, game_id: str, battle_id: str) -> CombatLog:
        validate_segment(battle_id, "battle_id")
        name = game_object_name(game_id, "combat", f"{battle_id}.json.gz")
        return CombatLog.model_validate_json(self._read_blob(name))

    def list_combat_logs(self, game_id: str) -> list[str]:
        prefix = game_object_name(game_id, "combat") + "/"
        battle_ids: list[str] = []
        for blob in self.client.list_blobs(self.bucket_name):
            name = blob.name.rstrip("/")
            if not name.startswith(prefix) or not name.endswith(".json.gz"):
                continue
            basename = name[len(prefix) :]
            if "/" in basename:
                continue
            battle_ids.append(basename.removesuffix(".json.gz"))
        return sorted(battle_ids)
