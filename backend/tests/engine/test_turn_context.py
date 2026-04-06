"""Tests for TurnContext initialisation and build_result."""

from openstars.engine.models import (
    Design,
    DesignCost,
    Fleet,
    FleetComposition,
    Galaxy,
    GalaxyMetadata,
    GalaxyPlanet,
    GameMeta,
    GlobalState,
    Habitability,
    Minerals,
    PlanetState,
    Player,
    Position,
    Scanner,
)
from openstars.engine.turn_context import TurnContext


def _make_galaxy(planets: list[GalaxyPlanet] | None = None) -> Galaxy:
    return Galaxy(
        galaxy=GalaxyMetadata(name="test", size="small", seed=0),
        planets=planets or [],
    )


def _make_global_state(
    fleets: list[Fleet] | None = None,
    planets: list[PlanetState] | None = None,
    designs: list[Design] | None = None,
    seed: int = 1,
    turn: int = 0,
    next_id: int = 50,
) -> GlobalState:
    return GlobalState(
        game=GameMeta(seed=seed, turn=turn, next_id=next_id),
        players=[Player(username="tim", name="Tim")],
        designs=designs or [],
        planets=planets or [],
        fleets=fleets or [],
    )


# --- Initialisation ---


def test_fleets_by_id_is_copy():
    fleet = Fleet(
        id="FL000001",
        name="Scout",
        owner="tim",
        position=Position(x=0, y=0),
        composition=[FleetComposition(design_id="DE000001", count=1)],
    )
    gs = _make_global_state(fleets=[fleet])
    ctx = TurnContext(gs, _make_galaxy())
    assert ctx.fleets_by_id["FL000001"] is not fleet


def test_planets_by_id_is_copy():
    planet = PlanetState(
        id="PL000001",
        owner="tim",
        population=100_000,
        habitability=Habitability(gravity=50, temperature=50, radiation=50),
        minerals=Minerals(),
        concentrations=Minerals(ironium=50, boranium=50, germanium=50),
    )
    gs = _make_global_state(planets=[planet])
    ctx = TurnContext(gs, _make_galaxy())
    assert ctx.planets_by_id["PL000001"] is not planet


def test_designs_by_id():
    design = Design(
        id="DE000001",
        owner="tim",
        name="Scout",
        hull="scout",
        speed=6,
        scanner=Scanner(normal=0),
        cost=DesignCost(resources=10, minerals=Minerals()),
    )
    gs = _make_global_state(designs=[design])
    ctx = TurnContext(gs, _make_galaxy())
    assert ctx.designs_by_id["DE000001"] is design


def test_max_coord_small_galaxy():
    ctx = TurnContext(_make_global_state(), _make_galaxy())
    assert ctx.max_coord == (1 << 40) - 1


def test_planet_names_and_coords():
    gp = GalaxyPlanet(id="PL000001", name="Terra", x=100, y=200)
    ctx = TurnContext(_make_global_state(), _make_galaxy(planets=[gp]))
    assert ctx.planet_names == {"PL000001": "Terra"}
    assert ctx.planet_coords == {(100, 200)}
    assert ctx.planet_coordinates_by_id == {"PL000001": (100, 200)}
    assert ctx.planet_coordinates("PL000001") == (100, 200)
    assert ctx.planet_coordinates("PL999999") is None


def test_planets_by_coord_populated():
    gp = GalaxyPlanet(id="PL000001", name="Terra", x=100, y=200)
    planet = PlanetState(
        id="PL000001",
        owner="tim",
        population=100_000,
        habitability=Habitability(gravity=50, temperature=50, radiation=50),
        minerals=Minerals(),
        concentrations=Minerals(ironium=50, boranium=50, germanium=50),
    )
    gs = _make_global_state(planets=[planet])
    ctx = TurnContext(gs, _make_galaxy(planets=[gp]))
    assert (100, 200) in ctx.planets_by_coord


def test_next_id_from_game_meta():
    gs = _make_global_state(next_id=77)
    ctx = TurnContext(gs, _make_galaxy())
    assert ctx._next_id == 77


def test_accumulators_start_empty():
    ctx = TurnContext(_make_global_state(), _make_galaxy())
    assert ctx.owner_events == {}
    assert ctx.planet_resources == {}
    assert ctx.pop_growth == {}
    assert ctx.fleets == []


# --- build_result ---


def test_build_result_increments_turn():
    gs = _make_global_state(turn=3)
    ctx = TurnContext(gs, _make_galaxy())
    result = ctx.build_result()
    assert result.game.turn == 4


def test_build_result_preserves_seed():
    gs = _make_global_state(seed=999)
    ctx = TurnContext(gs, _make_galaxy())
    result = ctx.build_result()
    assert result.game.seed == 999


def test_build_result_uses_updated_next_id():
    gs = _make_global_state(next_id=50)
    ctx = TurnContext(gs, _make_galaxy())
    ctx._next_id = 75
    result = ctx.build_result()
    assert result.game.next_id == 75


def test_build_result_planets_from_working_copy():
    planet = PlanetState(
        id="PL000001",
        owner="tim",
        population=100_000,
        habitability=Habitability(gravity=50, temperature=50, radiation=50),
        minerals=Minerals(),
        concentrations=Minerals(ironium=50, boranium=50, germanium=50),
    )
    gs = _make_global_state(planets=[planet])
    ctx = TurnContext(gs, _make_galaxy())
    ctx.planets_by_id["PL000001"] = planet.model_copy(update={"population": 200_000})
    result = ctx.build_result()
    assert result.planets[0].population == 200_000


def test_build_result_fleets_from_ctx():
    fleet = Fleet(
        id="FL000001",
        name="Scout",
        owner="tim",
        position=Position(x=0, y=0),
        composition=[FleetComposition(design_id="DE000001", count=1)],
    )
    gs = _make_global_state(fleets=[fleet])
    ctx = TurnContext(gs, _make_galaxy())
    moved = fleet.model_copy(update={"position": Position(x=10, y=10)})
    ctx.fleets = [moved]
    result = ctx.build_result()
    assert result.fleets[0].position.x == 10


def test_build_result_events_and_resources():
    gs = _make_global_state()
    ctx = TurnContext(gs, _make_galaxy())
    ctx.owner_events = {"tim": []}
    ctx.planet_resources = {"PL000001": 42}
    ctx.pop_growth = {"PL000001": 1000}
    result = ctx.build_result()
    assert result.events == {"tim": []}
    assert result.planet_resources == {"PL000001": 42}
    assert result.pop_growth == {"PL000001": 1000}
