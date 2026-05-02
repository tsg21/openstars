"""Turn 0 generation — create the race-selection game state (PRD 05)."""

import random

from openstars.engine.models import (
    Design,
    Galaxy,
    GameMeta,
    GlobalState,
    Habitability,
    Minerals,
    PlanetState,
    Player,
    default_research_state,
)
from openstars.storage.base import GameStorage

# Seed offsets for per-system RNGs — each distinct to avoid sequence coupling (PRD 04).
_ECON_SEED_OFFSET = 0xEC0_5EED
_POP_SEED_OFFSET = 0xAB_5EED

# Starting values are materialised during turn-0 resolution.
STARTING_POPULATION = 25_000


def create_initial_state(
    galaxy: Galaxy,
    player_usernames: list[str],
    game_seed: int,
) -> tuple[GlobalState, list[Design]]:
    """Create the bare Turn 0 race-selection state.

    Homeworld ownership, population, installations, starting designs, and
    starting fleets are materialised by turn-0 resolution after each player
    submits a race selection.
    """
    next_id = len(galaxy.planets)
    players = [
        Player(username=username, name=username, race=None, research_state=default_research_state())
        for username in sorted(player_usernames)
    ]

    conc_rng = random.Random(game_seed ^ _ECON_SEED_OFFSET)
    pop_rng = random.Random(game_seed ^ _POP_SEED_OFFSET)

    planet_states = [
        PlanetState(
            id=planet.id,
            concentrations=Minerals(
                ironium=conc_rng.randint(1, 200),
                boranium=conc_rng.randint(1, 200),
                germanium=conc_rng.randint(1, 200),
            ),
            habitability=Habitability(
                gravity=pop_rng.randint(0, 100),
                temperature=pop_rng.randint(0, 100),
                radiation=pop_rng.randint(0, 100),
            ),
        )
        for planet in galaxy.planets
    ]

    return (
        GlobalState(
            game=GameMeta(seed=game_seed, turn=0, next_id=next_id, combat_ruleset="altair"),
            players=players,
            planets=planet_states,
            fleets=[],
        ),
        [],
    )


def seed_player_design_registry(
    storage: GameStorage,
    game_id: str,
    designs: list[Design],
) -> None:
    """Persist starting (or other) player designs in the dedicated design registry."""
    for design in designs:
        storage.save_design(game_id, design.owner, design)
