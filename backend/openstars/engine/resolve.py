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

from openstars.engine.models import (
    Galaxy,
    GameMeta,
    GlobalState,
    PlanetState,
    PlayerCommands,
)
from openstars.engine.resolve_steps.commands import apply_commands, galaxy_max_coord
from openstars.engine.resolve_steps.mining import mine_planets
from openstars.engine.resolve_steps.movement import move_fleets
from openstars.engine.resolve_steps.population import grow_population
from openstars.engine.resolve_steps.production import resolve_production
from openstars.engine.resolve_steps.resources import calculate_planet_resources


def resolve_turn(
    global_state: GlobalState,
    galaxy: Galaxy,
    all_commands: dict[str, PlayerCommands],
) -> GlobalState:
    """Resolve one turn.

    Args:
        global_state: Current game state.
        galaxy: Galaxy definition (static).
        all_commands: Mapping of username → PlayerCommands.

    Returns:
        New GlobalState for the next turn.
    """
    fleets_by_id = {f.id: f.model_copy() for f in global_state.fleets}
    design_speeds = {d.id: d.speed for d in global_state.designs}
    designs_by_id = {d.id: d for d in global_state.designs}
    max_coord = galaxy_max_coord(galaxy)
    planet_coords = {(gp.x, gp.y) for gp in galaxy.planets}
    planet_names = {gp.id: gp.name for gp in galaxy.planets}
    planets_by_id: dict[str, PlanetState] = {p.id: p.model_copy() for p in global_state.planets}
    planets_by_coord = {
        (gp.x, gp.y): planets_by_id[gp.id] for gp in galaxy.planets if gp.id in planets_by_id
    }

    # Step 1: Apply commands
    next_id = apply_commands(
        fleets_by_id,
        planets_by_id,
        planet_coords,
        all_commands,
        max_coord,
        global_state.game.seed,
        global_state.game.next_id,
    )

    # Step 2: Move fleets
    moved_fleets = move_fleets(
        fleets_by_id,
        design_speeds,
        planets_by_coord,
        designs_by_id,
        planets_by_id,
    )

    # Step 3: Mining
    owner_events = mine_planets(planets_by_id, planet_names, global_state.game.turn)

    # Step 4: Calculate resources
    planet_resources = calculate_planet_resources(planets_by_id)

    # Step 5: Production
    production_events = resolve_production(
        planets_by_id,
        planet_resources,
        planet_names,
        global_state.game.turn,
    )
    for owner, events in production_events.items():
        owner_events.setdefault(owner, []).extend(events)

    # Step 6: Population growth / death
    pop_events, pop_growth = grow_population(planets_by_id, planet_names, global_state.game.turn)
    for owner, events in pop_events.items():
        owner_events.setdefault(owner, []).extend(events)

    # Step 7: Increment turn counter
    return GlobalState(
        game=GameMeta(
            seed=global_state.game.seed,
            turn=global_state.game.turn + 1,
            next_id=next_id,
        ),
        players=global_state.players,
        designs=global_state.designs,
        planets=[planets_by_id[p.id] for p in global_state.planets],
        fleets=moved_fleets,
        events=owner_events,
        planet_resources=planet_resources,
        pop_growth=pop_growth,
    )
