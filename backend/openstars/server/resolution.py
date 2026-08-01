"""Shared turn-resolution logic used by submit_commands."""

import logging
from dataclasses import dataclass

from openstars.engine.component_catalogue import load_component_catalogue
from openstars.engine.fog import derive_player_state
from openstars.engine.resolve import resolve_turn
from openstars.engine.state_context import StateContext
from openstars.game_directory.base import GameDirectory, GameSummary
from openstars.server.game_designs import list_all_designs_for_players
from openstars.storage.base import GameStorage

log = logging.getLogger(__name__)


@dataclass
class ResolveOutcome:
    new_turn: int
    resolved: bool


def resolve_current_turn(
    storage: GameStorage,
    directory: GameDirectory,
    game_id: str,
    summary: GameSummary,
) -> ResolveOutcome:
    """Run the turn resolution pipeline and persist the results.

    Calls directory.turn_resolved *after* all state files are durable so that
    a Firestore listener firing on current_turn change always finds readable state.

    Raises on engine error — the caller should return 500 and leave the command
    file in place for resubmission.
    """
    current_turn = summary.current_turn
    players = summary.players

    global_state = storage.load_global_state(game_id, current_turn)
    galaxy = storage.load_galaxy(game_id)
    designs = list_all_designs_for_players(storage, game_id, players)

    all_commands = {p: storage.load_commands(game_id, p, current_turn) for p in players}

    new_state = resolve_turn(
        global_state,
        galaxy,
        all_commands,
        designs,
        game_id=game_id,
        storage=storage,
    )
    new_turn = new_state.game.turn

    # Idempotent: if another resolver already wrote this turn, treat as success.
    try:
        storage.create_global_state(game_id, new_turn, new_state)
    except FileExistsError:
        log.warning("resolution.turn_already_exists game_id=%s new_turn=%d", game_id, new_turn)
        directory.turn_resolved(game_id, new_turn)
        return ResolveOutcome(new_turn=new_turn, resolved=True)

    component_catalogue = load_component_catalogue()
    state_ctx = StateContext(game_id, new_state, galaxy, designs, component_catalogue)

    if current_turn == 0:
        designs = list_all_designs_for_players(storage, game_id, players)
        state_ctx = StateContext(game_id, new_state, galaxy, designs, component_catalogue)

    for p in players:
        previous_player_state = (
            None if current_turn == 0 else storage.load_player_state(game_id, p, current_turn)
        )
        ps = derive_player_state(state_ctx, p, previous_player_state=previous_player_state)
        storage.save_player_state(game_id, p, new_turn, ps)

    # GCS writes are durable — now advance the Firestore record.
    directory.turn_resolved(game_id, new_turn)

    return ResolveOutcome(new_turn=new_turn, resolved=True)
