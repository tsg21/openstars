"""Abstract storage interface for game data."""

from abc import ABC, abstractmethod

from openstars.combat.altair.models import CombatLog
from openstars.engine.models import (
    Design,
    Galaxy,
    GlobalState,
    PlayerCommands,
    PlayerState,
)


class GameStorage(ABC):
    """Abstract base for game state persistence."""

    @abstractmethod
    def save_galaxy(self, game_id: str, galaxy: Galaxy) -> None: ...

    @abstractmethod
    def load_galaxy(self, game_id: str) -> Galaxy: ...

    @abstractmethod
    def save_global_state(self, game_id: str, turn: int, state: GlobalState) -> None: ...

    @abstractmethod
    def load_global_state(self, game_id: str, turn: int) -> GlobalState: ...

    @abstractmethod
    def save_player_state(
        self, game_id: str, username: str, turn: int, state: PlayerState
    ) -> None: ...

    @abstractmethod
    def load_player_state(self, game_id: str, username: str, turn: int) -> PlayerState: ...

    @abstractmethod
    def save_commands(
        self, game_id: str, username: str, turn: int, commands: PlayerCommands
    ) -> None: ...

    @abstractmethod
    def load_commands(self, game_id: str, username: str, turn: int) -> PlayerCommands: ...

    @abstractmethod
    def has_commands(self, game_id: str, username: str, turn: int) -> bool: ...

    @abstractmethod
    def list_games(self) -> list[str]: ...

    @abstractmethod
    def save_game_meta(self, game_id: str, meta: dict) -> None:
        """Save lightweight game metadata (name, galaxy_size, created_at, players)."""
        ...

    @abstractmethod
    def load_game_meta(self, game_id: str) -> dict: ...

    @abstractmethod
    def save_design(self, game_id: str, username: str, design: Design) -> None: ...

    @abstractmethod
    def load_design(self, game_id: str, username: str, design_id: str) -> Design: ...

    @abstractmethod
    def list_designs(self, game_id: str, username: str) -> list[Design]: ...

    @abstractmethod
    def save_combat_log(self, game_id: str, battle_id: str, log: CombatLog) -> None: ...

    @abstractmethod
    def load_combat_log(self, game_id: str, battle_id: str) -> CombatLog: ...

    @abstractmethod
    def list_combat_logs(self, game_id: str) -> list[str]: ...
