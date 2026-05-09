"""Abstract storage interface for game data."""

import json
from abc import ABC, abstractmethod

from openstars.combat.altair.models import CombatLog
from openstars.engine.models import (
    Design,
    Galaxy,
    GlobalState,
    PlayerCommands,
    PlayerState,
)
from openstars.storage.compression import BLOB_SUFFIX
from openstars.storage.paths import game_object_name, validate_segment
from openstars.storage.state_versioning import (
    load_state_payload,
    upgrade_global_state_payload,
    upgrade_player_state_payload,
)


class GameStorage(ABC):
    """Abstract base for game state persistence."""

    @abstractmethod
    def _create_json_blob(self, name: str, data: str) -> None:
        """Create a JSON object, raising FileExistsError if it already exists."""
        ...

    @abstractmethod
    def _update_json_blob(self, name: str, data: str) -> None:
        """Write a JSON object, replacing any previous value."""
        ...

    @abstractmethod
    def _load_json_blob(self, name: str) -> str:
        """Load a JSON string from a storage-object name."""
        ...

    @abstractmethod
    def _blob_exists(self, name: str) -> bool:
        """Return whether a storage-object name exists."""
        ...

    @abstractmethod
    def _list_blob_names(self) -> list[str]:
        """Return all storage-object names known to this adapter."""
        ...

    def save_galaxy(self, game_id: str, galaxy: Galaxy) -> None:
        self._update_json_blob(
            game_object_name(game_id, f"galaxy{BLOB_SUFFIX}"),
            galaxy.model_dump_json(indent=2),
        )

    def load_galaxy(self, game_id: str) -> Galaxy:
        return Galaxy.model_validate_json(
            self._load_json_blob(game_object_name(game_id, f"galaxy{BLOB_SUFFIX}"))
        )

    def create_global_state(self, game_id: str, turn: int, state: GlobalState) -> None:
        self._create_json_blob(
            game_object_name(game_id, "state", f"global-state-T{turn}{BLOB_SUFFIX}"),
            state.model_dump_json(indent=2),
        )

    def update_global_state(self, game_id: str, turn: int, state: GlobalState) -> None:
        self._update_json_blob(
            game_object_name(game_id, "state", f"global-state-T{turn}{BLOB_SUFFIX}"),
            state.model_dump_json(indent=2),
        )

    def save_global_state(self, game_id: str, turn: int, state: GlobalState) -> None:
        self.create_global_state(game_id, turn, state)

    def load_global_state(self, game_id: str, turn: int) -> GlobalState:
        payload = load_state_payload(
            self._load_json_blob(
                game_object_name(game_id, "state", f"global-state-T{turn}{BLOB_SUFFIX}")
            )
        )
        return GlobalState.model_validate(upgrade_global_state_payload(payload))

    def save_player_state(self, game_id: str, username: str, turn: int, state: PlayerState) -> None:
        validate_segment(username, "username")
        self._update_json_blob(
            game_object_name(game_id, "players", f"player-state-{username}-T{turn}{BLOB_SUFFIX}"),
            state.model_dump_json(indent=2),
        )

    def load_player_state(self, game_id: str, username: str, turn: int) -> PlayerState:
        validate_segment(username, "username")
        payload = load_state_payload(
            self._load_json_blob(
                game_object_name(
                    game_id, "players", f"player-state-{username}-T{turn}{BLOB_SUFFIX}"
                )
            )
        )
        return PlayerState.model_validate(upgrade_player_state_payload(payload))

    def save_commands(
        self, game_id: str, username: str, turn: int, commands: PlayerCommands
    ) -> None:
        validate_segment(username, "username")
        self._update_json_blob(
            game_object_name(
                game_id, "commands", f"player-command-{username}-T{turn}{BLOB_SUFFIX}"
            ),
            commands.model_dump_json(indent=2),
        )

    def load_commands(self, game_id: str, username: str, turn: int) -> PlayerCommands:
        validate_segment(username, "username")
        return PlayerCommands.model_validate_json(
            self._load_json_blob(
                game_object_name(
                    game_id, "commands", f"player-command-{username}-T{turn}{BLOB_SUFFIX}"
                )
            )
        )

    def has_commands(self, game_id: str, username: str, turn: int) -> bool:
        validate_segment(username, "username")
        return self._blob_exists(
            game_object_name(game_id, "commands", f"player-command-{username}-T{turn}{BLOB_SUFFIX}")
        )

    def list_games(self) -> list[str]:
        game_ids = set()
        for name in self._list_blob_names():
            name = name.rstrip("/")
            if not name.endswith(f"/meta{BLOB_SUFFIX}"):
                continue
            game_id = name[: -len(f"/meta{BLOB_SUFFIX}")]
            if "/" in game_id:
                continue
            validate_segment(game_id, "game_id")
            game_ids.add(game_id)
        return sorted(game_ids)

    def save_game_meta(self, game_id: str, meta: dict) -> None:
        """Save lightweight game metadata (name, galaxy_size, created_at, players)."""
        self._update_json_blob(
            game_object_name(game_id, f"meta{BLOB_SUFFIX}"),
            json.dumps(meta, indent=2, default=str),
        )

    def load_game_meta(self, game_id: str) -> dict:
        return json.loads(self._load_json_blob(game_object_name(game_id, f"meta{BLOB_SUFFIX}")))

    def save_design(self, game_id: str, username: str, design: Design) -> None:
        validate_segment(username, "username")
        self._update_json_blob(
            game_object_name(game_id, "designs", username, f"{design.id}{BLOB_SUFFIX}"),
            design.model_dump_json(indent=2),
        )

    def load_design(self, game_id: str, username: str, design_id: str) -> Design:
        validate_segment(username, "username")
        validate_segment(design_id, "design_id")
        return Design.model_validate_json(
            self._load_json_blob(
                game_object_name(game_id, "designs", username, f"{design_id}{BLOB_SUFFIX}")
            )
        )

    def list_designs(self, game_id: str, username: str) -> list[Design]:
        validate_segment(username, "username")
        prefix = game_object_name(game_id, "designs", username) + "/"
        design_ids: list[str] = []
        for name in self._list_blob_names():
            name = name.rstrip("/")
            if not name.startswith(prefix) or not name.endswith(BLOB_SUFFIX):
                continue
            basename = name[len(prefix) :]
            if "/" in basename:
                continue
            design_ids.append(basename.removesuffix(BLOB_SUFFIX))
        return [self.load_design(game_id, username, design_id) for design_id in sorted(design_ids)]

    def save_combat_log(self, game_id: str, battle_id: str, log: CombatLog) -> None:
        validate_segment(battle_id, "battle_id")
        self._update_json_blob(
            game_object_name(game_id, "combat", f"{battle_id}{BLOB_SUFFIX}"),
            log.model_dump_json(indent=2),
        )

    def load_combat_log(self, game_id: str, battle_id: str) -> CombatLog:
        validate_segment(battle_id, "battle_id")
        return CombatLog.model_validate_json(
            self._load_json_blob(game_object_name(game_id, "combat", f"{battle_id}{BLOB_SUFFIX}"))
        )

    def list_combat_logs(self, game_id: str) -> list[str]:
        prefix = game_object_name(game_id, "combat") + "/"
        battle_ids: list[str] = []
        for name in self._list_blob_names():
            name = name.rstrip("/")
            if not name.startswith(prefix) or not name.endswith(BLOB_SUFFIX):
                continue
            basename = name[len(prefix) :]
            if "/" in basename:
                continue
            battle_ids.append(basename.removesuffix(BLOB_SUFFIX))
        return sorted(battle_ids)
