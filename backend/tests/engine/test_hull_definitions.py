"""Tests for designer hull definitions."""

from typing import get_args

from openstars.engine.component_catalogue import SlotCategory, load_component_catalogue


def _designer_hulls():
    catalogue = load_component_catalogue()
    return [
        hull
        for hull in catalogue.by_type["hull"]
        if hull.hull is not None and hull.hull.domain == "ship" and hull.hull.slots
    ]


def _layout_hulls():
    catalogue = load_component_catalogue()
    return [hull for hull in catalogue.by_type["hull"] if hull.hull is not None and hull.hull.slots]


def test_hull_slot_numbers_are_unique_per_hull():
    for hull in _designer_hulls():
        slot_numbers = [slot.slot_number for slot in hull.hull.slots]
        assert len(slot_numbers) == len(set(slot_numbers))


def test_hull_slot_categories_are_valid():
    valid_categories = set(get_args(SlotCategory))
    for hull in _designer_hulls():
        for slot in hull.hull.slots:
            assert set(slot.slot_categories).issubset(valid_categories)


def test_ship_hulls_have_required_engine_slot():
    for hull in _designer_hulls():
        required_engine_slots = [
            slot for slot in hull.hull.slots if slot.required and "engine" in slot.slot_categories
        ]
        assert required_engine_slots


def test_hull_slots_use_uniform_two_by_two_layout_cells():
    for hull in _layout_hulls():
        for slot in hull.hull.slots:
            assert slot.size.w == 2
            assert slot.size.h == 2
