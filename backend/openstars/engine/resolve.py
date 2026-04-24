"""Turn resolution engine (PRD 07).

Phase 1 pipeline:
  1. Apply commands
  2. Move fleets
  3. Mining
  4. Calculate resources
  5. Production
  6. Population growth / death
  7. Increment turn counter
"""

import logging

from openstars.engine.component_catalogue import load_component_catalogue
from openstars.engine.models import (
    Design,
    Galaxy,
    GlobalState,
    PlayerCommands,
)
from openstars.engine.resolve_steps.apply_commands import apply_commands
from openstars.engine.resolve_steps.combat import resolve_combat
from openstars.engine.resolve_steps.mining import mine_planets
from openstars.engine.resolve_steps.movement import move_fleets
from openstars.engine.resolve_steps.population import grow_population
from openstars.engine.resolve_steps.production import resolve_production
from openstars.engine.resolve_steps.research import resolve_research
from openstars.engine.resolve_steps.resources import calculate_planet_resources
from openstars.engine.turn_context import TurnContext
from openstars.server.log_context import turn
from openstars.storage.base import GameStorage

log = logging.getLogger(__name__)


def resolve_turn(
    global_state: GlobalState,
    galaxy: Galaxy,
    all_commands: dict[str, PlayerCommands],
    designs: list[Design],
    *,
    game_id: str,
    storage: GameStorage,
) -> GlobalState:
    """Resolve one turn.

    Args:
        global_state: Current game state.
        galaxy: Galaxy definition (static).
        all_commands: Mapping of username → PlayerCommands.
        designs: All ship designs for players in this game (registry snapshot).
        game_id: Game identifier for storage of combat logs etc.
        storage: Storage backend for persisting combat logs.

    Returns:
        New GlobalState for the next turn.
    """

    token = turn.set(global_state.game.turn)
    try:
        component_catalogue = load_component_catalogue()
        ctx = TurnContext(game_id, global_state, galaxy, designs, component_catalogue)

        log.debug("resolve turn: applying commands")
        apply_commands(ctx, all_commands)

        log.debug("resolve turn: moving fleets")
        move_fleets(ctx)

        log.debug("resolve turn: combat")
        resolve_combat(ctx, storage)

        log.debug("resolve turn: mining")
        mine_planets(ctx)

        # Step 4: Calculate resources
        calculate_planet_resources(ctx)

        log.debug("resolve turn: production")
        resolve_production(ctx)

        log.debug("resolve turn: research")
        resolve_research(ctx)

        log.debug("resolve turn: population growth")
        grow_population(ctx)

        return ctx.build_result()
    finally:
        turn.reset(token)
