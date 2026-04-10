"""Tests for colonisation task resolution."""

from openstars.engine.colonisation import COLONY_SHIP_HULL
from openstars.engine.models import (
    Cargo,
    Design,
    DesignCost,
    Fleet,
    FleetComposition,
    Minerals,
    PlanetState,
    Position,
    Scanner,
)
from openstars.engine.resolve_steps.colonisation import (
    UNKNOWN_PLANET_NAME,
    colony_ship_entries,
    execute_colonise_task,
    fleet_has_colony_ship,
    recovered_colony_ship_minerals,
)


def _design(
    design_id: str,
    name: str,
    hull: str,
    cargo_capacity: int = 0,
) -> Design:
    return Design(
        id=design_id,
        owner="tim",
        name=name,
        hull=hull,
        fuel_usage=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        fuel_capacity=100,
        scanner=Scanner(normal=0, penetrating=0),
        cargo_capacity=cargo_capacity,
        cost=DesignCost(resources=10, minerals=Minerals()),
    )


def _fleet(
    composition: list[FleetComposition],
    cargo: Cargo | None = None,
) -> Fleet:
    return Fleet(
        id="FL1",
        name="Fleet #1",
        owner="tim",
        position=Position(x=0, y=0),
        composition=composition,
        cargo=cargo or Cargo(),
    )


def test_fleet_has_colony_ship():
    designs = {
        "DE1": _design("DE1", "Colony Ship", COLONY_SHIP_HULL, cargo_capacity=25),
        "DE2": _design("DE2", "Escort", "scout"),
    }
    fleet = _fleet(
        [
            FleetComposition(design_id="DE1", count=1),
            FleetComposition(design_id="DE2", count=1),
        ]
    )

    assert fleet_has_colony_ship(fleet, designs) is True
    assert len(colony_ship_entries(fleet, designs)) == 1


def test_recovered_colony_ship_minerals_sums_counts():
    recovered = recovered_colony_ship_minerals(
        [
            FleetComposition(design_id="DE1", count=2),
            FleetComposition(design_id="DE2", count=1),
        ]
    )

    assert recovered.ironium == 3
    assert recovered.boranium == 3
    assert recovered.germanium == 15


def test_execute_colonise_task_success_establishes_colony_and_clears_cargo():
    designs = {"DE1": _design("DE1", "Colony Ship", COLONY_SHIP_HULL, cargo_capacity=25)}
    fleet = _fleet(
        [FleetComposition(design_id="DE1", count=1)],
        cargo=Cargo(ironium=2, boranium=3, germanium=4, colonists=2500),
    )
    planet = PlanetState(id="PL1")

    result = execute_colonise_task(fleet, planet, designs, planet_name="Proxima II")

    assert result.planet is not None
    assert result.planet.owner == "tim"
    assert result.planet.population == 2500
    assert result.planet.minerals.ironium == 3
    assert result.planet.minerals.boranium == 4
    assert result.planet.minerals.germanium == 9
    assert result.fleet.cargo == Cargo()
    assert result.fleet.composition == []
    assert result.dissolve_fleet is True
    assert result.events[0].code == "colonisation.colonised"
    assert result.events[0].values == ["Colony Ship", "Proxima II", 2500, 1, 1, 5]


def test_execute_colonise_task_recovers_minerals_per_colony_ship():
    designs = {"DE1": _design("DE1", "Colony Ship", COLONY_SHIP_HULL, cargo_capacity=25)}
    fleet = _fleet(
        [FleetComposition(design_id="DE1", count=2)],
        cargo=Cargo(colonists=2500),
    )
    planet = PlanetState(id="PL1")

    result = execute_colonise_task(fleet, planet, designs, planet_name="Proxima II")

    assert result.planet is not None
    assert result.planet.minerals.ironium == 2
    assert result.planet.minerals.boranium == 2
    assert result.planet.minerals.germanium == 10


def test_execute_colonise_task_mixed_fleet_leaves_escorts_intact():
    designs = {
        "DE1": _design("DE1", "Colony Ship", COLONY_SHIP_HULL, cargo_capacity=25),
        "DE2": _design("DE2", "Escort", "scout"),
    }
    fleet = _fleet(
        [
            FleetComposition(design_id="DE1", count=1),
            FleetComposition(design_id="DE2", count=2),
        ],
        cargo=Cargo(colonists=2500),
    )
    planet = PlanetState(id="PL1")

    result = execute_colonise_task(fleet, planet, designs, planet_name="Proxima II")

    assert result.dissolve_fleet is False
    assert result.fleet.composition == [FleetComposition(design_id="DE2", count=2)]


def test_execute_colonise_task_no_planet():
    designs = {"DE1": _design("DE1", "Colony Ship", COLONY_SHIP_HULL, cargo_capacity=25)}
    fleet = _fleet(
        [FleetComposition(design_id="DE1", count=1)],
        cargo=Cargo(colonists=2500),
    )

    result = execute_colonise_task(fleet, None, designs)

    assert result.planet is None
    assert result.dissolve_fleet is False
    assert result.events[0].source_id is None
    assert result.events[0].values == ["Colony Ship", UNKNOWN_PLANET_NAME, "no_planet"]


def test_execute_colonise_task_planet_already_owned():
    designs = {"DE1": _design("DE1", "Colony Ship", COLONY_SHIP_HULL, cargo_capacity=25)}
    fleet = _fleet(
        [FleetComposition(design_id="DE1", count=1)],
        cargo=Cargo(colonists=2500),
    )
    planet = PlanetState(id="PL1", owner="sara", population=1200)

    result = execute_colonise_task(fleet, planet, designs, planet_name="Proxima II")

    assert result.planet == planet
    assert result.events[0].values == ["Colony Ship", "Proxima II", "planet_already_owned"]


def test_execute_colonise_task_no_colony_ship():
    designs = {"DE2": _design("DE2", "Escort", "scout")}
    fleet = _fleet(
        [FleetComposition(design_id="DE2", count=1)],
        cargo=Cargo(colonists=2500),
    )
    planet = PlanetState(id="PL1")

    result = execute_colonise_task(fleet, planet, designs, planet_name="Proxima II")

    assert result.events[0].values == ["Escort", "Proxima II", "no_colony_ship"]


def test_execute_colonise_task_no_colonists():
    designs = {"DE1": _design("DE1", "Colony Ship", COLONY_SHIP_HULL, cargo_capacity=25)}
    fleet = _fleet([FleetComposition(design_id="DE1", count=1)], cargo=Cargo())
    planet = PlanetState(id="PL1")

    result = execute_colonise_task(fleet, planet, designs, planet_name="Proxima II")

    assert result.events[0].values == ["Colony Ship", "Proxima II", "no_colonists"]
