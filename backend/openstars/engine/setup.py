"""Turn 0 generation — create initial game state from galaxy + player list (PRD 05)."""

from openstars.engine.ids import allocate_id
from openstars.engine.models import (
    Design,
    Fleet,
    FleetComposition,
    Galaxy,
    GameMeta,
    GlobalState,
    PlanetState,
    Player,
    Position,
)

# Starting values
STARTING_POPULATION = 25000
SCOUT_SPEED = 6  # parsecs per turn
SCOUT_SCANNER_RANGE = 150  # parsecs


def _assign_home_planets(galaxy: Galaxy, num_players: int, game_seed: int) -> list[int]:
    """Select home planets that maximise minimum distance between them.

    Uses a greedy algorithm: pick the planet farthest from all previously
    selected home planets. First pick is deterministic from the game seed.
    Returns indices into galaxy.planets.
    """
    planets = galaxy.planets
    n = len(planets)

    if num_players > n:
        raise ValueError(f"More players ({num_players}) than planets ({n})")

    # First home planet: pick based on game seed
    first_idx = game_seed % n
    selected = [first_idx]

    for _ in range(1, num_players):
        best_idx = -1
        best_min_dist_sq = -1

        for i in range(n):
            if i in selected:
                continue

            # Find minimum distance to any already-selected home planet
            min_dist_sq = -1
            for s in selected:
                dx = planets[i].x - planets[s].x
                dy = planets[i].y - planets[s].y
                dist_sq = dx * dx + dy * dy
                if min_dist_sq < 0 or dist_sq < min_dist_sq:
                    min_dist_sq = dist_sq

            if min_dist_sq > best_min_dist_sq:
                best_min_dist_sq = min_dist_sq
                best_idx = i

        selected.append(best_idx)

    return selected


def create_initial_state(
    galaxy: Galaxy,
    player_usernames: list[str],
    game_seed: int,
) -> GlobalState:
    """Create the Turn 0 global state.

    - Assigns home planets (spread across galaxy)
    - Sets ownership and starting population on home planets
    - Creates one scout design + one scout fleet per player
    - All other planets start uncolonised

    Args:
        galaxy: The galaxy definition.
        player_usernames: List of player usernames (min 2).
        game_seed: Game seed for ID generation and determinism.

    Returns:
        GlobalState for turn 0.
    """
    # The galaxy seed is used for planet IDs; the game seed is used for
    # designs, fleets, and all subsequent entities. next_id continues from
    # where galaxy generation left off.
    next_id = len(galaxy.planets)

    # Assign home planets
    home_indices = _assign_home_planets(galaxy, len(player_usernames), game_seed)

    # Create player entries (use username as display name for now)
    players = [Player(username=u, name=u) for u in sorted(player_usernames)]

    # Create planet states — home planets get ownership + population
    home_planet_ids = {galaxy.planets[idx].id for idx in home_indices}
    home_planet_owners: dict[str, str] = {}
    for i, idx in enumerate(home_indices):
        # Players are sorted alphabetically; assign home planets in that order
        home_planet_owners[galaxy.planets[idx].id] = players[i].username

    planet_states = []
    for gp in galaxy.planets:
        if gp.id in home_planet_ids:
            planet_states.append(
                PlanetState(
                    id=gp.id,
                    owner=home_planet_owners[gp.id],
                    population=STARTING_POPULATION,
                )
            )
        else:
            planet_states.append(PlanetState(id=gp.id))

    # Create one scout design per player
    designs = []
    for player in players:
        design_id, next_id = allocate_id(next_id, game_seed, "DE")
        designs.append(
            Design(
                id=design_id,
                owner=player.username,
                name="Scout",
                hull="scout",
                speed=SCOUT_SPEED,
                scanner_range=SCOUT_SCANNER_RANGE,
            )
        )

    # Create one scout fleet per player at their home planet
    fleets = []
    for i, player in enumerate(players):
        home_planet = galaxy.planets[home_indices[i]]
        fleet_id, next_id = allocate_id(next_id, game_seed, "FL")
        # Find the design for this player
        player_design = next(d for d in designs if d.owner == player.username)
        fleets.append(
            Fleet(
                id=fleet_id,
                owner=player.username,
                position=Position(x=home_planet.x, y=home_planet.y),
                composition=[FleetComposition(design_id=player_design.id, count=1)],
                waypoints=[],
            )
        )

    return GlobalState(
        game=GameMeta(seed=game_seed, turn=0, next_id=next_id),
        players=players,
        designs=designs,
        planets=planet_states,
        fleets=fleets,
    )
