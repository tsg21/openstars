"""Tests for economy.py and economy integration in setup/resolve/fog (PRD 12)."""

from openstars.engine.fog import derive_player_state
from openstars.engine.galaxy import generate_galaxy
from openstars.engine.models import (
    Design,
    Fleet,
    FleetComposition,
    GameMeta,
    GlobalState,
    Minerals,
    PlanetState,
    Player,
    Position,
    Scanner,
)
from openstars.engine.resolve import resolve_turn
from openstars.engine.resolve_steps import economy
from openstars.engine.setup import create_initial_state

# ---------------------------------------------------------------------------
# Pure unit tests — economy.py
# ---------------------------------------------------------------------------


def test_mines_operated_capped_by_population():
    # 1000 mines, pop=10000 → max = floor(10000/10000)*10 = 10
    assert economy.mines_operated(1000, 10000) == 10


def test_mines_operated_uncapped():
    # 5 mines, pop=100000 → max = 100, so 5 is returned
    assert economy.mines_operated(5, 100_000) == 5


def test_factories_operated_capped():
    # 500 factories, pop=10000 → max = 10
    assert economy.factories_operated(500, 10_000) == 10


def test_mine_minerals_at_concentration_100():
    concs = Minerals(ironium=100, boranium=100, germanium=100)
    result = economy.mine_minerals(10, concs)
    assert result.ironium == 10
    assert result.boranium == 10
    assert result.germanium == 10


def test_mine_minerals_scales_with_concentration():
    concs = Minerals(ironium=50, boranium=50, germanium=50)
    result = economy.mine_minerals(10, concs)
    # floor(10 * 1.0 * 50 / 100) = 5
    assert result.ironium == 5
    assert result.boranium == 5
    assert result.germanium == 5


def test_mine_minerals_floors_result():
    concs = Minerals(ironium=50, boranium=50, germanium=50)
    # floor(3 * 1.0 * 50 / 100) = floor(1.5) = 1
    result = economy.mine_minerals(3, concs)
    assert result.ironium == 1


def test_deplete_concentration_basic():
    # At conc=100, threshold = 12500 // 100 = 125.
    # mine_years starts at 100; adding 100 → 200 >= 125 → concentration drops once.
    planet = PlanetState(
        id="PL000001",
        concentrations=Minerals(ironium=100, boranium=100, germanium=100),
        mine_years=Minerals(ironium=100, boranium=100, germanium=100),
    )
    new_concs, new_mine_years = economy.deplete_concentrations(planet, 100, min_conc=1)
    assert new_concs.ironium == 99
    assert new_mine_years.ironium == 200 - 125  # 75 remaining


def test_deplete_concentration_homeworld_floor():
    # Homeworld concentration at floor (30) — should never drop below 30.
    planet = PlanetState(
        id="PL000001",
        is_homeworld=True,
        concentrations=Minerals(ironium=30, boranium=30, germanium=30),
        mine_years=Minerals(ironium=10000, boranium=10000, germanium=10000),
    )
    new_concs, _ = economy.deplete_concentrations(planet, 10000, min_conc=30)
    assert new_concs.ironium == 30
    assert new_concs.boranium == 30
    assert new_concs.germanium == 30


def test_deplete_concentration_normal_floor():
    # Normal planet concentration at floor (1) — should never drop below 1.
    planet = PlanetState(
        id="PL000001",
        concentrations=Minerals(ironium=1, boranium=1, germanium=1),
        mine_years=Minerals(ironium=100000, boranium=100000, germanium=100000),
    )
    new_concs, _ = economy.deplete_concentrations(planet, 10000, min_conc=1)
    assert new_concs.ironium == 1


def test_deplete_threshold_recalculates():
    # Start conc=100, mine_years=0, add 300:
    # total mine_years=300, threshold=125 → drop to conc=99, mine_years=175
    # new threshold=12500//99=126, 175>=126 → drop to conc=98, mine_years=49
    # new threshold=12500//98=127, 49<127 → stop
    planet = PlanetState(
        id="PL000001",
        concentrations=Minerals(ironium=100, boranium=200, germanium=50),
        mine_years=Minerals(ironium=0, boranium=0, germanium=0),
    )
    new_concs, new_mine_years = economy.deplete_concentrations(planet, 300, min_conc=1)
    assert new_concs.ironium == 98
    assert new_mine_years.ironium == 49


def test_calculate_resources_pop_only():
    pop_res, factory_res, total = economy.calculate_resources(25_000, 0)
    assert pop_res == 25
    assert factory_res == 0
    assert total == 25


def test_calculate_resources_with_factories():
    pop_res, factory_res, total = economy.calculate_resources(25_000, 10)
    assert pop_res == 25
    assert factory_res == 10
    assert total == 35


# ---------------------------------------------------------------------------
# Integration — setup.py
# ---------------------------------------------------------------------------


def _make_game():
    galaxy = generate_galaxy("Test", "small", seed=42, num_planets=20)
    state = create_initial_state(galaxy, ["tim", "sara"], game_seed=12345)
    return galaxy, state


def test_setup_home_planet_has_concentrations():
    _, state = _make_game()
    home_planets = [p for p in state.planets if p.owner is not None]
    for p in home_planets:
        assert p.concentrations.ironium >= 30
        assert p.concentrations.boranium >= 30
        assert p.concentrations.germanium >= 30


def test_setup_other_planets_have_concentrations():
    _, state = _make_game()
    others = [p for p in state.planets if p.owner is None]
    for p in others:
        assert 1 <= p.concentrations.ironium <= 200
        assert 1 <= p.concentrations.boranium <= 200
        assert 1 <= p.concentrations.germanium <= 200


def test_setup_home_planet_economy():
    _, state = _make_game()
    home_planets = [p for p in state.planets if p.owner is not None]
    for p in home_planets:
        assert p.mines == 10
        assert p.factories == 10
        assert p.minerals.ironium == 300
        assert p.minerals.boranium == 300
        assert p.minerals.germanium == 300
        assert p.is_homeworld is True


# ---------------------------------------------------------------------------
# Integration — resolve.py
# ---------------------------------------------------------------------------


def _make_state_with_mines(mines: int = 10, mine_years: Minerals | None = None) -> GlobalState:
    """Minimal 1-planet state with an owned planet that has mines."""
    return GlobalState(
        game=GameMeta(seed=42, turn=0, next_id=10),
        players=[Player(username="tim", name="Tim")],
        designs=[
            Design(
                id="DE000001",
                owner="tim",
                name="Scout",
                hull="scout",
                speed=6,
                scanner=Scanner(normal=150, penetrating=0),
            )
        ],
        planets=[
            PlanetState(
                id="PL000001",
                owner="tim",
                population=250_000,
                mines=mines,
                factories=10,
                minerals=Minerals(ironium=0, boranium=0, germanium=0),
                concentrations=Minerals(ironium=100, boranium=100, germanium=100),
                mine_years=mine_years or Minerals(),
            )
        ],
        fleets=[
            Fleet(
                id="FL000001",
                owner="tim",
                position=Position(x=0, y=0),
                composition=[FleetComposition(design_id="DE000001", count=1)],
                waypoints=[],
            )
        ],
    )


def _make_galaxy():
    return generate_galaxy("Test", "small", seed=42, num_planets=20)


def test_resolve_mining_step():
    """One turn with mines on a planet → surface minerals increase."""
    state = _make_state_with_mines(mines=10)
    galaxy = _make_galaxy()
    new_state = resolve_turn(state, galaxy, {})
    planet = next(p for p in new_state.planets if p.id == "PL000001")
    # mines_op = min(10, floor(250000/10000)*10) = min(10, 250) = 10
    # mined = floor(10 * 1.0 * 100 / 100) = 10 per type
    assert planet.minerals.ironium == 10
    assert planet.minerals.boranium == 10
    assert planet.minerals.germanium == 10


def test_resolve_mining_depletes_concentration():
    """Enough mine-years accumulated → concentration drops."""
    # At conc=100, threshold=125. With mines_op=10 each turn we need 13 turns.
    # Shortcut: start with mine_years=120, mines_op=10 → total=130 >= 125 → drop.
    state = _make_state_with_mines(
        mines=10,
        mine_years=Minerals(ironium=120, boranium=120, germanium=120),
    )
    galaxy = _make_galaxy()
    new_state = resolve_turn(state, galaxy, {})
    planet = next(p for p in new_state.planets if p.id == "PL000001")
    assert planet.concentrations.ironium == 99


def test_resolve_mining_events_generated():
    """mining_complete events appear in the resolved state for the planet owner."""
    state = _make_state_with_mines(mines=10)
    galaxy = _make_galaxy()
    new_state = resolve_turn(state, galaxy, {})
    events = new_state.events.get("tim", [])
    assert len(events) == 1
    ev = events[0]
    assert ev.type == "mining_complete"
    assert ev.planet_id == "PL000001"
    assert ev.ironium == 10
    assert ev.boranium == 10
    assert ev.germanium == 10


def test_resolve_resources_in_player_state():
    """`resources` field is populated for own planets in player state."""
    galaxy = _make_galaxy()
    state = create_initial_state(galaxy, ["tim", "sara"], game_seed=12345)
    new_state = resolve_turn(state, galaxy, {})
    ps = derive_player_state(new_state, galaxy, "tim")
    own_planet = next(p for p in ps.planets if p.owner == "tim")
    # pop = 25000 → pop_resources = 25; factories_op = min(10, 25) = 10 → factory_resources = 10
    assert own_planet.resources == 35


# ---------------------------------------------------------------------------
# Integration — fog.py economy visibility
# ---------------------------------------------------------------------------


def _make_fog_state(pen_range: int = 0) -> tuple[GlobalState, object]:
    """State with Tim's fleet near Sara's planet; scanner range configurable."""
    galaxy = generate_galaxy("Test", "small", seed=42, num_planets=20)
    state = GlobalState(
        game=GameMeta(seed=42, turn=1, next_id=10),
        players=[
            Player(username="tim", name="Tim"),
            Player(username="sara", name="Sara"),
        ],
        designs=[
            Design(
                id="DE000001",
                owner="tim",
                name="Scout",
                hull="scout",
                speed=6,
                scanner=Scanner(normal=150, penetrating=pen_range),
            )
        ],
        planets=[
            PlanetState(
                id=galaxy.planets[0].id,
                owner="sara",
                population=25_000,
                mines=5,
                factories=5,
                minerals=Minerals(ironium=50, boranium=60, germanium=70),
                concentrations=Minerals(ironium=80, boranium=90, germanium=100),
            )
        ],
        fleets=[
            Fleet(
                id="FL000001",
                owner="tim",
                position=Position(x=galaxy.planets[0].x, y=galaxy.planets[0].y),
                composition=[FleetComposition(design_id="DE000001", count=1)],
                waypoints=[],
            )
        ],
        planet_resources={galaxy.planets[0].id: 30},
    )
    return state, galaxy


def test_fog_economy_detailed_scan():
    """Enemy planet in penetrating scanner range exposes economy data."""
    state, galaxy = _make_fog_state(pen_range=150)
    ps = derive_player_state(state, galaxy, "tim")
    planet = next(p for p in ps.planets if p.owner == "sara")
    assert planet.scan_level == "detailed"
    assert planet.mines == 5
    assert planet.factories == 5
    assert planet.minerals is not None
    assert planet.concentrations is not None
    assert planet.resources == 30


def test_fog_economy_basic_scan():
    """Enemy planet in basic (non-penetrating) scanner range hides economy data."""
    state, galaxy = _make_fog_state(pen_range=0)
    ps = derive_player_state(state, galaxy, "tim")
    planet = next(p for p in ps.planets if p.owner == "sara")
    assert planet.scan_level == "basic"
    assert planet.mines is None
    assert planet.factories is None
    assert planet.minerals is None
    assert planet.concentrations is None
    assert planet.resources is None
