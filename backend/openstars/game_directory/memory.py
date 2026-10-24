"""In-memory GameDirectory for unit tests and GAME_DIRECTORY_BACKEND=memory."""

from datetime import UTC, datetime

from openstars.game_directory.base import GameDirectory, GameNotFoundError, GameSummary


class InMemoryGameDirectory(GameDirectory):
    def __init__(self) -> None:
        self._store: dict[str, GameSummary] = {}

    def create_game(self, game_id: str, summary: GameSummary) -> None:
        self._store[game_id] = summary.model_copy(deep=True)

    def get_game(self, game_id: str) -> GameSummary:
        if game_id not in self._store:
            raise GameNotFoundError(game_id)
        return self._store[game_id].model_copy(deep=True)

    def list_games_for_player(self, username: str, limit: int = 200) -> list[GameSummary]:
        results = [s for s in self._store.values() if username in s.players]
        results.sort(key=lambda s: s.created_at, reverse=True)
        return [s.model_copy(deep=True) for s in results[:limit]]

    def list_games_for_player_or_override(
        self, username: str, limit: int = 200
    ) -> list[GameSummary]:
        results = [
            s for s in self._store.values() if username in s.players or s.allow_player_override
        ]
        results.sort(key=lambda s: s.created_at, reverse=True)
        return [s.model_copy(deep=True) for s in results[:limit]]

    def list_all_games(self, limit: int = 200) -> list[GameSummary]:
        results = sorted(self._store.values(), key=lambda s: s.created_at, reverse=True)
        return [s.model_copy(deep=True) for s in results[:limit]]

    def player_submitted(self, game_id: str, players_submitted: list[str]) -> None:
        if game_id not in self._store:
            raise GameNotFoundError(game_id)
        self._store[game_id].players_submitted = list(players_submitted)
        self._store[game_id].updated_at = datetime.now(UTC)

    def turn_resolved(self, game_id: str, new_turn: int) -> None:
        if game_id not in self._store:
            raise GameNotFoundError(game_id)
        self._store[game_id].current_turn = new_turn
        self._store[game_id].players_submitted = []
        self._store[game_id].updated_at = datetime.now(UTC)

    def delete_game(self, game_id: str) -> None:
        self._store.pop(game_id, None)
