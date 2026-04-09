"""In-memory storage implementation for tests."""

import json

from openstars.engine.models import Design, Galaxy, GlobalState, PlayerCommands, PlayerState
from openstars.storage.base import GameStorage
from openstars.storage.paths import game_object_name, validate_segment
from openstars.storage.state_versioning import (
    load_state_payload,
    upgrade_global_state_payload,
    upgrade_player_state_payload,
)


class MemoryStorage(GameStorage):
    """Store game objects in memory for the lifetime of a process."""

    def __init__(self) -> None:
        self._objects: dict[str, str] = {}

    def _put_json(self, key: str, data: str) -> None:
        self._objects[key] = data

    def _get_json(self, key: str) -> str:
        if key not in self._objects:
            raise FileNotFoundError(f"Object not found: {key}")
        return self._objects[key]

    def save_galaxy(self, game_id: str, galaxy: Galaxy) -> None:
        key = game_object_name(game_id, "galaxy.json")
        self._put_json(key, galaxy.model_dump_json(indent=2))

    def load_galaxy(self, game_id: str) -> Galaxy:
        key = game_object_name(game_id, "galaxy.json")
        return Galaxy.model_validate_json(self._get_json(key))

    def save_global_state(self, game_id: str, turn: int, state: GlobalState) -> None:
        key = game_object_name(game_id, "state", f"global-state-T{turn}.json")
        self._put_json(key, state.model_dump_json(indent=2))

    def load_global_state(self, game_id: str, turn: int) -> GlobalState:
        key = game_object_name(game_id, "state", f"global-state-T{turn}.json")
        payload = load_state_payload(self._get_json(key))
        return GlobalState.model_validate(upgrade_global_state_payload(payload))

    def save_player_state(self, game_id: str, username: str, turn: int, state: PlayerState) -> None:
        validate_segment(username, "username")
        key = game_object_name(game_id, "players", f"player-state-{username}-T{turn}.json")
        self._put_json(key, state.model_dump_json(indent=2))

    def load_player_state(self, game_id: str, username: str, turn: int) -> PlayerState:
        validate_segment(username, "username")
        key = game_object_name(game_id, "players", f"player-state-{username}-T{turn}.json")
        payload = load_state_payload(self._get_json(key))
        return PlayerState.model_validate(upgrade_player_state_payload(payload))

    def save_commands(
        self, game_id: str, username: str, turn: int, commands: PlayerCommands
    ) -> None:
        validate_segment(username, "username")
        key = game_object_name(game_id, "commands", f"player-command-{username}-T{turn}.json")
        self._put_json(key, commands.model_dump_json(indent=2))

    def load_commands(self, game_id: str, username: str, turn: int) -> PlayerCommands:
        validate_segment(username, "username")
        key = game_object_name(game_id, "commands", f"player-command-{username}-T{turn}.json")
        return PlayerCommands.model_validate_json(self._get_json(key))

    def has_commands(self, game_id: str, username: str, turn: int) -> bool:
        validate_segment(username, "username")
        key = game_object_name(game_id, "commands", f"player-command-{username}-T{turn}.json")
        return key in self._objects

    def list_games(self) -> list[str]:
        game_ids = {
            key.split("/", maxsplit=1)[0] for key in self._objects if key.endswith("/meta.json")
        }
        return sorted(game_ids)

    def save_game_meta(self, game_id: str, meta: dict) -> None:
        key = game_object_name(game_id, "meta.json")
        self._put_json(key, json.dumps(meta, indent=2, default=str))

    def load_game_meta(self, game_id: str) -> dict:
        key = game_object_name(game_id, "meta.json")
        return json.loads(self._get_json(key))

    def save_design(self, game_id: str, username: str, design: Design) -> None:
        validate_segment(username, "username")
        key = game_object_name(game_id, "designs", username, f"{design.id}.json")
        self._put_json(key, design.model_dump_json(indent=2))

    def load_design(self, game_id: str, username: str, design_id: str) -> Design:
        validate_segment(username, "username")
        key = game_object_name(game_id, "designs", username, f"{design_id}.json")
        return Design.model_validate_json(self._get_json(key))

    def list_designs(self, game_id: str, username: str) -> list[Design]:
        validate_segment(username, "username")
        prefix = game_object_name(game_id, "designs", username) + "/"
        design_keys = sorted(
            key for key in self._objects if key.startswith(prefix) and key.endswith(".json")
        )
        return [Design.model_validate_json(self._objects[key]) for key in design_keys]
