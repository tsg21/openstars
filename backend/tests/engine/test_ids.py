"""Tests for the entity ID generator."""

import re

from openstars.engine.ids import allocate_id

ID_PATTERN = re.compile(r"^[A-Z]{2}[a-z0-9]{6}$")


def test_format():
    entity_id, new_next = allocate_id(0, seed=42, prefix="PL")
    assert ID_PATTERN.match(entity_id), f"Bad format: {entity_id}"
    assert entity_id.startswith("PL")
    assert new_next == 1


def test_determinism():
    id1, _ = allocate_id(0, seed=42, prefix="PL")
    id2, _ = allocate_id(0, seed=42, prefix="PL")
    assert id1 == id2


def test_uniqueness():
    ids = set()
    next_id = 0
    for _ in range(1000):
        entity_id, next_id = allocate_id(next_id, seed=42, prefix="PL")
        ids.add(entity_id)
    assert len(ids) == 1000


def test_different_seeds_produce_different_ids():
    id1, _ = allocate_id(0, seed=42, prefix="PL")
    id2, _ = allocate_id(0, seed=999, prefix="PL")
    assert id1 != id2


def test_prefix_types():
    for prefix in ("PL", "FL", "DE"):
        entity_id, _ = allocate_id(0, seed=42, prefix=prefix)
        assert entity_id[:2] == prefix
        assert ID_PATTERN.match(entity_id)


def test_sequential_ids_look_random():
    """Consecutive counter values should produce very different-looking IDs."""
    id1, _ = allocate_id(0, seed=42, prefix="PL")
    id2, _ = allocate_id(1, seed=42, prefix="PL")
    # The suffixes should differ significantly
    assert id1[2:] != id2[2:]


def test_counter_increments():
    _, next1 = allocate_id(0, seed=42, prefix="PL")
    _, next2 = allocate_id(next1, seed=42, prefix="FL")
    _, next3 = allocate_id(next2, seed=42, prefix="DE")
    assert next1 == 1
    assert next2 == 2
    assert next3 == 3
