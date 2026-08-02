"""Abstract GameDirectory interface and shared models."""

from abc import ABC, abstractmethod
from datetime import UTC, datetime

from pydantic import BaseModel


class GameNotFoundError(Exception):
    pass


class GameSummary(BaseModel):
    game_id: str
    name: str
    galaxy_size: str
    seed: int
    players: list[str]
    current_turn: int
    players_submitted: list[str]
    created_at: datetime
    updated_at: datetime
    # Whether a caller may act as a player other than their verified identity.
    #
    # The default here and the default on `new()` deliberately disagree. Documents
    # written before this field existed have no such key, and Firestore hands back
    # exactly what it stored — so the *model* default has to be True to keep those
    # games reachable. New games go through `new()`, which defaults to False so
    # anything created from now on is strict unless the creator opts in.
    allow_player_override: bool = True

    @property
    def all_turns_submitted(self) -> bool:
        return set(self.players_submitted) >= set(self.players)

    @classmethod
    def new(
        cls,
        game_id: str,
        name: str,
        galaxy_size: str,
        seed: int,
        players: list[str],
        allow_player_override: bool = False,
    ) -> "GameSummary":
        now = datetime.now(UTC)
        return cls(
            game_id=game_id,
            name=name,
            galaxy_size=galaxy_size,
            seed=seed,
            players=players,
            current_turn=0,
            players_submitted=[],
            created_at=now,
            updated_at=now,
            allow_player_override=allow_player_override,
        )


class GameDirectory(ABC):
    """Abstract interface for game-summary metadata and realtime notification writes."""

    @abstractmethod
    def create_game(self, game_id: str, summary: GameSummary) -> None:
        """Write the initial Firestore document. Raises if game_id already exists."""
        ...

    @abstractmethod
    def get_game(self, game_id: str) -> GameSummary:
        """Read the game document. Raises GameNotFoundError if missing."""
        ...

    @abstractmethod
    def list_games_for_player(self, username: str, limit: int = 200) -> list[GameSummary]:
        """Return games the player participates in, most-recent first."""
        ...

    @abstractmethod
    def list_all_games(self, limit: int = 200) -> list[GameSummary]:
        """Return all games, most-recent first."""
        ...

    @abstractmethod
    def player_submitted(self, game_id: str, players_submitted: list[str]) -> None:
        """Merge-update players_submitted and updated_at."""
        ...

    @abstractmethod
    def turn_resolved(self, game_id: str, new_turn: int) -> None:
        """Advance current_turn and reset players_submitted to []."""
        ...

    @abstractmethod
    def delete_game(self, game_id: str) -> None:
        """Delete the game document. Used only by cleanup tooling and tests."""
        ...
