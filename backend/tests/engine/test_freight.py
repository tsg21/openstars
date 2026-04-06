"""Tests for freight resolution helpers."""

from openstars.engine.models import (
    Cargo,
    CargoOrder,
    Design,
    DesignCost,
    Fleet,
    FleetComposition,
    Minerals,
    PlanetState,
    Scanner,
    WaypointTask,
)
from openstars.engine.resolve_steps.freight import (
    execute_transport_task,
    fleet_cargo_capacity,
    resolve_load,
    resolve_unload,
    used_capacity,
)


def test_resolve_load_all_capped_by_capacity():
    assert resolve_load("load_all", None, available=100, held=10, remaining_cap=20) == 20


def test_resolve_load_amount_partial_if_unavailable():
    assert resolve_load("load_amount", 30, available=12, held=0, remaining_cap=30) == 12


def test_resolve_load_up_to_target():
    assert resolve_load("load_up_to", 50, available=100, held=10, remaining_cap=100) == 40
    assert resolve_load("load_up_to", 10, available=100, held=10, remaining_cap=100) == 0
    assert resolve_load("load_up_to", 5, available=100, held=10, remaining_cap=100) == 0


def test_resolve_unload_all():
    assert resolve_unload("unload_all", None, held=25) == 25


def test_resolve_unload_amount_partial_if_less_held():
    assert resolve_unload("unload_amount", 30, held=12) == 12


def test_resolve_unload_but():
    assert resolve_unload("unload_but", 10, held=30) == 20


def test_fleet_cargo_capacity():
    fleet = Fleet(
        id="FL1",
        name="Fleet #1",
        owner="tim",
        position={"x": 0, "y": 0},
        composition=[
            FleetComposition(design_id="DE1", count=2),
            FleetComposition(design_id="DE2", count=3),
        ],
    )
    designs = {
        "DE1": Design(
            id="DE1",
            owner="tim",
            name="A",
            hull="a",
            speed=6,
            scanner=Scanner(normal=0, penetrating=0),
            cargo_capacity=10,
            cost=DesignCost(resources=10, minerals=Minerals()),
        ),
        "DE2": Design(
            id="DE2",
            owner="tim",
            name="B",
            hull="b",
            speed=6,
            scanner=Scanner(normal=0, penetrating=0),
            cargo_capacity=4,
            cost=DesignCost(resources=10, minerals=Minerals()),
        ),
    }
    assert fleet_cargo_capacity(fleet, designs) == 32


def test_used_capacity():
    assert used_capacity(Cargo(ironium=3, boranium=2, germanium=1, colonists=0)) == 6


def test_colonist_capacity_rounding():
    assert used_capacity(Cargo(colonists=100)) == 1
    assert used_capacity(Cargo(colonists=101)) == 2
    assert used_capacity(Cargo(colonists=200)) == 2


def test_execute_transport_task_colonists_respects_rounding_capacity():
    fleet = Fleet(
        id="FL1",
        name="Fleet #1",
        owner="tim",
        position={"x": 0, "y": 0},
        composition=[FleetComposition(design_id="DE1", count=1)],
        cargo=Cargo(colonists=99),
    )
    design = Design(
        id="DE1",
        owner="tim",
        name="Freighter",
        hull="small_freighter",
        speed=6,
        scanner=Scanner(normal=0, penetrating=0),
        cargo_capacity=2,
        cost=DesignCost(resources=10, minerals=Minerals()),
    )
    planet = PlanetState(id="PL1", owner="tim", population=1000)
    task = WaypointTask(
        type="transport",
        orders=[CargoOrder(cargo_type="colonists", action="load_amount", amount=200)],
    )
    updated_fleet, updated_planet = execute_transport_task(fleet, planet, task, {"DE1": design})
    assert updated_fleet.cargo.colonists == 199
    assert updated_planet.population == 900
