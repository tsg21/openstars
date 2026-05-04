"""Turn-0 race selection and starting-state materialisation."""

import math
from dataclasses import dataclass

from openstars.engine.designs import build_design
from openstars.engine.models import (
    Cargo,
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
from openstars.engine.race.models import PRT, Race, ResearchCostProfile
from openstars.engine.resolve_steps.commands.select_race import (
    RACE_REVALIDATION_FAILED,
    apply_select_race_command,
)
from openstars.engine.turn_context import TurnContext
from openstars.server.errors import GameError
from openstars.storage.base import GameStorage

STARTING_POPULATION = 25_000
TURN_ZERO_INCOMPLETE = "TURN_ZERO_INCOMPLETE"


@dataclass
class _StartingShip:
    fleet_name: str
    hull_id: str
    components: list[dict]


_SCOUT_COMPONENTS = [
    {"slot_number": 1, "component_id": "quick_jump_5", "component_count": 1},
    {"slot_number": 2, "component_id": "bat_scanner", "component_count": 1},
]
_ENGINE_ONLY_COMPONENTS = [
    {"slot_number": 1, "component_id": "quick_jump_5", "component_count": 1},
]


def _joat_starting_ships(construction_level: int) -> list[_StartingShip]:
    freighter_hull = "privateer" if construction_level >= 4 else "medium_freighter"
    freighter_name = "Privateer" if construction_level >= 4 else "Medium Freighter"
    return [
        _StartingShip("Scout", "scout", _SCOUT_COMPONENTS),
        _StartingShip("Scout", "scout", _SCOUT_COMPONENTS),
        _StartingShip("Colony Ship", "colony_ship", _ENGINE_ONLY_COMPONENTS),
        _StartingShip(freighter_name, freighter_hull, _ENGINE_ONLY_COMPONENTS),
        _StartingShip("Mini Miner", "mini_miner", _ENGINE_ONLY_COMPONENTS),
        _StartingShip("Destroyer", "destroyer", _ENGINE_ONLY_COMPONENTS),
    ]


def _starting_ships(race: Race, construction_level: int) -> list[_StartingShip]:
    if race.prt == PRT.JACK_OF_ALL_TRADES:
        return _joat_starting_ships(construction_level)
    raise ValueError(f"Starting fleet not defined for PRT {race.prt}")


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


def _apply_starting_tech_levels(ctx: TurnContext, username: str, race: Race) -> None:
    """Set research levels for turn-0 based on PRT and the start_at_tech_3 accelerator."""
    state = ctx.research_state_by_username[username]
    new_levels = dict(state.levels)

    if race.prt == PRT.JACK_OF_ALL_TRADES:
        for field in new_levels:
            new_levels[field] = max(new_levels[field], 3)

    if race.research.start_at_tech_3:
        target = 4 if race.prt == PRT.JACK_OF_ALL_TRADES else 3
        for field, profile in race.research.field_profile.items():
            if profile == ResearchCostProfile.EXPENSIVE:
                new_levels[field] = max(new_levels[field], target)

    ctx.research_state_by_username[username] = state.model_copy(update={"levels": new_levels})


def _build_starting_fleet(
    ctx: TurnContext,
    username: str,
    home_x: int,
    home_y: int,
    ships: list[_StartingShip],
    storage: GameStorage,
) -> None:
    """Create one design per unique hull in `ships`, then one fleet per ship."""
    research_state = ctx.research_state_by_username[username]
    designs_by_hull: dict[str, str] = {}  # hull_id -> design_id

    for ship in ships:
        if ship.hull_id not in designs_by_hull:
            design = build_design(
                design_id=ctx.allocate_id("DE"),
                owner=username,
                name=ship.fleet_name,
                hull_id=ship.hull_id,
                components=ship.components,
                catalogue=ctx.component_catalogue,
                player_levels=research_state.levels,
            )
            ctx.designs_by_id[design.id] = design
            storage.save_design(ctx.game_id, username, design)
            designs_by_hull[ship.hull_id] = design.id

    for ship in ships:
        design_id = designs_by_hull[ship.hull_id]
        design = ctx.designs_by_id[design_id]
        ctx.fleets.append(
            Fleet(
                id=ctx.allocate_id("FL"),
                name=ship.fleet_name,
                owner=username,
                position=Position(x=home_x, y=home_y),
                composition=[FleetComposition(design_id=design_id, count=1)],
                cargo=Cargo(),
                fuel=design.fuel_capacity,
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

        _apply_starting_tech_levels(ctx, username, race)
        construction_level = ctx.research_state_by_username[username].levels["construction"]
        ships = _starting_ships(race, construction_level)
        _build_starting_fleet(
            ctx, username, home_planet_static.x, home_planet_static.y, ships, storage
        )
        ctx.append_event(
            GameEvent(owner=username, source_id=None, code="race.saved", values=[race.prt])
        )
