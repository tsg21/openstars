"""Shared helpers for resolving the authoritative current turn."""

from openstars.storage.base import GameStorage


def get_current_turn(storage: GameStorage, game_id: str, meta: dict) -> int:
    """Find the current turn, using metadata directly when available."""
    try:
        return int(meta["current_turn"])
    except (KeyError, TypeError, ValueError):
        pass

    # only needed for very old files. Remove this later.
    turn = 0
    while True:
        try:
            storage.load_global_state(game_id, turn + 1)
            turn += 1
        except FileNotFoundError:
            break
    return turn
