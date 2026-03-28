"""Tests for engine models."""

import pytest
from pydantic import ValidationError

from openstars.engine.models import (
    Design,
    Fleet,
    FleetComposition,
    Galaxy,
    GalaxyMetadata,
    GalaxyPlanet,
    GameMeta,
    GlobalState,
    PlanetState,
    Player,
    PlayerCommands,
    PlayerState,
    Position,
    SetWaypointsCommand,
)


def test_position():
    p = Position(x=100, y=200)
    assert p.x == 100
    assert p.y == 200


def test_position_rejects_missing_fields():
    with pytest.raises(ValidationError):
        Position(x=100)  # type: ignore[call-arg]


def test_galaxy():
    g = Galaxy(
        galaxy=GalaxyMetadata(name="Test", size="small", seed=42),
        planets=[GalaxyPlanet(id="PLabc123", name="Sol", x=1000, y=2000)],
    )
    assert g.galaxy.name == "Test"
    assert len(g.planets) == 1


def test_global_state():
    state = GlobalState(
        game=GameMeta(seed=42, turn=0, next_id=10),
        players=[Player(username="tim", name="Tim's Empire")],
        designs=[
            Design(
                id="DEabc123",
                owner="tim",
                name="Scout",
                hull="scout",
                speed=6,
                scanner_range=150,
            )
        ],
        planets=[PlanetState(id="PLabc123", owner="tim", population=25000)],
        fleets=[
            Fleet(
                id="FLabc123",
                owner="tim",
                position=Position(x=100, y=200),
                composition=[FleetComposition(design_id="DEabc123", count=1)],
                waypoints=[],
            )
        ],
    )
    assert state.game.turn == 0
    assert state.players[0].username == "tim"
    assert state.fleets[0].waypoints == []


def test_planet_state_defaults():
    p = PlanetState(id="PLabc123")
    assert p.owner is None
    assert p.population == 0


def test_player_state():
    ps = PlayerState(
        player="tim",
        turn=0,
        planets=[],
        fleets=[],
        designs=[],
        events=[],
    )
    assert ps.player == "tim"


def test_set_waypoints_command():
    cmd = SetWaypointsCommand(
        fleet_id="FLabc123",
        waypoints=[Position(x=100, y=200)],
    )
    assert cmd.type == "set_waypoints"


def test_player_commands():
    pc = PlayerCommands(
        commands=[
            SetWaypointsCommand(
                fleet_id="FLabc123",
                waypoints=[Position(x=100, y=200)],
            )
        ]
    )
    assert len(pc.commands) == 1


def test_player_commands_rejects_invalid():
    with pytest.raises(ValidationError):
        PlayerCommands(commands="not a list")  # type: ignore[arg-type]
