"""Tests for production helper functions."""

from openstars.engine.models import Minerals, PlanetState, ProductionProgress, ProductionQueueItem
from openstars.engine.resolve_steps.production import (
    PRODUCTION_COSTS,
    apply_completed_unit,
    consume_completed_unit,
    get_production_cost,
    largest_payable_resource_increment,
    proportional_mineral_spend,
    remove_queue_item_quantity,
    spend_production_increment,
)


def test_production_cost_tables_match_prd_12():
    mine_cost = get_production_cost("mine")
    factory_cost = get_production_cost("factory")

    assert mine_cost.resources == 5
    assert mine_cost.minerals == Minerals()
    assert factory_cost.resources == 10
    assert factory_cost.minerals == Minerals(germanium=4)
    assert PRODUCTION_COSTS["factory"] == factory_cost


def test_proportional_mineral_thresholds_for_factory_progress():
    factory_cost = get_production_cost("factory")

    assert proportional_mineral_spend(2, factory_cost).germanium == 0
    assert proportional_mineral_spend(3, factory_cost).germanium == 1
    assert proportional_mineral_spend(5, factory_cost).germanium == 2
    assert proportional_mineral_spend(8, factory_cost).germanium == 3
    assert proportional_mineral_spend(10, factory_cost).germanium == 4


def test_largest_payable_increment_blocks_factory_without_germanium():
    factory_cost = get_production_cost("factory")
    progress = ProductionProgress(
        resources_spent=4,
        minerals_spent=Minerals(germanium=1),
    )

    increment = largest_payable_resource_increment(
        progress=progress,
        available_resources=4,
        available_minerals=Minerals(),
        cost=factory_cost,
    )

    assert increment == 0


def test_spend_increment_uses_largest_payable_resource_increment():
    factory_cost = get_production_cost("factory")
    progress, remaining_resources, remaining_minerals = spend_production_increment(
        progress=ProductionProgress(),
        available_resources=10,
        available_minerals=Minerals(germanium=2),
        cost=factory_cost,
    )

    assert progress.resources_spent == 7
    assert progress.minerals_spent == Minerals(germanium=2)
    assert remaining_resources == 3
    assert remaining_minerals == Minerals()


def test_completion_resets_progress_and_decrements_quantity():
    item = ProductionQueueItem(
        id="PQ000001",
        item_type="factory",
        quantity=3,
        progress=ProductionProgress(
            resources_spent=10,
            minerals_spent=Minerals(germanium=4),
        ),
    )

    updated_item = consume_completed_unit(item)

    assert updated_item is not None
    assert updated_item.quantity == 2
    assert updated_item.progress == ProductionProgress()


def test_completion_removes_last_item():
    item = ProductionQueueItem(id="PQ000001", item_type="mine", quantity=1)

    assert consume_completed_unit(item) is None


def test_apply_completed_unit_effects():
    planet = PlanetState(id="PL000001", mines=2, factories=3)

    mined = apply_completed_unit(planet, "mine")
    factory_built = apply_completed_unit(planet, "factory")

    assert mined.mines == 3
    assert mined.factories == 3
    assert factory_built.mines == 2
    assert factory_built.factories == 4


def test_remove_semantics_can_discard_partial_progress_without_refunds():
    item = ProductionQueueItem(
        id="PQ000001",
        item_type="factory",
        quantity=4,
        progress=ProductionProgress(
            resources_spent=6,
            minerals_spent=Minerals(germanium=2),
        ),
    )

    updated_item = remove_queue_item_quantity(
        item,
        quantity=1,
        discard_in_progress_unit=True,
    )

    assert updated_item is not None
    assert updated_item.quantity == 3
    assert updated_item.progress == ProductionProgress()


def test_remove_semantics_can_preserve_partial_progress_when_not_removed():
    item = ProductionQueueItem(
        id="PQ000001",
        item_type="factory",
        quantity=4,
        progress=ProductionProgress(
            resources_spent=6,
            minerals_spent=Minerals(germanium=2),
        ),
    )

    updated_item = remove_queue_item_quantity(
        item,
        quantity=1,
        discard_in_progress_unit=False,
    )

    assert updated_item is not None
    assert updated_item.quantity == 3
    assert updated_item.progress.resources_spent == 6


def test_remove_semantics_remove_entire_entry():
    item = ProductionQueueItem(id="PQ000001", item_type="mine", quantity=2)

    assert remove_queue_item_quantity(item, quantity=2, discard_in_progress_unit=False) is None
