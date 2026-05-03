from openstars.engine.models import (
    Galaxy,
    GlobalState,
    PlayerCommands,
    SelectRaceCommand,
)
from openstars.engine.resolve import resolve_turn
from openstars.storage.base import GameStorage


def submit_default_race_and_resolve_turn_0(
    global_state: GlobalState,
    galaxy: Galaxy,
    storage: GameStorage,
    usernames: list[str],
    *,
    game_id: str = "game1",
) -> GlobalState:
    commands = {
        username: PlayerCommands(
            commands=[SelectRaceCommand(predefined_id="humanoid")],
        )
        for username in usernames
    }
    return resolve_turn(
        global_state,
        galaxy,
        commands,
        designs=[],
        game_id=game_id,
        storage=storage,
    )
