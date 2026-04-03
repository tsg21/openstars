"""Turn 0 generation — create initial game state from galaxy + player list (PRD 05)."""

import random

from openstars.engine.ids import allocate_id
from openstars.engine.models import (
    Cargo,
    Design,
    Fleet,
    FleetComposition,
    Galaxy,
    GameMeta,
    GlobalState,
    Habitability,
    Minerals,
    PlanetState,
    Player,
    Position,
    Scanner,
)

# Seed offsets for per-system RNGs — each distinct to avoid sequence coupling (PRD 04).
_ECON_SEED_OFFSET = 0xEC0_5EED
_POP_SEED_OFFSET = 0xAB_5EED

# Starting values
STARTING_POPULATION = 25000
SCOUT_SPEED = 6  # parsecs per turn
SCOUT_SCANNER_NORMAL = 150  # parsecs — normal (non-penetrating) range
SCOUT_SCANNER_PENETRATING = 0  # parsecs — no penetrating scanner in Phase 1
SMALL_FREIGHTER_SPEED = 6  # parsecs per turn
SMALL_FREIGHTER_CAPACITY = 70  # kT
COLONY_SHIP_SPEED = 6  # parsecs per turn
COLONY_SHIP_CAPACITY = 25  # kT


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
    - Creates three designs (scout + small freighter + colony ship)
      and three fleets per player
    - All other planets start uncolonised

    Args:
        galaxy: The galaxy definition.
        player_usernames: List of player usernames (min 1).
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

    # Generate concentrations for every planet using a seeded RNG distinct from
    # galaxy generation (PRD 04 — use offset to avoid sequence coupling).
    conc_rng = random.Random(game_seed ^ _ECON_SEED_OFFSET)

    def _random_conc() -> int:
        return conc_rng.randint(1, 200)

    # Generate environment values for every planet using a separate seeded RNG.
    pop_rng = random.Random(game_seed ^ _POP_SEED_OFFSET)

    def _random_env() -> int:
        return pop_rng.randint(0, 100)

    # JOAT racial ideal (50 = midpoint of each range)
    _HOME_HABITABILITY = Habitability(gravity=50, temperature=50, radiation=50)

    # Create planet states — home planets get ownership + population
    home_planet_ids = {galaxy.planets[idx].id for idx in home_indices}
    home_planet_owners: dict[str, str] = {}
    for i, idx in enumerate(home_indices):
        # Players are sorted alphabetically; assign home planets in that order
        home_planet_owners[galaxy.planets[idx].id] = players[i].username

    planet_states = []
    for gp in galaxy.planets:
        concentrations = Minerals(
            ironium=_random_conc(),
            boranium=_random_conc(),
            germanium=_random_conc(),
        )
        # Draw environment RNG values for every planet (home planets override below)
        hab = Habitability(
            gravity=_random_env(),
            temperature=_random_env(),
            radiation=_random_env(),
        )
        if gp.id in home_planet_ids:
            concentrations = Minerals(
                ironium=max(concentrations.ironium, 30),
                boranium=max(concentrations.boranium, 30),
                germanium=max(concentrations.germanium, 30),
            )
            planet_states.append(
                PlanetState(
                    id=gp.id,
                    owner=home_planet_owners[gp.id],
                    population=STARTING_POPULATION,
                    mines=10,
                    factories=10,
                    minerals=Minerals(ironium=300, boranium=300, germanium=300),
                    concentrations=concentrations,
                    mine_years=Minerals(),
                    is_homeworld=True,
                    habitability=_HOME_HABITABILITY,
                )
            )
        else:
            planet_states.append(
                PlanetState(
                    id=gp.id,
                    concentrations=concentrations,
                    habitability=hab,
                )
            )

    # Create one scout, one small freighter, and one colony ship design per player
    designs = []
    player_scout_design_id: dict[str, str] = {}
    player_freighter_design_id: dict[str, str] = {}
    player_colony_ship_design_id: dict[str, str] = {}
    for player in players:
        scout_design_id, next_id = allocate_id(next_id, game_seed, "DE")
        designs.append(
            Design(
                id=scout_design_id,
                owner=player.username,
                name="Scout",
                hull="scout",
                speed=SCOUT_SPEED,
                scanner=Scanner(
                    normal=SCOUT_SCANNER_NORMAL,
                    penetrating=SCOUT_SCANNER_PENETRATING,
                ),
            )
        )
        player_scout_design_id[player.username] = scout_design_id

        freighter_design_id, next_id = allocate_id(next_id, game_seed, "DE")
        designs.append(
            Design(
                id=freighter_design_id,
                owner=player.username,
                name="Small Freighter",
                hull="small_freighter",
                speed=SMALL_FREIGHTER_SPEED,
                scanner=Scanner(normal=0, penetrating=0),
                cargo_capacity=SMALL_FREIGHTER_CAPACITY,
            )
        )
        player_freighter_design_id[player.username] = freighter_design_id

        colony_ship_design_id, next_id = allocate_id(next_id, game_seed, "DE")
        designs.append(
            Design(
                id=colony_ship_design_id,
                owner=player.username,
                name="Colony Ship",
                hull="colony_ship",
                speed=COLONY_SHIP_SPEED,
                scanner=Scanner(normal=0, penetrating=0),
                cargo_capacity=COLONY_SHIP_CAPACITY,
            )
        )
        player_colony_ship_design_id[player.username] = colony_ship_design_id

    # Create one scout fleet, one small freighter fleet, and one colony ship fleet
    # per player at the home planet.
    fleets = []
    for i, player in enumerate(players):
        home_planet = galaxy.planets[home_indices[i]]
        scout_fleet_id, next_id = allocate_id(next_id, game_seed, "FL")
        fleets.append(
            Fleet(
                id=scout_fleet_id,
                owner=player.username,
                position=Position(x=home_planet.x, y=home_planet.y),
                composition=[
                    FleetComposition(
                        design_id=player_scout_design_id[player.username],
                        count=1,
                    )
                ],
                cargo=Cargo(),
                waypoints=[],
                repeat=False,
            )
        )
        freighter_fleet_id, next_id = allocate_id(next_id, game_seed, "FL")
        fleets.append(
            Fleet(
                id=freighter_fleet_id,
                owner=player.username,
                position=Position(x=home_planet.x, y=home_planet.y),
                composition=[
                    FleetComposition(design_id=player_freighter_design_id[player.username], count=1)
                ],
                waypoints=[],
                repeat=False,
            )
        )
        colony_ship_fleet_id, next_id = allocate_id(next_id, game_seed, "FL")
        fleets.append(
            Fleet(
                id=colony_ship_fleet_id,
                owner=player.username,
                position=Position(x=home_planet.x, y=home_planet.y),
                composition=[
                    FleetComposition(
                        design_id=player_colony_ship_design_id[player.username],
                        count=1,
                    )
                ],
                cargo=Cargo(),
                waypoints=[],
                repeat=False,
            )
        )

    return GlobalState(
        game=GameMeta(seed=game_seed, turn=0, next_id=next_id),
        players=players,
        designs=designs,
        planets=planet_states,
        fleets=fleets,
    )
