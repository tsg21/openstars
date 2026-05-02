from openstars.engine.fog import derive_player_state
from openstars.engine.galaxy import LIGHT_YEAR
from openstars.engine.models import (
    Design,
    DesignCost,
    Fleet,
    FleetComposition,
    Galaxy,
    GalaxyMetadata,
    GalaxyPlanet,
    GlobalState,
    Habitability,
    Minerals,
    PlanetState,
    Player,
    Position,
    Scanner,
)
from openstars.engine.race.presets import default_race


def _build_state(*, turn: int, fleet_x: int, target_owner: str | None = "sara") -> GlobalState:
    return GlobalState(
        game={"seed": 1, "turn": turn, "next_id": 1},
        players=[
            Player(username="tim", name="Tim", race=default_race()),
            Player(username="sara", name="Sara", race=default_race()),
        ],
        planets=[
            PlanetState(id="PL-home", owner="tim", population=25000),
            PlanetState(
                id="PL-target",
                owner=target_owner,
                population=12000,
                mines=40,
                factories=30,
                minerals=Minerals(ironium=100, boranium=90, germanium=80),
                concentrations=Minerals(ironium=60, boranium=55, germanium=45),
                habitability=Habitability(gravity=50, temperature=50, radiation=50),
            ),
        ],
        fleets=[
            Fleet(
                id="FLT-1",
                name="Scout",
                owner="tim",
                position=Position(x=fleet_x, y=0),
                composition=[FleetComposition(design_id="tim-scout", count=1)],
            )
        ],
    )


def _build_galaxy() -> Galaxy:
    return Galaxy(
        galaxy=GalaxyMetadata(name="test", size="small", seed=1),
        planets=[
            GalaxyPlanet(id="PL-home", name="Home", x=0, y=0),
            GalaxyPlanet(id="PL-target", name="Target", x=200 * LIGHT_YEAR, y=0),
        ],
    )


def _build_designs(*, penetrating: int = 0) -> list[Design]:
    return [
        Design(
            id="tim-scout",
            owner="tim",
            name="Scout",
            hull="scout",
            mass=1,
            fuel_usage=[1] * 10,
            fuel_capacity=10,
            scanner=Scanner(normal=150, penetrating=penetrating),
            cargo_capacity=0,
            cost=DesignCost(resources=10),
        )
    ]


def test_scanned_planet_becomes_stale_when_out_of_range():
    galaxy = _build_galaxy()
    designs = _build_designs()

    in_range_state = _build_state(turn=2, fleet_x=100 * LIGHT_YEAR)
    previous = derive_player_state(in_range_state, galaxy, "tim", designs)
    previous_target = next(planet for planet in previous.planets if planet.id == "PL-target")
    assert previous_target.scan_level == "basic"

    out_of_range_state = _build_state(turn=3, fleet_x=400 * LIGHT_YEAR)
    current = derive_player_state(
        out_of_range_state,
        galaxy,
        "tim",
        designs,
        previous_player_state=previous,
    )
    target = next(planet for planet in current.planets if planet.id == "PL-target")

    assert target.scan_level == "basic"
    assert target.scan_age == 1


def test_existing_stale_planet_chains_with_incrementing_scan_age():
    galaxy = _build_galaxy()
    designs = _build_designs()

    state_t2 = _build_state(turn=2, fleet_x=100 * LIGHT_YEAR)
    ps_t2 = derive_player_state(state_t2, galaxy, "tim", designs)

    state_t3 = _build_state(turn=3, fleet_x=400 * LIGHT_YEAR)
    ps_t3 = derive_player_state(
        state_t3,
        galaxy,
        "tim",
        designs,
        previous_player_state=ps_t2,
    )

    state_t4 = _build_state(turn=4, fleet_x=430 * LIGHT_YEAR)
    ps_t4 = derive_player_state(
        state_t4,
        galaxy,
        "tim",
        designs,
        previous_player_state=ps_t3,
    )
    target = next(planet for planet in ps_t4.planets if planet.id == "PL-target")

    assert target.scan_level == "basic"
    assert target.scan_age == 2


def test_planet_reentering_scanner_range_clears_stale_status():
    galaxy = _build_galaxy()
    designs = _build_designs()

    state_t2 = _build_state(turn=2, fleet_x=100 * LIGHT_YEAR)
    ps_t2 = derive_player_state(state_t2, galaxy, "tim", designs)

    state_t3 = _build_state(turn=3, fleet_x=400 * LIGHT_YEAR)
    ps_t3 = derive_player_state(
        state_t3,
        galaxy,
        "tim",
        designs,
        previous_player_state=ps_t2,
    )
    target_t3 = next(planet for planet in ps_t3.planets if planet.id == "PL-target")
    assert target_t3.scan_age == 1

    state_t4 = _build_state(turn=4, fleet_x=100 * LIGHT_YEAR)
    ps_t4 = derive_player_state(
        state_t4,
        galaxy,
        "tim",
        designs,
        previous_player_state=ps_t3,
    )
    target_t4 = next(planet for planet in ps_t4.planets if planet.id == "PL-target")

    assert target_t4.scan_level == "basic"
    assert target_t4.scan_age == 0


def test_turn_zero_without_previous_state_keeps_none_for_unscanned_planet():
    galaxy = _build_galaxy()
    designs = _build_designs()

    state = _build_state(turn=0, fleet_x=400 * LIGHT_YEAR)
    player_state = derive_player_state(state, galaxy, "tim", designs, previous_player_state=None)
    target = next(planet for planet in player_state.planets if planet.id == "PL-target")

    assert target.scan_level == "none"
    assert target.scan_age == 0


def test_stale_preserves_fields_from_basic_and_detailed_previous_scans():
    galaxy = _build_galaxy()

    basic_designs = _build_designs(penetrating=0)
    detailed_designs = _build_designs(penetrating=300)

    state_t5 = _build_state(turn=5, fleet_x=100 * LIGHT_YEAR)

    basic_prev = derive_player_state(state_t5, galaxy, "tim", basic_designs)
    basic_stale = derive_player_state(
        _build_state(turn=6, fleet_x=400 * LIGHT_YEAR),
        galaxy,
        "tim",
        basic_designs,
        previous_player_state=basic_prev,
    )
    basic_target = next(planet for planet in basic_stale.planets if planet.id == "PL-target")
    assert basic_target.scan_level == "basic"
    assert basic_target.scan_age == 1
    assert basic_target.owner == "sara"
    assert basic_target.population is None
    assert basic_target.minerals is None
    assert basic_target.habitability is None

    detailed_prev = derive_player_state(state_t5, galaxy, "tim", detailed_designs)
    detailed_stale = derive_player_state(
        _build_state(turn=6, fleet_x=650 * LIGHT_YEAR),
        galaxy,
        "tim",
        detailed_designs,
        previous_player_state=detailed_prev,
    )
    detailed_target = next(planet for planet in detailed_stale.planets if planet.id == "PL-target")
    assert detailed_target.scan_level == "detailed"
    assert detailed_target.scan_age == 1
    assert detailed_target.population == 12000
    assert detailed_target.minerals is not None
    assert detailed_target.habitability is not None
