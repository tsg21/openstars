"""Tests for engine models."""

import pytest
from pydantic import ValidationError

from openstars.engine.colonisation import (
    COLONY_SHIP_RECOVERED_MINERALS,
    recovered_minerals_for_colony_ships,
)
from openstars.engine.models import (
    AddProductionItemCommand,
    ClearProductionQueueCommand,
    Design,
    Fleet,
    FleetComposition,
    Galaxy,
    GalaxyMetadata,
    GalaxyPlanet,
    GameEvent,
    GameMeta,
    GlobalState,
    MoveProductionItemCommand,
    PlanetState,
    Player,
    PlayerCommands,
    PlayerPlanet,
    PlayerProductionQueueItem,
    PlayerState,
    Position,
    ProductionProgress,
    ProductionQueueItem,
    RemoveProductionItemCommand,
    Scanner,
    SetWaypointsCommand,
    Waypoint,
    WaypointTask,
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
                scanner=Scanner(normal=150, penetrating=0),
            )
        ],
        planets=[PlanetState(id="PLabc123", owner="tim", population=25000)],
        fleets=[
            Fleet(
                id="FLabc123",
                name="Fleet #1",
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
    assert p.production_queue == []


def test_production_queue_item_defaults_and_serialization():
    item = ProductionQueueItem(id="PQabc123", item_type="factory", quantity=3)
    dumped = item.model_dump()

    assert item.progress.resources_spent == 0
    assert item.progress.minerals_spent.germanium == 0
    assert dumped["item_type"] == "factory"
    assert dumped["progress"]["minerals_spent"]["ironium"] == 0


def test_player_planet_production_queue_round_trips():
    planet = PlayerPlanet(
        id="PLabc123",
        name="Earth",
        x=1,
        y=2,
        production_queue=[
            PlayerProductionQueueItem(
                id="PQabc123",
                item_type="mine",
                quantity=2,
                progress=ProductionProgress(resources_spent=4),
            )
        ],
    )

    assert planet.production_queue is not None
    assert planet.production_queue[0].progress.resources_spent == 4


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


def test_game_event_allows_new_codes_without_schema_changes():
    event = GameEvent(
        owner="tim",
        source_id="PLabc123",
        code="future.custom_code",
        values=["alpha", 12],
    )
    assert event.code == "future.custom_code"
    assert event.values == ["alpha", 12]


def test_set_waypoints_command():
    cmd = SetWaypointsCommand(
        fleet_id="FLabc123",
        waypoints=[Waypoint(x=100, y=200)],
    )
    assert cmd.type == "set_waypoints"


def test_set_waypoints_command_accepts_colonise_task():
    cmd = SetWaypointsCommand(
        fleet_id="FLabc123",
        waypoints=[Waypoint(x=100, y=200, task=WaypointTask(type="colonise"))],
    )
    assert cmd.waypoints[0].task is not None
    assert cmd.waypoints[0].task.type == "colonise"


def test_colony_ship_dismantle_recovery_values():
    assert COLONY_SHIP_RECOVERED_MINERALS.ironium == 1
    assert COLONY_SHIP_RECOVERED_MINERALS.boranium == 1
    assert COLONY_SHIP_RECOVERED_MINERALS.germanium == 5

    doubled = recovered_minerals_for_colony_ships(2)
    assert doubled.ironium == 2
    assert doubled.boranium == 2
    assert doubled.germanium == 10


def test_player_commands():
    pc = PlayerCommands(
        commands=[
            SetWaypointsCommand(
                fleet_id="FLabc123",
                waypoints=[Waypoint(x=100, y=200)],
            )
        ]
    )
    assert len(pc.commands) == 1


def test_player_commands_supports_production_commands():
    pc = PlayerCommands.model_validate(
        {
            "commands": [
                {
                    "type": "add_production_item",
                    "planet_id": "PLabc123",
                    "item_type": "factory",
                    "quantity": 5,
                    "insert_after_item_id": None,
                },
                {
                    "type": "move_production_item",
                    "planet_id": "PLabc123",
                    "item_id": "PQabc123",
                    "insert_after_item_id": None,
                },
                {
                    "type": "remove_production_item",
                    "planet_id": "PLabc123",
                    "item_id": "PQabc123",
                    "quantity": 1,
                },
                {
                    "type": "clear_production_queue",
                    "planet_id": "PLabc123",
                },
            ]
        }
    )

    assert isinstance(pc.commands[0], AddProductionItemCommand)
    assert isinstance(pc.commands[1], MoveProductionItemCommand)
    assert isinstance(pc.commands[2], RemoveProductionItemCommand)
    assert isinstance(pc.commands[3], ClearProductionQueueCommand)


@pytest.mark.parametrize(
    "payload",
    [
        {
            "type": "add_production_item",
            "planet_id": "PLabc123",
            "item_type": "lab",
            "quantity": 1,
        },
        {
            "type": "add_production_item",
            "planet_id": "PLabc123",
            "item_type": "mine",
            "quantity": 0,
        },
        {
            "type": "remove_production_item",
            "planet_id": "PLabc123",
            "item_id": "PQabc123",
            "quantity": 0,
        },
    ],
)
def test_player_commands_rejects_invalid_production_payloads(payload):
    with pytest.raises(ValidationError):
        PlayerCommands.model_validate({"commands": [payload]})


def test_player_commands_rejects_invalid():
    with pytest.raises(ValidationError):
        PlayerCommands(commands="not a list")  # type: ignore[arg-type]
