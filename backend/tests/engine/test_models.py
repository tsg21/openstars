"""Tests for engine models."""

import pytest
from pydantic import ValidationError

from openstars.engine.colonisation import (
    COLONY_SHIP_RECOVERED_MINERALS,
    recovered_minerals_for_colony_ships,
)
from openstars.engine.models import (
    STATE_VERSION,
    AddProductionItemCommand,
    ClearProductionQueueCommand,
    Design,
    DesignCost,
    Fleet,
    FleetComposition,
    Galaxy,
    GalaxyMetadata,
    GalaxyPlanet,
    GameEvent,
    GameMeta,
    GlobalState,
    Minerals,
    MoveProductionItemCommand,
    PlanetStarbaseState,
    PlanetState,
    Player,
    PlayerCommands,
    PlayerPlanet,
    PlayerPlanetStarbaseSummary,
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
    assert state.state_version == STATE_VERSION
    assert state.players[0].username == "tim"
    assert state.fleets[0].waypoints == []


def test_global_state_serialises_root_state_version():
    state = GlobalState(
        game=GameMeta(seed=42, turn=0, next_id=10),
        players=[],
        planets=[],
        fleets=[],
    )

    dumped = state.model_dump()

    assert dumped["state_version"] == STATE_VERSION


def test_planet_state_defaults():
    p = PlanetState(id="PLabc123")
    assert p.owner is None
    assert p.population == 0
    assert p.production_queue == []
    assert p.starbase is None


def test_planet_state_supports_starbase_state():
    planet = PlanetState(
        id="PLabc123",
        starbase=PlanetStarbaseState(type="space_station", can_build_ships=True),
    )
    dumped = planet.model_dump()

    assert planet.starbase is not None
    assert planet.starbase.type == "space_station"
    assert dumped["starbase"]["can_build_ships"] is True


def test_production_queue_item_defaults_and_serialization():
    item = ProductionQueueItem(id="PQabc123", item_type="factory", quantity=3)
    dumped = item.model_dump()

    assert item.progress.resources_spent == 0
    assert item.progress.minerals_spent.germanium == 0
    assert dumped["item_type"] == "factory"
    assert dumped["progress"]["minerals_spent"]["ironium"] == 0


def test_ship_production_queue_item_requires_design_id():
    item = ProductionQueueItem(id="PQship1", item_type="ship", design_id="DEship1", quantity=2)
    dumped = item.model_dump()
    assert dumped["design_id"] == "DEship1"

    with pytest.raises(ValidationError):
        ProductionQueueItem(id="PQship2", item_type="ship", quantity=1)

    with pytest.raises(ValidationError):
        ProductionQueueItem(id="PQmine1", item_type="mine", quantity=1, design_id="DEship1")


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
        starbase=PlayerPlanetStarbaseSummary(present=True, type="orbital_fort"),
    )

    assert planet.production_queue is not None
    assert planet.production_queue[0].progress.resources_spent == 4
    assert planet.starbase is not None


def test_player_planet_ship_queue_item_round_trips_design_id():
    planet = PlayerPlanet(
        id="PLabc123",
        name="Earth",
        x=1,
        y=2,
        production_queue=[
            PlayerProductionQueueItem(
                id="PQship1",
                item_type="ship",
                design_id="DEship1",
                quantity=1,
                progress=ProductionProgress(resources_spent=4),
            )
        ],
    )
    assert planet.production_queue is not None
    assert planet.production_queue[0].design_id == "DEship1"


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
    assert ps.state_version == STATE_VERSION


def test_player_state_serialises_root_state_version():
    ps = PlayerState(
        player="tim",
        turn=0,
        planets=[],
        fleets=[],
        designs=[],
        events=[],
    )

    dumped = ps.model_dump()

    assert dumped["state_version"] == STATE_VERSION


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
                    "item_type": "ship",
                    "design_id": "DEship1",
                    "quantity": 2,
                },
                {
                    "type": "add_production_item",
                    "planet_id": "PLabc123",
                    "item_type": "starbase",
                    "target_type": "space_station",
                    "quantity": 1,
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
    assert isinstance(pc.commands[1], AddProductionItemCommand)
    assert isinstance(pc.commands[2], MoveProductionItemCommand)
    assert isinstance(pc.commands[3], RemoveProductionItemCommand)
    assert isinstance(pc.commands[4], ClearProductionQueueCommand)


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
            "item_type": "starbase",
            "quantity": 1,
        },
        {
            "type": "add_production_item",
            "planet_id": "PLabc123",
            "item_type": "mine",
            "design_id": "DEship1",
            "quantity": 1,
        },
        {
            "type": "add_production_item",
            "planet_id": "PLabc123",
            "item_type": "ship",
            "quantity": 1,
        },
        {
            "type": "add_production_item",
            "planet_id": "PLabc123",
            "item_type": "mine",
            "target_type": "space_station",
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


def test_design_round_trips_fuel_fields():
    design = Design(
        id="DE1",
        owner="tim",
        name="Scout",
        hull="scout",
        fuel_usage=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        fuel_capacity=50,
        scanner=Scanner(normal=100, penetrating=0),
        cost=DesignCost(resources=10, minerals=Minerals()),
    )
    loaded = Design.model_validate(design.model_dump())
    assert loaded.fuel_capacity == 50
    assert loaded.fuel_usage[5] == 5


def test_design_rejects_invalid_fuel_usage_length():
    with pytest.raises(ValidationError):
        Design(
            id="DE1",
            owner="tim",
            name="Scout",
            hull="scout",
            fuel_usage=[1, 2, 3],
            fuel_capacity=50,
            scanner=Scanner(normal=100, penetrating=0),
            cost=DesignCost(resources=10, minerals=Minerals()),
        )


def test_fleet_and_waypoint_round_trip_fuel_and_warp():
    fleet = Fleet(
        id="FL1",
        name="Fleet #1",
        owner="tim",
        position=Position(x=0, y=0),
        composition=[FleetComposition(design_id="DE1", count=1)],
        fuel=42,
        waypoints=[Waypoint(x=10, y=20, warp=4)],
    )
    dumped = fleet.model_dump()
    assert dumped["fuel"] == 42
    assert dumped["waypoints"][0]["warp"] == 4
