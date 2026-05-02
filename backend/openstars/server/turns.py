"""Shared helpers for resolving the authoritative current turn."""

from openstars.engine.models import SelectRaceCommand
from openstars.storage.base import GameStorage


def get_current_turn(storage: GameStorage, game_id: str, meta: dict) -> int:
    """Find the current turn, using metadata directly when available."""
    try:
        return int(meta["current_turn"])
    except (KeyError, TypeError, ValueError):
        pass


def player_submitted(storage: GameStorage, game_id: str, username: str, turn: int) -> bool:
    """Has the player submitted commands for this turn?

    At T=0 (race-selection phase) this requires a saved SelectRaceCommand;
    at T>=1 any saved commands count, including an empty list.
    """
    if not storage.has_commands(game_id, username, turn):
        return False
    if turn == 0:
        try:
            cmds = storage.load_commands(game_id, username, turn)
        except FileNotFoundError:
            return False
        return any(isinstance(c, SelectRaceCommand) for c in cmds.commands)
    return True
