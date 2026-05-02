"""Tests for turn resolution and fleet movement."""

from openstars.engine.component_catalogue import load_component_catalogue
from openstars.engine.galaxy import generate_galaxy
from openstars.engine.models import (
    AddProductionItemCommand,
    Cargo,
    ClearProductionQueueCommand,
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
    MoveProductionItemCommand,
    PlanetState,
    Player,
    PlayerCommands,
    Position,
    ProductionProgress,
    ProductionQueueItem,
    RemoveProductionItemCommand,
    RenameFleetCommand,
    Scanner,
    SetWaypointsCommand,
    Waypoint,
    WaypointTask,
)
from openstars.engine.race.presets import default_race
from openstars.engine.resolve import resolve_turn
from openstars.engine.resolve_steps.apply_commands import apply_commands
from openstars.engine.resolve_steps.movement import LIGHT_YEAR, isqrt, move_fleet
from openstars.engine.turn_context import TurnContext
from openstars.storage.memory import MemoryStorage
from tests.engine.race._helpers import submit_default_race_and_resolve_turn_0

_GOOD_HAB = Habitability(gravity=50, temperature=50, radiation=50)
_TEST_DESIGN_COST = DesignCost(resources=10, minerals=Minerals())
_TEST_ENGINE_FUEL_USAGE = [0, 15, 35, 45, 55, 70, 80, 90, 100, 120]
_CATALOGUE = load_component_catalogue()
_SCOUT_HULL_MASS = _CATALOGUE.by_id["scout"].mass
_COLONY_SHIP_HULL_MASS = _CATALOGUE.by_id["colony_ship"].mass
_JOAT_RACE = default_race()

# Default designs for `_make_state` / `_rt` resolution tests (Tim + Sara scouts).
_RESOLVE_PAIR_DESIGNS: list[Design] = [
    Design(
        id="DE000001",
        owner="tim",
        name="Scout",
        hull="scout",
        mass=_SCOUT_HULL_MASS + 4,
        fuel_usage=_TEST_ENGINE_FUEL_USAGE,
        fuel_capacity=100,
        scanner=Scanner(normal=150, penetrating=0),
        cost=_TEST_DESIGN_COST,
    ),
    Design(
        id="DE000002",
        owner="sara",
        name="Scout",
        hull="scout",
        mass=_SCOUT_HULL_MASS + 4,
        fuel_usage=_TEST_ENGINE_FUEL_USAGE,
        fuel_capacity=100,
        scanner=Scanner(normal=150, penetrating=0),
        cost=_TEST_DESIGN_COST,
    ),
]


def _rt(
    global_state: GlobalState,
    galaxy: Galaxy,
    all_commands: dict[str, PlayerCommands] | None = None,
    *,
    designs: list[Design] | None = None,
) -> GlobalState:
    return resolve_turn(
        global_state,
        galaxy,
        all_commands or {},
        designs if designs is not None else _RESOLVE_PAIR_DESIGNS,
        game_id="game1",
        storage=MemoryStorage(),
    )


# --- isqrt tests ---


def test_isqrt_zero():
    assert isqrt(0) == 0


def test_isqrt_perfect_squares():
    assert isqrt(1) == 1
    assert isqrt(4) == 2
    assert isqrt(9) == 3
    assert isqrt(100) == 10
    assert isqrt(10000) == 100


def test_isqrt_non_perfect():
    assert isqrt(2) == 1
    assert isqrt(3) == 1
    assert isqrt(5) == 2
    assert isqrt(99) == 9


def test_isqrt_large():
    # Large coordinate values
    val = (1 << 40) * (1 << 40)
    assert isqrt(val) == 1 << 40


# --- Fleet movement tests ---


def _make_design(design_id: str, fuel_usage: list[int] | None = None) -> Design:
    return Design(
        id=design_id,
        owner="tim",
        name="Test",
        hull="scout",
        mass=_SCOUT_HULL_MASS + 4,
        fuel_usage=fuel_usage or _TEST_ENGINE_FUEL_USAGE,
        fuel_capacity=100,
        scanner=Scanner(normal=0, penetrating=0),
        cost=DesignCost(resources=10, minerals=Minerals()),
    )


def _make_fleet(
    x: int,
    y: int,
    waypoints: list[tuple[int, int]],
    fleet_id: str = "FL000001",
) -> Fleet:
    return Fleet(
        id=fleet_id,
        name="Fleet #1",
        owner="tim",
        position=Position(x=x, y=y),
        composition=[FleetComposition(design_id="DE000001", count=1)],
        waypoints=[Waypoint(x=wx, y=wy, warp=6) for wx, wy in waypoints],
        fuel=200,
    )


def _make_move_ctx(
    fleet: Fleet,
    designs: dict[str, Design],
    planets: list[PlanetState] | None = None,
    galaxy_planets: list[GalaxyPlanet] | None = None,
) -> TurnContext:
    return TurnContext(
        "game1",
        GlobalState(
            game=GameMeta(seed=42, turn=0, next_id=100),
            players=[
                Player(username="tim", name="Tim", race=_JOAT_RACE),
                Player(username="sara", name="Sara", race=default_race()),
            ],
            planets=planets or [],
            fleets=[fleet],
        ),
        Galaxy(
            galaxy=GalaxyMetadata(name="Test", size="small", seed=42),
            planets=galaxy_planets or [],
        ),
        list(designs.values()),
        _CATALOGUE,
    )


def test_stationary_fleet():
    """Fleet with no waypoints doesn't move."""
    fleet = _make_fleet(100, 200, [])
    ctx = _make_move_ctx(fleet, {"DE000001": _make_design("DE000001")})
    moved, events = move_fleet(ctx, fleet)
    assert events == []
    assert moved.position.x == 100
    assert moved.position.y == 200


def test_fleet_moves_toward_waypoint():
    """Fleet moves toward its waypoint."""
    # Place fleet at origin, waypoint far away along x-axis
    start_x = 549755813888
    target_x = start_x + 100 * LIGHT_YEAR  # 100 light-years away
    fleet = _make_fleet(start_x, 0, [(target_x, 0)])
    ctx = _make_move_ctx(fleet, {"DE000001": _make_design("DE000001")})
    moved, events = move_fleet(ctx, fleet)
    assert events == []
    # Warp-6 moves 36 light-years toward target.
    expected_x = start_x + 36 * LIGHT_YEAR
    assert moved.position.x == expected_x
    assert moved.position.y == 0
    assert len(moved.waypoints) == 1  # Not yet arrived
    assert moved.bearing == 90.0


def test_fleet_arrives_at_waypoint():
    """Fleet arrives when close enough."""
    start_x = 0
    target_x = 3 * LIGHT_YEAR  # 3 light-years away, speed is 6
    fleet = _make_fleet(start_x, 0, [(target_x, 0)])
    ctx = _make_move_ctx(fleet, {"DE000001": _make_design("DE000001")})
    moved, events = move_fleet(ctx, fleet)
    assert events == []
    assert moved.position.x == target_x
    assert moved.position.y == 0
    assert len(moved.waypoints) == 0  # Waypoint consumed
    assert moved.bearing == 90.0


def test_stationary_fleet_keeps_bearing():
    fleet = _make_fleet(100, 200, [])
    fleet = fleet.model_copy(update={"bearing": 135.0})
    ctx = _make_move_ctx(fleet, {"DE000001": _make_design("DE000001")})
    moved, events = move_fleet(ctx, fleet)
    assert events == []
    assert moved.position.x == 100
    assert moved.position.y == 200
    assert moved.bearing == 135.0


def test_multi_waypoint_in_one_turn():
    """Fleet can pass through multiple waypoints in one turn."""
    # Two waypoints each 2 light-years away, speed 6 → should reach both
    wp1_x = 2 * LIGHT_YEAR
    wp2_x = 4 * LIGHT_YEAR
    fleet = _make_fleet(0, 0, [(wp1_x, 0), (wp2_x, 0)])
    ctx = _make_move_ctx(fleet, {"DE000001": _make_design("DE000001")})
    moved, events = move_fleet(ctx, fleet)
    assert events == []
    assert moved.position.x == wp2_x
    assert len(moved.waypoints) == 0


def test_fleet_moves_at_requested_warp_when_fuel_suffices():
    """Multi-design fleet follows explicit waypoint warp when fuel is sufficient."""
    fleet = Fleet(
        id="FL000001",
        name="Fleet #1",
        owner="tim",
        position=Position(x=0, y=0),
        composition=[
            FleetComposition(design_id="DE000001", count=1),
            FleetComposition(design_id="DE000002", count=1),
        ],
        waypoints=[Waypoint(x=100 * LIGHT_YEAR, y=0, warp=3)],
        fuel=200,
    )
    designs = {
        "DE000001": _make_design("DE000001", _TEST_ENGINE_FUEL_USAGE),
        "DE000002": _make_design("DE000002", _TEST_ENGINE_FUEL_USAGE),
    }
    ctx = _make_move_ctx(fleet, designs)
    moved, events = move_fleet(
        ctx,
        fleet,
    )
    assert events == []
    expected_x = 9 * LIGHT_YEAR
    assert moved.position.x == expected_x


def test_diagonal_movement():
    """Fleet moves diagonally toward waypoint."""
    # 45-degree angle, target at (100*P, 100*P)
    target = 100 * LIGHT_YEAR
    fleet = _make_fleet(0, 0, [(target, target)])
    ctx = _make_move_ctx(fleet, {"DE000001": _make_design("DE000001")})
    moved, events = move_fleet(ctx, fleet)
    # Should move at warp-6 budget (36 light-years) along the diagonal.
    # Just verify it moved and is closer to the target
    assert events == []
    assert moved.position.x > 0
    assert moved.position.y > 0
    assert moved.position.x == moved.position.y  # Should be equal for 45°


def test_zero_distance_waypoint_does_not_grant_free_high_warp_on_later_leg():
    fleet = Fleet(
        id="FL000001",
        name="Fleet #1",
        owner="tim",
        position=Position(x=0, y=0),
        composition=[FleetComposition(design_id="DE000001", count=1)],
        waypoints=[
            Waypoint(x=0, y=0, warp=10),
            Waypoint(x=100 * LIGHT_YEAR, y=0),
        ],
        fuel=0,
    )
    ctx = _make_move_ctx(fleet, {"DE000001": _make_design("DE000001")})

    moved, events = move_fleet(ctx, fleet)

    assert events == []
    assert moved is not None
    assert moved.position == Position(x=LIGHT_YEAR, y=0)
    assert len(moved.waypoints) == 1
    assert moved.waypoints[0] == Waypoint(x=100 * LIGHT_YEAR, y=0)


def test_colonise_waypoint_dissolves_fleet_after_arrival():
    planet = PlanetState(id="PL000001")
    fleet = Fleet(
        id="FL000001",
        name="Fleet #1",
        owner="tim",
        position=Position(x=0, y=0),
        composition=[FleetComposition(design_id="DE000001", count=1)],
        cargo=Cargo(colonists=2500),
        fuel=200,
        waypoints=[Waypoint(x=3 * LIGHT_YEAR, y=0, task=WaypointTask(type="colonise"))],
    )
    designs = {
        "DE000001": Design(
            id="DE000001",
            owner="tim",
            name="Colony Ship",
            hull="colony_ship",
            mass=_COLONY_SHIP_HULL_MASS + 2,
            fuel_usage=_TEST_ENGINE_FUEL_USAGE,
            fuel_capacity=100,
            scanner=Scanner(normal=0, penetrating=0),
            cargo_capacity=25,
            cost=_TEST_DESIGN_COST,
        )
    }
    ctx = _make_move_ctx(
        fleet,
        designs,
        planets=[planet],
        galaxy_planets=[GalaxyPlanet(id=planet.id, name="Proxima", x=3 * LIGHT_YEAR, y=0)],
    )

    moved, events = move_fleet(ctx, fleet)

    assert moved is None
    assert fleet.id not in ctx.fleets_by_id
    assert ctx.planets_by_id[planet.id].owner == "tim"
    assert events[0].code == "colonisation.colonised"
    assert events[0].values[1] == "Proxima"


def test_colonise_waypoint_leaves_surviving_escort_fleet():
    planet = PlanetState(id="PL000001")
    fleet = Fleet(
        id="FL000001",
        name="Fleet #1",
        owner="tim",
        position=Position(x=0, y=0),
        composition=[
            FleetComposition(design_id="DE000001", count=1),
            FleetComposition(design_id="DE000002", count=1),
        ],
        cargo=Cargo(colonists=2500),
        fuel=200,
        waypoints=[Waypoint(x=3 * LIGHT_YEAR, y=0, task=WaypointTask(type="colonise"))],
    )
    designs = {
        "DE000001": Design(
            id="DE000001",
            owner="tim",
            name="Colony Ship",
            hull="colony_ship",
            mass=_COLONY_SHIP_HULL_MASS + 2,
            fuel_usage=_TEST_ENGINE_FUEL_USAGE,
            fuel_capacity=100,
            scanner=Scanner(normal=0, penetrating=0),
            cargo_capacity=25,
            cost=_TEST_DESIGN_COST,
        ),
        "DE000002": Design(
            id="DE000002",
            owner="tim",
            name="Scout",
            hull="scout",
            mass=_SCOUT_HULL_MASS + 4,
            fuel_usage=_TEST_ENGINE_FUEL_USAGE,
            fuel_capacity=100,
            scanner=Scanner(normal=0, penetrating=0),
            cost=_TEST_DESIGN_COST,
        ),
    }
    ctx = _make_move_ctx(
        fleet,
        designs,
        planets=[planet],
        galaxy_planets=[GalaxyPlanet(id=planet.id, name="Proxima", x=3 * LIGHT_YEAR, y=0)],
    )

    moved, events = move_fleet(ctx, fleet)

    assert moved is not None
    assert moved.composition == [FleetComposition(design_id="DE000002", count=1)]
    assert moved.position == Position(x=3 * LIGHT_YEAR, y=0)
    assert events[0].code == "colonisation.colonised"


def test_colonise_runs_only_after_reaching_waypoint():
    planet = PlanetState(id="PL000001")
    fleet = Fleet(
        id="FL000001",
        name="Fleet #1",
        owner="tim",
        position=Position(x=0, y=0),
        composition=[FleetComposition(design_id="DE000001", count=1)],
        cargo=Cargo(colonists=2500),
        waypoints=[Waypoint(x=10 * LIGHT_YEAR, y=0, warp=3, task=WaypointTask(type="colonise"))],
        fuel=200,
    )
    designs = {
        "DE000001": Design(
            id="DE000001",
            owner="tim",
            name="Colony Ship",
            hull="colony_ship",
            mass=_COLONY_SHIP_HULL_MASS + 2,
            fuel_usage=_TEST_ENGINE_FUEL_USAGE,
            fuel_capacity=100,
            scanner=Scanner(normal=0, penetrating=0),
            cargo_capacity=25,
            cost=_TEST_DESIGN_COST,
        )
    }

    ctx = _make_move_ctx(
        fleet,
        designs,
        planets=[planet],
        galaxy_planets=[GalaxyPlanet(id=planet.id, name="Proxima", x=10 * LIGHT_YEAR, y=0)],
    )

    moved, events = move_fleet(ctx, fleet)

    assert moved is not None
    assert moved.position == Position(x=9 * LIGHT_YEAR, y=0)
    assert events == []
    assert planet.owner is None


def test_failed_colonise_consumes_waypoint_but_keeps_fleet():
    planet = PlanetState(id="PL000001")
    fleet = Fleet(
        id="FL000001",
        name="Fleet #1",
        owner="tim",
        position=Position(x=0, y=0),
        composition=[FleetComposition(design_id="DE000001", count=1)],
        cargo=Cargo(),
        fuel=200,
        waypoints=[Waypoint(x=3 * LIGHT_YEAR, y=0, task=WaypointTask(type="colonise"))],
    )
    designs = {
        "DE000001": Design(
            id="DE000001",
            owner="tim",
            name="Colony Ship",
            hull="colony_ship",
            mass=_COLONY_SHIP_HULL_MASS + 2,
            fuel_usage=_TEST_ENGINE_FUEL_USAGE,
            fuel_capacity=100,
            scanner=Scanner(normal=0, penetrating=0),
            cargo_capacity=25,
            cost=_TEST_DESIGN_COST,
        )
    }

    ctx = _make_move_ctx(
        fleet,
        designs,
        planets=[planet],
        galaxy_planets=[GalaxyPlanet(id=planet.id, name="Proxima", x=3 * LIGHT_YEAR, y=0)],
    )

    moved, events = move_fleet(ctx, fleet)

    assert moved is not None
    assert moved.position == Position(x=3 * LIGHT_YEAR, y=0)
    assert moved.waypoints == []
    assert moved.composition == fleet.composition
    assert events[0].code == "colonisation.failed"
    assert events[0].values[-1] == "no_colonists"


def test_resolve_colonisation_triggers_same_turn_population_loss():
    hostile_hab = Habitability(gravity=0, temperature=0, radiation=0)
    colony_designs = [
        Design(
            id="DE000001",
            owner="tim",
            name="Colony Ship",
            hull="colony_ship",
            mass=_COLONY_SHIP_HULL_MASS + 2,
            fuel_usage=_TEST_ENGINE_FUEL_USAGE,
            fuel_capacity=100,
            scanner=Scanner(normal=0, penetrating=0),
            cargo_capacity=25,
            cost=_TEST_DESIGN_COST,
        ),
        Design(
            id="DE000002",
            owner="sara",
            name="Scout",
            hull="scout",
            mass=_SCOUT_HULL_MASS + 4,
            fuel_usage=_TEST_ENGINE_FUEL_USAGE,
            fuel_capacity=100,
            scanner=Scanner(normal=0, penetrating=0),
            cost=_TEST_DESIGN_COST,
        ),
    ]
    state = GlobalState(
        game=GameMeta(seed=42, turn=0, next_id=100),
        players=[
            Player(username="tim", name="Tim", race=_JOAT_RACE),
            Player(username="sara", name="Sara", race=default_race()),
        ],
        planets=[
            PlanetState(id="PLHOME", owner="tim", population=25000, habitability=_GOOD_HAB),
            PlanetState(id="PLHOSTILE", owner=None, population=0, habitability=hostile_hab),
        ],
        fleets=[
            Fleet(
                id="FL000001",
                name="Fleet #1",
                owner="tim",
                position=Position(x=0, y=0),
                composition=[FleetComposition(design_id="DE000001", count=1)],
                cargo=Cargo(colonists=2500),
                fuel=200,
                waypoints=[Waypoint(x=3 * LIGHT_YEAR, y=0, task=WaypointTask(type="colonise"))],
            ),
            Fleet(
                id="FL000002",
                name="Fleet #1",
                owner="sara",
                position=Position(x=20 * LIGHT_YEAR, y=0),
                composition=[FleetComposition(design_id="DE000002", count=1)],
                waypoints=[],
            ),
        ],
    )
    galaxy = Galaxy(
        galaxy=GalaxyMetadata(name="Test", size="small", seed=42),
        planets=[
            GalaxyPlanet(id="PLHOME", name="Sol", x=0, y=0),
            GalaxyPlanet(id="PLHOSTILE", name="Inferno", x=3 * LIGHT_YEAR, y=0),
        ],
    )

    new_state = _rt(state, galaxy, designs=colony_designs)

    hostile = next(planet for planet in new_state.planets if planet.id == "PLHOSTILE")
    assert hostile.owner == "tim"
    assert 0 < hostile.population < 2500
    assert any(event.code == "colonisation.colonised" for event in new_state.events["tim"])
    assert any(event.code == "population.colonists_died" for event in new_state.events["tim"])
    assert "sara" not in new_state.events


# --- Full resolution tests ---


def _make_state(
    fleets: list[Fleet] | None = None,
    turn: int = 0,
) -> GlobalState:
    return GlobalState(
        game=GameMeta(seed=42, turn=turn, next_id=100),
        players=[
            Player(username="tim", name="Tim", race=_JOAT_RACE),
            Player(username="sara", name="Sara", race=default_race()),
        ],
        planets=[
            PlanetState(id="PL000001", owner="tim", population=25000, habitability=_GOOD_HAB),
            PlanetState(id="PL000002", owner="sara", population=25000, habitability=_GOOD_HAB),
        ],
        fleets=fleets
        or [
            _make_fleet(0, 0, [], fleet_id="FL000001"),
            Fleet(
                id="FL000002",
                name="Fleet #1",
                owner="sara",
                position=Position(x=100 * LIGHT_YEAR, y=100 * LIGHT_YEAR),
                composition=[FleetComposition(design_id="DE000002", count=1)],
                waypoints=[],
            ),
        ],
    )


def _make_galaxy():
    return generate_galaxy("Test", "small", seed=42, num_planets=20)


def test_resolve_increments_turn():
    state = _make_state()
    galaxy = _make_galaxy()
    new_state = _rt(state, galaxy)
    assert new_state.game.turn == 1


def test_resolve_applies_waypoints():
    state = _make_state()
    galaxy = _make_galaxy()
    commands = {
        "tim": PlayerCommands(
            commands=[
                SetWaypointsCommand(
                    fleet_id="FL000001",
                    waypoints=[Waypoint(x=50 * LIGHT_YEAR, y=0, warp=3)],
                )
            ]
        )
    }
    new_state = _rt(state, galaxy, commands)
    tim_fleet = next(f for f in new_state.fleets if f.owner == "tim")
    # Fleet should have moved at warp-3 (9 light-years) toward the waypoint.
    assert tim_fleet.position.x == 9 * LIGHT_YEAR


def test_resolve_ignores_wrong_owner():
    """Sara can't command Tim's fleet."""
    state = _make_state()
    galaxy = _make_galaxy()
    commands = {
        "sara": PlayerCommands(
            commands=[
                SetWaypointsCommand(
                    fleet_id="FL000001",  # Tim's fleet
                    waypoints=[Waypoint(x=50 * LIGHT_YEAR, y=0)],
                )
            ]
        )
    }
    new_state = _rt(state, galaxy, commands)
    tim_fleet = next(f for f in new_state.fleets if f.id == "FL000001")
    # Fleet should NOT have moved
    assert tim_fleet.position.x == 0


def test_resolve_preserves_planet_identity():
    """Planet IDs and owners are preserved across a turn."""
    state = _make_state()
    galaxy = _make_galaxy()
    new_state = _rt(state, galaxy)
    assert {p.id for p in new_state.planets} == {p.id for p in state.planets}
    for old, new in zip(
        sorted(state.planets, key=lambda p: p.id),
        sorted(new_state.planets, key=lambda p: p.id),
    ):
        assert new.owner == old.owner


def test_resolve_determinism():
    state = _make_state()
    galaxy = _make_galaxy()
    commands = {
        "tim": PlayerCommands(
            commands=[
                SetWaypointsCommand(
                    fleet_id="FL000001",
                    waypoints=[Waypoint(x=50 * LIGHT_YEAR, y=0)],
                )
            ]
        )
    }
    result1 = _rt(state, galaxy, commands)
    result2 = _rt(state, galaxy, commands)
    assert result1 == result2


def test_resolve_adds_production_item_with_server_generated_id():
    state = _make_state()
    galaxy = _make_galaxy()

    new_state = _rt(
        state,
        galaxy,
        {
            "tim": PlayerCommands(
                commands=[
                    AddProductionItemCommand(
                        planet_id="PL000001",
                        item_type="factory",
                        quantity=2,
                    )
                ]
            )
        },
    )

    planet = next(p for p in new_state.planets if p.id == "PL000001")
    assert len(planet.production_queue) == 1
    assert planet.production_queue[0].id.startswith("PQ")
    assert planet.production_queue[0].quantity == 2
    assert new_state.game.next_id == state.game.next_id + 1


def test_resolve_adds_starbase_production_item_with_target_type():
    state = _make_state()
    galaxy = _make_galaxy()

    new_state = _rt(
        state,
        galaxy,
        {
            "tim": PlayerCommands(
                commands=[
                    AddProductionItemCommand(
                        planet_id="PL000001",
                        item_type="starbase",
                        target_type="orbital_fort",
                        quantity=1,
                    )
                ]
            )
        },
    )

    planet = next(p for p in new_state.planets if p.id == "PL000001")
    assert len(planet.production_queue) == 1
    assert planet.production_queue[0].item_type == "starbase"
    assert planet.production_queue[0].target_type == "orbital_fort"


def test_resolve_rejects_duplicate_unfinished_starbase_queue_items():
    state = _make_state()
    state.planets[0].production_queue = [
        ProductionQueueItem(
            id="PQ000001",
            item_type="starbase",
            target_type="orbital_fort",
            quantity=1,
        )
    ]
    galaxy = _make_galaxy()

    new_state = _rt(
        state,
        galaxy,
        {
            "tim": PlayerCommands(
                commands=[
                    AddProductionItemCommand(
                        planet_id="PL000001",
                        item_type="starbase",
                        target_type="space_station",
                        quantity=1,
                    )
                ]
            )
        },
    )

    queue = next(p for p in new_state.planets if p.id == "PL000001").production_queue
    assert len(queue) == 1
    assert queue[0].target_type == "orbital_fort"


def test_resolve_moves_production_item_preserving_progress():
    state = _make_state()
    state.planets[0].production_queue = [
        ProductionQueueItem(id="PQ000001", item_type="mine", quantity=1),
        ProductionQueueItem(
            id="PQ000002",
            item_type="factory",
            quantity=3,
            progress=ProductionProgress(resources_spent=6),
        ),
    ]
    galaxy = _make_galaxy()

    new_state = _rt(
        state,
        galaxy,
        {
            "tim": PlayerCommands(
                commands=[
                    MoveProductionItemCommand(
                        planet_id="PL000001",
                        item_id="PQ000002",
                        insert_after_item_id=None,
                    )
                ]
            )
        },
    )

    queue = next(p for p in new_state.planets if p.id == "PL000001").production_queue
    assert [item.id for item in queue] == ["PQ000002", "PQ000001"]
    assert queue[0].progress.resources_spent == 6


def test_resolve_partial_remove_preserves_progress():
    state = _make_state()
    state.planets[0].production_queue = [
        ProductionQueueItem(
            id="PQ000001",
            item_type="factory",
            quantity=4,
            progress=ProductionProgress(resources_spent=6),
        )
    ]
    galaxy = _make_galaxy()

    new_state = _rt(
        state,
        galaxy,
        {
            "tim": PlayerCommands(
                commands=[
                    RemoveProductionItemCommand(
                        planet_id="PL000001",
                        item_id="PQ000001",
                        quantity=1,
                    )
                ]
            )
        },
    )

    queue_item = next(p for p in new_state.planets if p.id == "PL000001").production_queue[0]
    assert queue_item.quantity == 3
    assert queue_item.progress.resources_spent == 6


def test_resolve_full_remove_drops_partial_progress():
    state = _make_state()
    state.planets[0].production_queue = [
        ProductionQueueItem(
            id="PQ000001",
            item_type="factory",
            quantity=1,
            progress=ProductionProgress(resources_spent=6),
        )
    ]
    galaxy = _make_galaxy()

    new_state = _rt(
        state,
        galaxy,
        {
            "tim": PlayerCommands(
                commands=[
                    RemoveProductionItemCommand(
                        planet_id="PL000001",
                        item_id="PQ000001",
                        quantity=1,
                    )
                ]
            )
        },
    )

    queue = next(p for p in new_state.planets if p.id == "PL000001").production_queue
    assert queue == []


def test_resolve_clears_production_queue():
    state = _make_state()
    state.planets[0].production_queue = [
        ProductionQueueItem(id="PQ000001", item_type="mine", quantity=1),
        ProductionQueueItem(id="PQ000002", item_type="factory", quantity=2),
    ]
    galaxy = _make_galaxy()

    new_state = _rt(
        state,
        galaxy,
        {"tim": PlayerCommands(commands=[ClearProductionQueueCommand(planet_id="PL000001")])},
    )

    queue = next(p for p in new_state.planets if p.id == "PL000001").production_queue
    assert queue == []


def test_resolve_ignores_invalid_cross_owner_and_cross_planet_queue_references():
    state = _make_state()
    state.planets[0].population = 0
    state.planets[1].population = 0
    state.planets[0].production_queue = [
        ProductionQueueItem(id="PQ000001", item_type="mine", quantity=1)
    ]
    state.planets[1].production_queue = [
        ProductionQueueItem(id="PQ000002", item_type="factory", quantity=2)
    ]
    galaxy = _make_galaxy()

    new_state = _rt(
        state,
        galaxy,
        {
            "tim": PlayerCommands(
                commands=[
                    MoveProductionItemCommand(
                        planet_id="PL000001",
                        item_id="PQ000001",
                        insert_after_item_id="PQ000002",
                    ),
                    RemoveProductionItemCommand(
                        planet_id="PL000002",
                        item_id="PQ000002",
                        quantity=1,
                    ),
                ]
            )
        },
    )

    tim_queue = next(p for p in new_state.planets if p.id == "PL000001").production_queue
    sara_queue = next(p for p in new_state.planets if p.id == "PL000002").production_queue
    assert [item.id for item in tim_queue] == ["PQ000001"]
    assert sara_queue[0].quantity == 2


def test_resolve_completes_mine_in_single_turn():
    state = _make_state()
    state.planets[0].production_queue = [
        ProductionQueueItem(id="PQ000001", item_type="mine", quantity=1)
    ]
    galaxy = _make_galaxy()

    new_state = _rt(state, galaxy)

    planet = next(p for p in new_state.planets if p.id == "PL000001")
    assert planet.mines == 1
    assert planet.production_queue == []
    assert new_state.events["tim"][0].code == "production.completed"
    assert new_state.events["tim"][0].values[0:2] == [1, "mine"]


def test_resolve_persists_factory_progress_across_turns():
    state = _make_state()
    state.planets[0].population = 6_000
    state.planets[0].minerals.germanium = 10
    state.planets[0].production_queue = [
        ProductionQueueItem(id="PQ000001", item_type="factory", quantity=1)
    ]
    galaxy = _make_galaxy()

    turn_one_state = _rt(state, galaxy)
    planet_after_turn_one = next(p for p in turn_one_state.planets if p.id == "PL000001")
    assert planet_after_turn_one.factories == 0
    assert planet_after_turn_one.production_queue[0].progress.resources_spent == 6
    assert planet_after_turn_one.production_queue[0].progress.minerals_spent.germanium == 2

    turn_two_state = _rt(turn_one_state, galaxy)
    planet_after_turn_two = next(p for p in turn_two_state.planets if p.id == "PL000001")
    assert planet_after_turn_two.factories == 1
    assert planet_after_turn_two.production_queue == []


def test_resolve_blocks_rest_of_queue_when_current_item_cannot_progress():
    state = _make_state()
    state.planets[0].minerals.germanium = 0
    state.planets[0].production_queue = [
        ProductionQueueItem(id="PQ000001", item_type="factory", quantity=1),
        ProductionQueueItem(id="PQ000002", item_type="mine", quantity=1),
    ]
    galaxy = _make_galaxy()

    new_state = _rt(state, galaxy)

    planet = next(p for p in new_state.planets if p.id == "PL000001")
    assert planet.factories == 0
    assert planet.mines == 0
    assert [item.id for item in planet.production_queue] == ["PQ000001", "PQ000002"]
    assert new_state.events == {}


def test_resolve_aggregates_multiple_completed_units_from_one_queue_entry():
    state = _make_state()
    state.planets[0].population = 25_000
    state.planets[0].production_queue = [
        ProductionQueueItem(id="PQ000001", item_type="mine", quantity=3)
    ]
    galaxy = _make_galaxy()

    new_state = _rt(state, galaxy)

    planet = next(p for p in new_state.planets if p.id == "PL000001")
    assert planet.mines == 3
    assert planet.production_queue == []
    assert len(new_state.events["tim"]) == 1
    assert new_state.events["tim"][0].values[0] == 3


def test_resolve_processes_production_in_lexicographic_planet_order():
    state = _make_state()
    state.planets = [
        PlanetState(id="PL000010", owner="tim", population=25_000, habitability=_GOOD_HAB),
        PlanetState(id="PL000002", owner="tim", population=25_000, habitability=_GOOD_HAB),
    ]
    for planet in state.planets:
        planet.production_queue = [
            ProductionQueueItem(id=f"PQ{planet.id}", item_type="mine", quantity=1)
        ]
    galaxy = _make_galaxy()

    new_state = _rt(state, galaxy)

    production_events = new_state.events["tim"]
    assert [event.source_id for event in production_events] == ["PL000002", "PL000010"]


def test_full_turn_cycle():
    """Full cycle: create state → set waypoints → resolve → verify movement."""
    galaxy = generate_galaxy("Test", "small", seed=42, num_planets=20)
    from openstars.engine.create_game import create_initial_state

    state, _designs = create_initial_state(galaxy, ["tim", "sara"], game_seed=12345)
    storage = MemoryStorage()
    state = submit_default_race_and_resolve_turn_0(
        state, galaxy, storage, ["tim", "sara"], game_id="game1"
    )
    designs = storage.list_designs("game1", "sara") + storage.list_designs("game1", "tim")

    # Find Tim's fleet and pick a destination
    tim_fleet = next(f for f in state.fleets if f.owner == "tim")
    dest = Waypoint(x=tim_fleet.position.x + 50 * LIGHT_YEAR, y=tim_fleet.position.y, warp=1)

    commands = {
        "tim": PlayerCommands(
            commands=[
                SetWaypointsCommand(
                    fleet_id=tim_fleet.id,
                    waypoints=[dest],
                )
            ]
        ),
        "sara": PlayerCommands(commands=[]),
    }

    new_state = resolve_turn(state, galaxy, commands, designs, game_id="game1", storage=storage)
    assert new_state.game.turn == 2

    new_tim_fleet = next(f for f in new_state.fleets if f.id == tim_fleet.id)
    # Should have moved at warp-1 budget (1 light-year) toward destination.
    assert new_tim_fleet.position.x == tim_fleet.position.x + LIGHT_YEAR


# --- rename_fleet command tests ---


def _rename_fleet_ctx() -> TurnContext:
    """Return a minimal TurnContext with a single fleet for rename tests."""
    fleet = Fleet(
        id="FL000001",
        name="Fleet #1",
        owner="tim",
        position=Position(x=0, y=0),
        composition=[FleetComposition(design_id="DE000001", count=1)],
    )
    global_state = GlobalState(
        game=GameMeta(seed=42, turn=0, next_id=100),
        players=[],
        planets=[],
        fleets=[fleet],
    )
    galaxy = Galaxy(
        galaxy=GalaxyMetadata(name="test", size="small", seed=0),
        planets=[],
    )
    return TurnContext("game1", global_state, galaxy, [], _CATALOGUE)


def test_rename_fleet_updates_name():
    ctx = _rename_fleet_ctx()
    apply_commands(
        ctx,
        all_commands={
            "tim": PlayerCommands(
                commands=[RenameFleetCommand(fleet_id="FL000001", name="Vanguard")]
            )
        },
    )
    assert ctx.fleets_by_id["FL000001"].name == "Vanguard"


def test_rename_fleet_ignores_unowned_fleet():
    ctx = _rename_fleet_ctx()
    apply_commands(
        ctx,
        all_commands={
            "sara": PlayerCommands(
                commands=[RenameFleetCommand(fleet_id="FL000001", name="Vanguard")]
            )
        },
    )
    assert ctx.fleets_by_id["FL000001"].name == "Fleet #1"


def test_rename_fleet_ignores_unknown_fleet():
    ctx = _rename_fleet_ctx()
    apply_commands(
        ctx,
        all_commands={
            "tim": PlayerCommands(
                commands=[RenameFleetCommand(fleet_id="FL999999", name="Vanguard")]
            )
        },
    )
    assert ctx.fleets_by_id["FL000001"].name == "Fleet #1"
