"""Tests for turn resolution and fleet movement."""

from openstars.engine.galaxy import generate_galaxy
from openstars.engine.models import (
    AddProductionItemCommand,
    ClearProductionQueueCommand,
    Design,
    Fleet,
    FleetComposition,
    GameMeta,
    GlobalState,
    Habitability,
    MoveProductionItemCommand,
    PlanetState,
    Player,
    PlayerCommands,
    Position,
    ProductionProgress,
    ProductionQueueItem,
    RemoveProductionItemCommand,
    Scanner,
    SetWaypointsCommand,
    Waypoint,
)
from openstars.engine.resolve import resolve_turn
from openstars.engine.resolve_steps.movement import PARSEC, isqrt, move_fleet

_GOOD_HAB = Habitability(gravity=50, temperature=50, radiation=50)

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


def _make_fleet(
    x: int, y: int, waypoints: list[tuple[int, int]], fleet_id: str = "FL000001"
) -> Fleet:
    return Fleet(
        id=fleet_id,
        owner="tim",
        position=Position(x=x, y=y),
        composition=[FleetComposition(design_id="DE000001", count=1)],
        waypoints=[Waypoint(x=wx, y=wy) for wx, wy in waypoints],
    )


def test_stationary_fleet():
    """Fleet with no waypoints doesn't move."""
    fleet = _make_fleet(100, 200, [])
    moved, _ = move_fleet(fleet, {"DE000001": 6}, {}, {}, {}, {})
    assert moved.position.x == 100
    assert moved.position.y == 200


def test_fleet_moves_toward_waypoint():
    """Fleet moves toward its waypoint."""
    # Place fleet at origin, waypoint far away along x-axis
    start_x = 549755813888
    target_x = start_x + 100 * PARSEC  # 100 parsecs away
    fleet = _make_fleet(start_x, 0, [(target_x, 0)])
    moved, _ = move_fleet(fleet, {"DE000001": 6}, {}, {}, {}, {})
    # Should move 6 parsecs toward target
    expected_x = start_x + 6 * PARSEC
    assert moved.position.x == expected_x
    assert moved.position.y == 0
    assert len(moved.waypoints) == 1  # Not yet arrived


def test_fleet_arrives_at_waypoint():
    """Fleet arrives when close enough."""
    start_x = 0
    target_x = 3 * PARSEC  # 3 parsecs away, speed is 6
    fleet = _make_fleet(start_x, 0, [(target_x, 0)])
    moved, _ = move_fleet(fleet, {"DE000001": 6}, {}, {}, {}, {})
    assert moved.position.x == target_x
    assert moved.position.y == 0
    assert len(moved.waypoints) == 0  # Waypoint consumed


def test_multi_waypoint_in_one_turn():
    """Fleet can pass through multiple waypoints in one turn."""
    # Two waypoints each 2 parsecs away, speed 6 → should reach both
    wp1_x = 2 * PARSEC
    wp2_x = 4 * PARSEC
    fleet = _make_fleet(0, 0, [(wp1_x, 0), (wp2_x, 0)])
    moved, _ = move_fleet(fleet, {"DE000001": 6}, {}, {}, {}, {})
    assert moved.position.x == wp2_x
    assert len(moved.waypoints) == 0


def test_fleet_speed_is_slowest_design():
    """Multi-design fleet moves at slowest speed."""
    fleet = Fleet(
        id="FL000001",
        owner="tim",
        position=Position(x=0, y=0),
        composition=[
            FleetComposition(design_id="DE000001", count=1),
            FleetComposition(design_id="DE000002", count=1),
        ],
        waypoints=[Waypoint(x=100 * PARSEC, y=0)],
    )
    moved, _ = move_fleet(fleet, {"DE000001": 6, "DE000002": 3}, {}, {}, {}, {})
    # Speed should be 3 (slowest)
    expected_x = 3 * PARSEC
    assert moved.position.x == expected_x


def test_diagonal_movement():
    """Fleet moves diagonally toward waypoint."""
    # 45-degree angle, target at (100*P, 100*P)
    target = 100 * PARSEC
    fleet = _make_fleet(0, 0, [(target, target)])
    moved, _ = move_fleet(fleet, {"DE000001": 6}, {}, {}, {}, {})
    # Should move 6 parsecs along the diagonal
    # Distance to target = sqrt(2) * 100 * PARSEC ≈ 141 parsecs
    # Movement = 6 parsecs → fleet should be at roughly (6/sqrt(2), 6/sqrt(2)) parsecs
    # Just verify it moved and is closer to the target
    assert moved.position.x > 0
    assert moved.position.y > 0
    assert moved.position.x == moved.position.y  # Should be equal for 45°


# --- Full resolution tests ---


def _make_state(
    fleets: list[Fleet] | None = None,
    turn: int = 0,
) -> GlobalState:
    return GlobalState(
        game=GameMeta(seed=42, turn=turn, next_id=100),
        players=[Player(username="tim", name="Tim"), Player(username="sara", name="Sara")],
        designs=[
            Design(
                id="DE000001",
                owner="tim",
                name="Scout",
                hull="scout",
                speed=6,
                scanner=Scanner(normal=150, penetrating=0),
            ),
            Design(
                id="DE000002",
                owner="sara",
                name="Scout",
                hull="scout",
                speed=6,
                scanner=Scanner(normal=150, penetrating=0),
            ),
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
                owner="sara",
                position=Position(x=100 * PARSEC, y=100 * PARSEC),
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
    new_state = resolve_turn(state, galaxy, {})
    assert new_state.game.turn == 1


def test_resolve_applies_waypoints():
    state = _make_state()
    galaxy = _make_galaxy()
    commands = {
        "tim": PlayerCommands(
            commands=[
                SetWaypointsCommand(
                    fleet_id="FL000001",
                    waypoints=[Waypoint(x=50 * PARSEC, y=0)],
                )
            ]
        )
    }
    new_state = resolve_turn(state, galaxy, commands)
    tim_fleet = next(f for f in new_state.fleets if f.owner == "tim")
    # Fleet should have moved toward the waypoint
    assert tim_fleet.position.x == 6 * PARSEC


def test_resolve_ignores_wrong_owner():
    """Sara can't command Tim's fleet."""
    state = _make_state()
    galaxy = _make_galaxy()
    commands = {
        "sara": PlayerCommands(
            commands=[
                SetWaypointsCommand(
                    fleet_id="FL000001",  # Tim's fleet
                    waypoints=[Waypoint(x=50 * PARSEC, y=0)],
                )
            ]
        )
    }
    new_state = resolve_turn(state, galaxy, commands)
    tim_fleet = next(f for f in new_state.fleets if f.id == "FL000001")
    # Fleet should NOT have moved
    assert tim_fleet.position.x == 0


def test_resolve_preserves_planet_identity():
    """Planet IDs and owners are preserved across a turn."""
    state = _make_state()
    galaxy = _make_galaxy()
    new_state = resolve_turn(state, galaxy, {})
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
                    waypoints=[Waypoint(x=50 * PARSEC, y=0)],
                )
            ]
        )
    }
    result1 = resolve_turn(state, galaxy, commands)
    result2 = resolve_turn(state, galaxy, commands)
    assert result1 == result2


def test_resolve_adds_production_item_with_server_generated_id():
    state = _make_state()
    galaxy = _make_galaxy()

    new_state = resolve_turn(
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

    new_state = resolve_turn(
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

    new_state = resolve_turn(
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

    new_state = resolve_turn(
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

    new_state = resolve_turn(
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

    new_state = resolve_turn(
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

    new_state = resolve_turn(state, galaxy, {})

    planet = next(p for p in new_state.planets if p.id == "PL000001")
    assert planet.mines == 1
    assert planet.production_queue == []
    assert new_state.events["tim"][0].type == "production_completed"
    assert new_state.events["tim"][0].item_type == "mine"
    assert new_state.events["tim"][0].quantity == 1


def test_resolve_persists_factory_progress_across_turns():
    state = _make_state()
    state.planets[0].population = 6_000
    state.planets[0].minerals.germanium = 10
    state.planets[0].production_queue = [
        ProductionQueueItem(id="PQ000001", item_type="factory", quantity=1)
    ]
    galaxy = _make_galaxy()

    turn_one_state = resolve_turn(state, galaxy, {})
    planet_after_turn_one = next(p for p in turn_one_state.planets if p.id == "PL000001")
    assert planet_after_turn_one.factories == 0
    assert planet_after_turn_one.production_queue[0].progress.resources_spent == 6
    assert planet_after_turn_one.production_queue[0].progress.minerals_spent.germanium == 2

    turn_two_state = resolve_turn(turn_one_state, galaxy, {})
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

    new_state = resolve_turn(state, galaxy, {})

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

    new_state = resolve_turn(state, galaxy, {})

    planet = next(p for p in new_state.planets if p.id == "PL000001")
    assert planet.mines == 3
    assert planet.production_queue == []
    assert len(new_state.events["tim"]) == 1
    assert new_state.events["tim"][0].quantity == 3


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

    new_state = resolve_turn(state, galaxy, {})

    production_events = new_state.events["tim"]
    assert [event.planet_id for event in production_events] == ["PL000002", "PL000010"]


def test_full_turn_cycle():
    """Full cycle: create state → set waypoints → resolve → verify movement."""
    galaxy = generate_galaxy("Test", "small", seed=42, num_planets=20)
    from openstars.engine.create_game import create_initial_state

    state = create_initial_state(galaxy, ["tim", "sara"], game_seed=12345)

    # Find Tim's fleet and pick a destination
    tim_fleet = next(f for f in state.fleets if f.owner == "tim")
    dest = Waypoint(x=tim_fleet.position.x + 50 * PARSEC, y=tim_fleet.position.y)

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

    new_state = resolve_turn(state, galaxy, commands)
    assert new_state.game.turn == 1

    new_tim_fleet = next(f for f in new_state.fleets if f.id == tim_fleet.id)
    # Should have moved 6 parsecs toward destination
    assert new_tim_fleet.position.x == tim_fleet.position.x + 6 * PARSEC
