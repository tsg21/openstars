"""Load combined ship design registry for all players in a game."""

from openstars.engine.models import Design
from openstars.storage.base import GameStorage


def list_all_designs_for_players(
    storage: GameStorage,
    game_id: str,
    player_usernames: list[str],
) -> list[Design]:
    """Return every stored design for the game's players, sorted by design id."""
    by_id: dict[str, Design] = {}
    for username in sorted(player_usernames):
        for design in storage.list_designs(game_id, username):
            by_id[design.id] = design
    return sorted(by_id.values(), key=lambda d: d.id)
