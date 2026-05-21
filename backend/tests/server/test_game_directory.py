"""Unit tests for the GameDirectory abstraction (Step 2)."""

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest

from openstars.game_directory.base import GameNotFoundError, GameSummary
from openstars.game_directory.memory import InMemoryGameDirectory


def _summary(game_id: str = "g1", players: list[str] | None = None, created_offset: int = 0):
    from datetime import timedelta

    now = datetime.now(UTC) + timedelta(seconds=created_offset)
    return GameSummary(
        game_id=game_id,
        name=f"Game {game_id}",
        galaxy_size="small",
        seed=42,
        players=players or ["alice", "bob"],
        current_turn=0,
        players_submitted=[],
        created_at=now,
        updated_at=now,
    )


# --- Factory ---


class TestBuildGameDirectory:
    def test_memory_backend(self, monkeypatch):
        monkeypatch.setenv("GAME_DIRECTORY_BACKEND", "memory")
        from openstars.game_directory.factory import build_game_directory
        from openstars.game_directory.memory import InMemoryGameDirectory

        d = build_game_directory()
        assert isinstance(d, InMemoryGameDirectory)

    def test_storage_memory_implies_memory(self, monkeypatch):
        monkeypatch.delenv("GAME_DIRECTORY_BACKEND", raising=False)
        monkeypatch.setenv("STORAGE_BACKEND", "memory")
        from openstars.game_directory.factory import build_game_directory
        from openstars.game_directory.memory import InMemoryGameDirectory

        d = build_game_directory()
        assert isinstance(d, InMemoryGameDirectory)

    def test_firestore_backend_missing_project_id(self, monkeypatch):
        monkeypatch.setenv("GAME_DIRECTORY_BACKEND", "firestore")
        monkeypatch.delenv("FIREBASE_PROJECT_ID", raising=False)
        from openstars.game_directory.factory import build_game_directory

        with pytest.raises(RuntimeError, match="FIREBASE_PROJECT_ID"):
            build_game_directory()

    def test_unknown_backend_raises(self, monkeypatch):
        monkeypatch.setenv("GAME_DIRECTORY_BACKEND", "bogus")
        from openstars.game_directory.factory import build_game_directory

        with pytest.raises(RuntimeError, match="Unsupported"):
            build_game_directory()

    def test_firestore_backend_returns_firestore_directory(self, monkeypatch):
        monkeypatch.setenv("GAME_DIRECTORY_BACKEND", "firestore")
        monkeypatch.setenv("FIREBASE_PROJECT_ID", "test-project")
        with (
            patch("firebase_admin._apps", {}),
            patch("firebase_admin.initialize_app"),
            patch("firebase_admin.firestore.client", return_value=MagicMock()),
        ):
            from openstars.game_directory.factory import build_game_directory
            from openstars.game_directory.firestore import FirestoreGameDirectory

            d = build_game_directory()
            assert isinstance(d, FirestoreGameDirectory)


# --- InMemoryGameDirectory ---


class TestInMemoryGameDirectory:
    def setup_method(self):
        self.dir = InMemoryGameDirectory()

    def test_create_and_get_round_trips(self):
        s = _summary()
        self.dir.create_game("g1", s)
        got = self.dir.get_game("g1")
        assert got.name == s.name
        assert got.players == s.players
        assert got.current_turn == 0
        assert got.players_submitted == []

    def test_get_missing_raises(self):
        with pytest.raises(GameNotFoundError):
            self.dir.get_game("nope")

    def test_list_games_for_player_filters_by_membership(self):
        self.dir.create_game("g1", _summary("g1", ["alice", "bob"]))
        self.dir.create_game("g2", _summary("g2", ["carol"]))
        results = self.dir.list_games_for_player("alice")
        assert len(results) == 1
        assert results[0].game_id == "g1"

    def test_list_games_for_player_orders_most_recent_first(self):
        self.dir.create_game("g1", _summary("g1", ["alice"], created_offset=0))
        self.dir.create_game("g2", _summary("g2", ["alice"], created_offset=10))
        results = self.dir.list_games_for_player("alice")
        assert results[0].game_id == "g2"
        assert results[1].game_id == "g1"

    def test_player_submitted_updates_field_and_bumps_updated_at(self):
        s = _summary()
        self.dir.create_game("g1", s)
        before = self.dir.get_game("g1").updated_at
        self.dir.player_submitted("g1", ["alice"])
        after = self.dir.get_game("g1")
        assert after.players_submitted == ["alice"]
        assert after.updated_at >= before

    def test_turn_resolved_advances_turn_and_resets_submitted(self):
        s = _summary()
        self.dir.create_game("g1", s)
        self.dir.player_submitted("g1", ["alice", "bob"])
        self.dir.turn_resolved("g1", 1)
        got = self.dir.get_game("g1")
        assert got.current_turn == 1
        assert got.players_submitted == []


# --- GameSummary.all_turns_submitted ---


class TestAllTurnsSubmitted:
    def test_true_when_all_submitted(self):
        s = _summary()
        s.players_submitted = ["alice", "bob"]
        assert s.all_turns_submitted is True

    def test_false_when_partial(self):
        s = _summary()
        s.players_submitted = ["alice"]
        assert s.all_turns_submitted is False

    def test_false_when_empty(self):
        s = _summary()
        assert s.all_turns_submitted is False

    def test_true_with_superset_submitted(self):
        """Order-independent: submitted is a superset of players."""
        s = _summary()
        s.players_submitted = ["bob", "alice"]
        assert s.all_turns_submitted is True


# --- FirestoreGameDirectory (mock client) ---


class TestFirestoreGameDirectoryMock:
    def _make_dir(self):
        from openstars.game_directory.firestore import FirestoreGameDirectory

        mock_client = MagicMock()
        return FirestoreGameDirectory(mock_client), mock_client

    def test_create_game_calls_set_with_expected_payload(self):
        d, client = self._make_dir()
        s = _summary()
        d.create_game("g1", s)
        doc_ref = client.collection.return_value.document.return_value
        doc_ref.set.assert_called_once()
        payload = doc_ref.set.call_args[0][0]
        assert payload["name"] == s.name
        assert payload["players"] == s.players
        assert payload["current_turn"] == 0
        assert payload["players_submitted"] == []

    def test_player_submitted_calls_set_merge(self):
        d, client = self._make_dir()
        d.player_submitted("g1", ["alice"])
        doc_ref = client.collection.return_value.document.return_value
        doc_ref.set.assert_called_once()
        _, kwargs = doc_ref.set.call_args
        assert kwargs.get("merge") is True
        payload = doc_ref.set.call_args[0][0]
        assert payload["players_submitted"] == ["alice"]

    def test_turn_resolved_calls_set_merge_with_new_turn(self):
        d, client = self._make_dir()
        d.turn_resolved("g1", 2)
        doc_ref = client.collection.return_value.document.return_value
        doc_ref.set.assert_called_once()
        _, kwargs = doc_ref.set.call_args
        assert kwargs.get("merge") is True
        payload = doc_ref.set.call_args[0][0]
        assert payload["current_turn"] == 2
        assert payload["players_submitted"] == []

    def test_delete_game_calls_delete(self):
        d, client = self._make_dir()
        d.delete_game("g1")
        doc_ref = client.collection.return_value.document.return_value
        doc_ref.delete.assert_called_once()
