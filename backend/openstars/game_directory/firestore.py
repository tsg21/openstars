"""Firestore-backed GameDirectory."""

from datetime import UTC, datetime

from google.cloud import firestore

from openstars.game_directory.base import GameDirectory, GameNotFoundError, GameSummary

_COLLECTION = "games"


class FirestoreGameDirectory(GameDirectory):
    def __init__(self, client: firestore.Client) -> None:
        self._client = client

    def _doc_ref(self, game_id: str):
        return self._client.collection(_COLLECTION).document(game_id)

    def create_game(self, game_id: str, summary: GameSummary) -> None:
        self._doc_ref(game_id).set(
            {
                "name": summary.name,
                "galaxy_size": summary.galaxy_size,
                "seed": summary.seed,
                "players": summary.players,
                "current_turn": summary.current_turn,
                "players_submitted": summary.players_submitted,
                "created_at": firestore.SERVER_TIMESTAMP,
                "updated_at": firestore.SERVER_TIMESTAMP,
            }
        )

    def get_game(self, game_id: str) -> GameSummary:
        snap = self._doc_ref(game_id).get()
        if not snap.exists:
            raise GameNotFoundError(game_id)
        return self._snap_to_summary(game_id, snap.to_dict())

    def list_games_for_player(self, username: str, limit: int = 200) -> list[GameSummary]:
        query = (
            self._client.collection(_COLLECTION)
            .where(filter=firestore.FieldFilter("players", "array_contains", username))
            .order_by("created_at", direction=firestore.Query.DESCENDING)
            .limit(limit)
        )
        return [self._snap_to_summary(doc.id, doc.to_dict()) for doc in query.stream()]

    def list_all_games(self, limit: int = 200) -> list[GameSummary]:
        query = (
            self._client.collection(_COLLECTION)
            .order_by("created_at", direction=firestore.Query.DESCENDING)
            .limit(limit)
        )
        return [self._snap_to_summary(doc.id, doc.to_dict()) for doc in query.stream()]

    def player_submitted(self, game_id: str, players_submitted: list[str]) -> None:
        self._doc_ref(game_id).set(
            {"players_submitted": players_submitted, "updated_at": firestore.SERVER_TIMESTAMP},
            merge=True,
        )

    def turn_resolved(self, game_id: str, new_turn: int) -> None:
        self._doc_ref(game_id).set(
            {
                "current_turn": new_turn,
                "players_submitted": [],
                "updated_at": firestore.SERVER_TIMESTAMP,
            },
            merge=True,
        )

    def delete_game(self, game_id: str) -> None:
        self._doc_ref(game_id).delete()

    @staticmethod
    def _snap_to_summary(game_id: str, data: dict) -> GameSummary:
        def _to_dt(val) -> datetime:
            if isinstance(val, datetime):
                return val.astimezone(UTC) if val.tzinfo else val.replace(tzinfo=UTC)
            # Firestore DatetimeWithNanoseconds
            try:
                return val.astimezone(UTC)
            except Exception:
                return datetime.now(UTC)

        return GameSummary.model_validate(
            {
                **data,
                "game_id": game_id,
                "created_at": _to_dt(data["created_at"]),
                "updated_at": _to_dt(data["updated_at"]),
            }
        )
