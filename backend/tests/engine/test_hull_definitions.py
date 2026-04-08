"""Tests for designer hull definitions."""

from openstars.engine.hull_definitions import SLOT_CATEGORIES, load_hull_registry


def test_hull_slot_ids_are_unique_per_hull():
    registry = load_hull_registry()
    for hull in registry.ship_hulls:
        slot_ids = [slot.slot_id for slot in hull.slots]
        assert len(slot_ids) == len(set(slot_ids))


def test_hull_slot_categories_are_valid():
    registry = load_hull_registry()
    valid_categories = set(SLOT_CATEGORIES)
    for hull in registry.ship_hulls:
        for slot in hull.slots:
            assert set(slot.slot_categories).issubset(valid_categories)


def test_engine_required_slots_marked_required():
    registry = load_hull_registry()
    for hull in registry.ship_hulls:
        required_engine_slots = [
            slot for slot in hull.slots if slot.required and "engine" in slot.slot_categories
        ]
        assert len(required_engine_slots) >= hull.engine_required_slots
