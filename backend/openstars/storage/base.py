"""Abstract storage interface for game data."""

from abc import ABC, abstractmethod

from openstars.engine.models import (
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
