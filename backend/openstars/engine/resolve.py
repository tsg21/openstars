"""Turn resolution engine (PRD 07).

Phase 1 pipeline:
  1. Apply commands (set_waypoints)
  2. Move fleets
  3. Mining
  4. Calculate resources
  5. Increment turn counter
"""

from openstars.engine import economy
from openstars.engine.models import (
    Fleet,
    Galaxy,
    GameEvent,
    GameMeta,
    GlobalState,
    Minerals,
    PlanetState,
    PlayerCommands,
    Position,
)
from openstars.engine.movement import move_fleet


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
    # Build fleet lookup (mutable copies)
    fleets_by_id: dict[str, Fleet] = {f.id: f.model_copy() for f in global_state.fleets}

    # Build design speed lookup
    design_speeds: dict[str, int] = {d.id: d.speed for d in global_state.designs}

    # Galaxy bounds for validation
    max_coord = _galaxy_max_coord(galaxy)

    # --- Step 1: Apply commands ---
    # Process players alphabetically for determinism
    for username in sorted(all_commands.keys()):
        commands = all_commands[username]
        for cmd in commands.commands:
            if cmd.type == "set_waypoints":
                fleet = fleets_by_id.get(cmd.fleet_id)
                if fleet is None:
                    continue  # Unknown fleet — skip
                if fleet.owner != username:
                    continue  # Not owned by this player — skip

                # Validate waypoint coordinates
                valid_waypoints = []
                for wp in cmd.waypoints:
                    if 0 <= wp.x <= max_coord and 0 <= wp.y <= max_coord:
                        valid_waypoints.append(Position(x=wp.x, y=wp.y))

                # Replace fleet waypoints
                fleets_by_id[cmd.fleet_id] = Fleet(
                    id=fleet.id,
                    owner=fleet.owner,
                    position=fleet.position,
                    composition=fleet.composition,
                    waypoints=valid_waypoints,
                )

    # --- Step 2: Move fleets ---
    # Process fleets sorted by ID for determinism
    moved_fleets = []
    for fleet_id in sorted(fleets_by_id.keys()):
        fleet = fleets_by_id[fleet_id]
        moved = move_fleet(fleet, design_speeds)
        moved_fleets.append(moved)

    # Build planet name lookup from galaxy
    planet_names: dict[str, str] = {gp.id: gp.name for gp in galaxy.planets}

    # Work on mutable planet copies
    planets_by_id: dict[str, PlanetState] = {p.id: p.model_copy() for p in global_state.planets}

    # Per-owner event accumulator
    owner_events: dict[str, list[GameEvent]] = {}

    # --- Step 3: Mining ---
    # Process planets sorted by ID for determinism
    for planet_id in sorted(planets_by_id.keys()):
        planet = planets_by_id[planet_id]
        if planet.owner is None or planet.mines == 0:
            continue

        mines_op = economy.mines_operated(planet.mines, planet.population)
        mined = economy.mine_minerals(mines_op, planet.concentrations)

        new_minerals = Minerals(
            ironium=planet.minerals.ironium + mined.ironium,
            boranium=planet.minerals.boranium + mined.boranium,
            germanium=planet.minerals.germanium + mined.germanium,
        )

        min_conc = 30 if planet.is_homeworld else 1
        new_concs, new_mine_years = economy.deplete_concentrations(planet, mines_op, min_conc)

        planets_by_id[planet_id] = PlanetState(
            id=planet.id,
            owner=planet.owner,
            population=planet.population,
            mines=planet.mines,
            factories=planet.factories,
            minerals=new_minerals,
            concentrations=new_concs,
            mine_years=new_mine_years,
            is_homeworld=planet.is_homeworld,
        )

        event = GameEvent(
            type="mining_complete",
            turn=global_state.game.turn,
            planet_id=planet.id,
            planet_name=planet_names.get(planet.id),
            ironium=mined.ironium,
            boranium=mined.boranium,
            germanium=mined.germanium,
        )
        owner_events.setdefault(planet.owner, []).append(event)

    # --- Step 4: Calculate resources ---
    # Store per-planet resources for use in derive_player_state
    planet_resources: dict[str, int] = {}
    for planet_id in sorted(planets_by_id.keys()):
        planet = planets_by_id[planet_id]
        if planet.owner is None:
            continue
        factories_op = economy.factories_operated(planet.factories, planet.population)
        _, _, total = economy.calculate_resources(planet.population, factories_op)
        planet_resources[planet_id] = total

    # --- Step 5: Increment turn counter ---
    new_turn = global_state.game.turn + 1

    return GlobalState(
        game=GameMeta(
            seed=global_state.game.seed,
            turn=new_turn,
            next_id=global_state.game.next_id,
        ),
        players=global_state.players,
        designs=global_state.designs,
        planets=list(planets_by_id[p.id] for p in global_state.planets),
        fleets=moved_fleets,
        events=owner_events,
        planet_resources=planet_resources,
    )


def _galaxy_max_coord(galaxy: Galaxy) -> int:
    """Get the maximum coordinate value for a galaxy size."""
    from openstars.engine.galaxy import GALAXY_SIZES

    bits = GALAXY_SIZES.get(galaxy.galaxy.size, 40)
    return (1 << bits) - 1
