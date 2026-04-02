"""Unit tests for colonisation helpers and movement integration."""

from openstars.engine.galaxy import PARSEC
from openstars.engine.models import (
    Cargo,
    Design,
    Fleet,
    FleetComposition,
    Minerals,
    PlanetState,
    Position,
    Scanner,
    Waypoint,
    WaypointTask,
)
from openstars.engine.resolve_steps.colonisation import (
    count_colony_ships,
    fleet_has_colony_ship,
    recovered_minerals_for_colony_ships,
    resolve_colonize_task,
)
from openstars.engine.resolve_steps.movement import move_fleets


def _design(design_id: str, hull: str, owner: str = "tim", cargo_capacity: int = 25) -> Design:
    return Design(
        id=design_id,
        owner=owner,
        name=hull,
        hull=hull,
        speed=6,
        scanner=Scanner(normal=0, penetrating=0),
        cargo_capacity=cargo_capacity,
    )


def test_fleet_has_colony_ship_and_count_colony_ships():
    fleet = Fleet(
        id="FL1",
        owner="tim",
        position=Position(x=0, y=0),
        composition=[
            FleetComposition(design_id="DE_COL", count=2),
            FleetComposition(design_id="DE_SCOUT", count=1),
        ],
    )
    designs = {
        "DE_COL": _design("DE_COL", "colony_ship"),
        "DE_SCOUT": _design("DE_SCOUT", "scout", cargo_capacity=0),
    }
    assert fleet_has_colony_ship(fleet, designs)
    assert count_colony_ships(fleet, designs) == 2


def test_recovered_minerals_for_colony_ship_count():
    one = recovered_minerals_for_colony_ships(1)
    three = recovered_minerals_for_colony_ships(3)
    assert one == Minerals(ironium=1, boranium=1, germanium=5)
    assert three == Minerals(ironium=5, boranium=5, germanium=15)


def test_resolve_colonize_task_failure_reasons():
    fleet = Fleet(
        id="FL1",
        owner="tim",
        position=Position(x=0, y=0),
        composition=[FleetComposition(design_id="DE_COL", count=1)],
        cargo=Cargo(colonists=1000),
    )
    empty = PlanetState(id="PL1")
    owned = PlanetState(id="PL2", owner="sara")
    designs = {"DE_COL": _design("DE_COL", "colony_ship")}

    _, _, no_planet = resolve_colonize_task(fleet, None, designs)
    assert no_planet.type == "colonize_failed"
    assert no_planet.reason == "no_planet"

    _, _, already_owned = resolve_colonize_task(fleet, owned, designs)
    assert already_owned.reason == "planet_already_owned"

    no_colony_fleet = fleet.model_copy(
        update={"composition": [FleetComposition(design_id="DE_S", count=1)]}
    )
    _, _, no_colony_ship = resolve_colonize_task(
        no_colony_fleet, empty, {"DE_S": _design("DE_S", "scout", cargo_capacity=0)}
    )
    assert no_colony_ship.reason == "no_colony_ship"

    no_colonists = fleet.model_copy(update={"cargo": Cargo(colonists=0)})
    _, _, no_colonists_event = resolve_colonize_task(no_colonists, empty, designs)
    assert no_colonists_event.reason == "no_colonists"


def test_successful_colonisation_transfers_ownership_and_population():
    fleet = Fleet(
        id="FL1",
        owner="tim",
        position=Position(x=0, y=0),
        composition=[FleetComposition(design_id="DE_COL", count=1)],
        cargo=Cargo(colonists=2300),
    )
    planet = PlanetState(id="PL1")
    updated_fleet, updated_planet, event = resolve_colonize_task(
        fleet, planet, {"DE_COL": _design("DE_COL", "colony_ship")}
    )
    assert updated_fleet is None
    assert updated_planet is not None
    assert updated_planet.owner == "tim"
    assert updated_planet.population == 2300
    assert event.type == "colonised"
    assert event.colonists_landed == 2300


def test_successful_colonisation_deposits_recovery_and_fleet_minerals():
    fleet = Fleet(
        id="FL1",
        owner="tim",
        position=Position(x=0, y=0),
        composition=[FleetComposition(design_id="DE_COL", count=2)],
        cargo=Cargo(colonists=1500, ironium=8, boranium=6, germanium=4),
    )
    planet = PlanetState(id="PL1", minerals=Minerals(ironium=1, boranium=2, germanium=3))
    _, updated_planet, event = resolve_colonize_task(
        fleet, planet, {"DE_COL": _design("DE_COL", "colony_ship")}
    )
    assert updated_planet is not None
    assert updated_planet.minerals == Minerals(ironium=12, boranium=11, germanium=17)
    assert event.minerals_recovered == Minerals(ironium=3, boranium=3, germanium=10)


def test_mixed_fleet_colonisation_removes_only_colony_ships():
    fleet = Fleet(
        id="FL1",
        owner="tim",
        position=Position(x=0, y=0),
        composition=[
            FleetComposition(design_id="DE_COL", count=1),
            FleetComposition(design_id="DE_SCOUT", count=2),
        ],
        cargo=Cargo(colonists=500, ironium=2),
    )
    planet = PlanetState(id="PL1")
    updated_fleet, _, _ = resolve_colonize_task(
        fleet,
        planet,
        {
            "DE_COL": _design("DE_COL", "colony_ship"),
            "DE_SCOUT": _design("DE_SCOUT", "scout", cargo_capacity=0),
        },
    )
    assert updated_fleet is not None
    assert updated_fleet.composition == [FleetComposition(design_id="DE_SCOUT", count=2)]
    assert updated_fleet.cargo == Cargo()


def test_colonize_task_executes_on_arrival_and_dissolves_fleet():
    colony_design = _design("DE_COL", "colony_ship")
    scout_design = _design("DE_SCOUT", "scout", cargo_capacity=0)
    fleets_by_id = {
        "FL1": Fleet(
            id="FL1",
            owner="tim",
            position=Position(x=0, y=0),
            composition=[FleetComposition(design_id="DE_COL", count=1)],
            cargo=Cargo(colonists=1000),
            waypoints=[Waypoint(x=0, y=0, task=WaypointTask(type="colonize"))],
        ),
        "FL2": Fleet(
            id="FL2",
            owner="tim",
            position=Position(x=10 * PARSEC, y=0),
            composition=[FleetComposition(design_id="DE_SCOUT", count=1)],
            waypoints=[],
        ),
    }
    planets_by_id = {"PL1": PlanetState(id="PL1")}
    planets_by_coord = {(0, 0): planets_by_id["PL1"]}
    moved, events = move_fleets(
        fleets_by_id,
        {"DE_COL": 6, "DE_SCOUT": 6},
        planets_by_coord,
        {"DE_COL": colony_design, "DE_SCOUT": scout_design},
        planets_by_id,
    )
    assert {fleet.id for fleet in moved} == {"FL2"}
    assert planets_by_id["PL1"].owner == "tim"
    assert len(events) == 1
    assert events[0].type == "colonised"


def test_colonize_failure_consumes_waypoint_and_keeps_other_state():
    colony_design = _design("DE_COL", "colony_ship")
    fleets_by_id = {
        "FL1": Fleet(
            id="FL1",
            owner="tim",
            position=Position(x=0, y=0),
            composition=[FleetComposition(design_id="DE_COL", count=1)],
            cargo=Cargo(colonists=500),
            waypoints=[
                Waypoint(x=0, y=0, task=WaypointTask(type="colonize")),
                Waypoint(x=6 * PARSEC, y=0),
            ],
        ),
        "FL2": Fleet(
            id="FL2",
            owner="tim",
            position=Position(x=50, y=50),
            composition=[FleetComposition(design_id="DE_COL", count=1)],
            cargo=Cargo(colonists=200),
            waypoints=[],
        ),
    }
    planets_by_id = {"PL1": PlanetState(id="PL1", owner="sara"), "PL2": PlanetState(id="PL2")}
    planets_by_coord = {(0, 0): planets_by_id["PL1"], (100, 100): planets_by_id["PL2"]}
    moved, events = move_fleets(
        fleets_by_id,
        {"DE_COL": 6},
        planets_by_coord,
        {"DE_COL": colony_design},
        planets_by_id,
    )
    fl1 = next(f for f in moved if f.id == "FL1")
    assert fl1.position.x == 6 * PARSEC
    assert len(fl1.waypoints) == 0
    assert planets_by_id["PL2"].owner is None
    assert next(f for f in moved if f.id == "FL2").position == Position(x=50, y=50)
    assert len(events) == 1
    assert events[0].type == "colonize_failed"
    assert events[0].reason == "planet_already_owned"
