"""Turn-0 race selection and starting-state materialisation."""

import math

from openstars.engine.designs import build_design
from openstars.engine.models import (
    Cargo,
    Design,
    Fleet,
    FleetComposition,
    Galaxy,
    GameEvent,
    Habitability,
    Minerals,
    PlanetStarbaseState,
    PlayerCommands,
    Position,
    SelectRaceCommand,
)
from openstars.engine.race.costs import RaceValidationError
from openstars.engine.resolve_steps.commands.select_race import (
    RACE_REVALIDATION_FAILED,
    apply_select_race_command,
)
from openstars.engine.turn_context import TurnContext
from openstars.server.errors import GameError
from openstars.storage.base import GameStorage

STARTING_POPULATION = 25_000
TURN_ZERO_INCOMPLETE = "TURN_ZERO_INCOMPLETE"

_STARTING_SCOUT_COMPONENTS = [
    {"slot_number": 1, "component_id": "quick_jump_5", "component_count": 1},
    {"slot_number": 2, "component_id": "bat_scanner", "component_count": 1},
]
_STARTING_SMALL_FREIGHTER_COMPONENTS = [
    {"slot_number": 1, "component_id": "quick_jump_5", "component_count": 1},
]
_STARTING_COLONY_SHIP_COMPONENTS = [
    {"slot_number": 1, "component_id": "quick_jump_5", "component_count": 1},
]


def _assign_home_planets(galaxy: Galaxy, num_players: int, game_seed: int) -> list[int]:
    """Select home planets that maximise minimum distance between them."""
    planets = galaxy.planets
    n = len(planets)
    if num_players > n:
        raise ValueError(f"More players ({num_players}) than planets ({n})")

    selected = [game_seed % n]
    for _ in range(1, num_players):
        best_idx = -1
        best_min_dist_sq = -1
        for i in range(n):
            if i in selected:
                continue
            min_dist_sq = min(
                (planets[i].x - planets[s].x) ** 2 + (planets[i].y - planets[s].y) ** 2
                for s in selected
            )
            if min_dist_sq > best_min_dist_sq:
                best_min_dist_sq = min_dist_sq
                best_idx = i
        selected.append(best_idx)
    return selected


def _last_select_race_command(commands: PlayerCommands | None) -> SelectRaceCommand | None:
    if commands is None:
        return None
    selected = None
    for command in commands.commands:
        if isinstance(command, SelectRaceCommand):
            selected = command
    return selected


def _home_habitability_from_race(race, random_habitability: Habitability) -> Habitability:
    values = {}
    for field_name in ("gravity", "temperature", "radiation"):
        factor = getattr(race.habitability, field_name)
        if factor.immune:
            values[field_name] = getattr(random_habitability, field_name)
        else:
            low, high = factor.range
            values[field_name] = math.floor((low + high) / 2)
    return Habitability(**values)


def _build_starting_designs(ctx: TurnContext, username: str) -> list[Design]:
    research_state = ctx.research_state_by_username[username]
    design_specs = (
        ("Scout", "scout", _STARTING_SCOUT_COMPONENTS),
        ("Small Freighter", "small_freighter", _STARTING_SMALL_FREIGHTER_COMPONENTS),
        ("Colony Ship", "colony_ship", _STARTING_COLONY_SHIP_COMPONENTS),
    )
    designs = []
    for name, hull_id, components in design_specs:
        design = build_design(
            design_id=ctx.allocate_id("DE"),
            owner=username,
            name=name,
            hull_id=hull_id,
            components=components,
            catalogue=ctx.component_catalogue,
            player_levels=research_state.levels,
        )
        designs.append(design)
        ctx.designs_by_id[design.id] = design
    return designs


def _build_starting_fleets(
    ctx: TurnContext,
    username: str,
    home_x: int,
    home_y: int,
    scout_design: Design,
    freighter_design: Design,
    colony_ship_design: Design,
) -> None:
    for scout_index in range(2):
        ctx.fleets.append(
            Fleet(
                id=ctx.allocate_id("FL"),
                name=f"Fleet #{scout_index + 1}",
                owner=username,
                position=Position(x=home_x, y=home_y),
                composition=[FleetComposition(design_id=scout_design.id, count=1)],
                cargo=Cargo(),
                fuel=scout_design.fuel_capacity,
                waypoints=[],
                repeat=False,
                bearing=None,
            )
        )

    ctx.fleets.append(
        Fleet(
            id=ctx.allocate_id("FL"),
            name="Fleet #3",
            owner=username,
            position=Position(x=home_x, y=home_y),
            composition=[FleetComposition(design_id=freighter_design.id, count=1)],
            waypoints=[],
            fuel=freighter_design.fuel_capacity,
            repeat=False,
            bearing=None,
        )
    )
    ctx.fleets.append(
        Fleet(
            id=ctx.allocate_id("FL"),
            name="Fleet #4",
            owner=username,
            position=Position(x=home_x, y=home_y),
            composition=[FleetComposition(design_id=colony_ship_design.id, count=1)],
            cargo=Cargo(),
            fuel=colony_ship_design.fuel_capacity,
            waypoints=[],
            repeat=False,
            bearing=None,
        )
    )


def resolve_turn_zero(
    ctx: TurnContext,
    all_commands: dict[str, PlayerCommands],
    storage: GameStorage,
) -> None:
    """Resolve the race-selection phase and materialise starting assets."""
    usernames = sorted(player.username for player in ctx.global_state.players)
    home_indices = _assign_home_planets(ctx.galaxy, len(usernames), ctx.global_state.game.seed)
    home_planet_id_by_username = {
        username: ctx.galaxy.planets[home_indices[index]].id
        for index, username in enumerate(usernames)
    }

    for username, planet_id in home_planet_id_by_username.items():
        planet = ctx.planets_by_id[planet_id]
        planet.owner = username
        planet.is_homeworld = True
        planet.concentrations = Minerals(
            ironium=max(planet.concentrations.ironium, 30),
            boranium=max(planet.concentrations.boranium, 30),
            germanium=max(planet.concentrations.germanium, 30),
        )

    for username in usernames:
        command = _last_select_race_command(all_commands.get(username))
        if command is None:
            raise GameError(
                409,
                TURN_ZERO_INCOMPLETE,
                f"Player {username} has not submitted a race selection",
            )
        try:
            apply_select_race_command(ctx, username, command)
        except RaceValidationError as exc:
            raise GameError(
                409,
                RACE_REVALIDATION_FAILED,
                f"Race selection for {username} no longer validates: {exc.detail}",
            ) from exc

        race = ctx.race_by_username[username]
        planet_id = home_planet_id_by_username[username]
        home_planet_state = ctx.planets_by_id[planet_id]
        home_planet_static = next(planet for planet in ctx.galaxy.planets if planet.id == planet_id)
        home_planet_state.habitability = _home_habitability_from_race(
            race, home_planet_state.habitability
        )
        home_planet_state.population = STARTING_POPULATION
        home_planet_state.mines = 10
        home_planet_state.factories = 10
        home_planet_state.minerals = Minerals(ironium=300, boranium=300, germanium=300)
        home_planet_state.starbase = PlanetStarbaseState(type="space_station", can_build_ships=True)

        designs = _build_starting_designs(ctx, username)
        for design in designs:
            storage.save_design(ctx.game_id, username, design)
        _build_starting_fleets(
            ctx,
            username,
            home_planet_static.x,
            home_planet_static.y,
            next(design for design in designs if design.hull == "scout"),
            next(design for design in designs if design.hull == "small_freighter"),
            next(design for design in designs if design.hull == "colony_ship"),
        )
        ctx.append_event(
            GameEvent(owner=username, source_id=None, code="race.saved", values=[race.prt])
        )
