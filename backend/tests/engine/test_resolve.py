"""Tests for turn resolution and fleet movement."""

from openstars.engine.galaxy import generate_galaxy
from openstars.engine.models import (
    Design,
    Fleet,
    FleetComposition,
    GameMeta,
    GlobalState,
    PlanetState,
    Player,
    PlayerCommands,
    Position,
    SetWaypointsCommand,
)
from openstars.engine.movement import PARSEC, isqrt, move_fleet
from openstars.engine.resolve import resolve_turn

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
        waypoints=[Position(x=wx, y=wy) for wx, wy in waypoints],
    )


def test_stationary_fleet():
    """Fleet with no waypoints doesn't move."""
    fleet = _make_fleet(100, 200, [])
    moved = move_fleet(fleet, {"DE000001": 6})
    assert moved.position.x == 100
    assert moved.position.y == 200


def test_fleet_moves_toward_waypoint():
    """Fleet moves toward its waypoint."""
    # Place fleet at origin, waypoint far away along x-axis
    start_x = 549755813888
    target_x = start_x + 100 * PARSEC  # 100 parsecs away
    fleet = _make_fleet(start_x, 0, [(target_x, 0)])
    moved = move_fleet(fleet, {"DE000001": 6})
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
    moved = move_fleet(fleet, {"DE000001": 6})
    assert moved.position.x == target_x
    assert moved.position.y == 0
    assert len(moved.waypoints) == 0  # Waypoint consumed


def test_multi_waypoint_in_one_turn():
    """Fleet can pass through multiple waypoints in one turn."""
    # Two waypoints each 2 parsecs away, speed 6 → should reach both
    wp1_x = 2 * PARSEC
    wp2_x = 4 * PARSEC
    fleet = _make_fleet(0, 0, [(wp1_x, 0), (wp2_x, 0)])
    moved = move_fleet(fleet, {"DE000001": 6})
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
        waypoints=[Position(x=100 * PARSEC, y=0)],
    )
    moved = move_fleet(fleet, {"DE000001": 6, "DE000002": 3})
    # Speed should be 3 (slowest)
    expected_x = 3 * PARSEC
    assert moved.position.x == expected_x


def test_diagonal_movement():
    """Fleet moves diagonally toward waypoint."""
    # 45-degree angle, target at (100*P, 100*P)
    target = 100 * PARSEC
    fleet = _make_fleet(0, 0, [(target, target)])
    moved = move_fleet(fleet, {"DE000001": 6})
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
                id="DE000001", owner="tim", name="Scout",
                hull="scout", speed=6, scanner_range=150,
            ),
            Design(
                id="DE000002", owner="sara", name="Scout",
                hull="scout", speed=6, scanner_range=150,
            ),
        ],
        planets=[
            PlanetState(id="PL000001", owner="tim", population=25000),
            PlanetState(id="PL000002", owner="sara", population=25000),
        ],
        fleets=fleets or [
            _make_fleet(0, 0, [], fleet_id="FL000001"),
            Fleet(
                id="FL000002", owner="sara",
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
        "tim": PlayerCommands(commands=[
            SetWaypointsCommand(
                fleet_id="FL000001",
                waypoints=[Position(x=50 * PARSEC, y=0)],
            )
        ])
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
        "sara": PlayerCommands(commands=[
            SetWaypointsCommand(
                fleet_id="FL000001",  # Tim's fleet
                waypoints=[Position(x=50 * PARSEC, y=0)],
            )
        ])
    }
    new_state = resolve_turn(state, galaxy, commands)
    tim_fleet = next(f for f in new_state.fleets if f.id == "FL000001")
    # Fleet should NOT have moved
    assert tim_fleet.position.x == 0


def test_resolve_preserves_planets():
    state = _make_state()
    galaxy = _make_galaxy()
    new_state = resolve_turn(state, galaxy, {})
    assert new_state.planets == state.planets


def test_resolve_determinism():
    state = _make_state()
    galaxy = _make_galaxy()
    commands = {
        "tim": PlayerCommands(commands=[
            SetWaypointsCommand(
                fleet_id="FL000001",
                waypoints=[Position(x=50 * PARSEC, y=0)],
            )
        ])
    }
    result1 = resolve_turn(state, galaxy, commands)
    result2 = resolve_turn(state, galaxy, commands)
    assert result1 == result2


def test_full_turn_cycle():
    """Full cycle: create state → set waypoints → resolve → verify movement."""
    galaxy = generate_galaxy("Test", "small", seed=42, num_planets=20)
    from openstars.engine.setup import create_initial_state
    state = create_initial_state(galaxy, ["tim", "sara"], game_seed=12345)

    # Find Tim's fleet and pick a destination
    tim_fleet = next(f for f in state.fleets if f.owner == "tim")
    dest = Position(x=tim_fleet.position.x + 50 * PARSEC, y=tim_fleet.position.y)

    commands = {
        "tim": PlayerCommands(commands=[
            SetWaypointsCommand(
                fleet_id=tim_fleet.id,
                waypoints=[dest],
            )
        ]),
        "sara": PlayerCommands(commands=[]),
    }

    new_state = resolve_turn(state, galaxy, commands)
    assert new_state.game.turn == 1

    new_tim_fleet = next(f for f in new_state.fleets if f.owner == "tim")
    # Should have moved 6 parsecs toward destination
    assert new_tim_fleet.position.x == tim_fleet.position.x + 6 * PARSEC
