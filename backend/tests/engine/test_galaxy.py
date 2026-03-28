"""Tests for galaxy generation."""

import re

from openstars.engine.galaxy import GALAXY_SIZES, generate_galaxy

ID_PATTERN = re.compile(r"^PL[a-z0-9]{6}$")


def test_determinism():
    g1 = generate_galaxy("Test", "small", seed=42)
    g2 = generate_galaxy("Test", "small", seed=42)
    assert g1 == g2


def test_planet_count():
    g = generate_galaxy("Test", "small", seed=42, num_planets=30)
    assert len(g.planets) == 30


def test_default_planet_count():
    g = generate_galaxy("Test", "small", seed=42)
    assert len(g.planets) == 50  # default for small


def test_planets_within_bounds():
    g = generate_galaxy("Test", "small", seed=42)
    max_coord = (1 << GALAXY_SIZES["small"]) - 1
    for p in g.planets:
        assert 0 <= p.x <= max_coord
        assert 0 <= p.y <= max_coord


def test_minimum_separation():
    """All planets must be at least min_sep apart."""
    g = generate_galaxy("Test", "small", seed=42)
    max_coord = (1 << GALAXY_SIZES["small"]) - 1
    min_sep = max_coord // 200
    min_sep_sq = min_sep * min_sep

    for i, p1 in enumerate(g.planets):
        for p2 in g.planets[i + 1 :]:
            dx = p1.x - p2.x
            dy = p1.y - p2.y
            dist_sq = dx * dx + dy * dy
            assert dist_sq >= min_sep_sq, f"Planets {p1.name} and {p2.name} too close"


def test_unique_ids():
    g = generate_galaxy("Test", "small", seed=42)
    ids = [p.id for p in g.planets]
    assert len(ids) == len(set(ids))


def test_id_format():
    g = generate_galaxy("Test", "small", seed=42)
    for p in g.planets:
        assert ID_PATTERN.match(p.id), f"Bad ID format: {p.id}"


def test_unique_names():
    g = generate_galaxy("Test", "small", seed=42)
    names = [p.name for p in g.planets]
    assert len(names) == len(set(names))


def test_different_seeds():
    g1 = generate_galaxy("Test", "small", seed=42)
    g2 = generate_galaxy("Test", "small", seed=999)
    # Different seeds should produce different planet positions
    pos1 = [(p.x, p.y) for p in g1.planets]
    pos2 = [(p.x, p.y) for p in g2.planets]
    assert pos1 != pos2


def test_galaxy_metadata():
    g = generate_galaxy("My Galaxy", "medium", seed=123)
    assert g.galaxy.name == "My Galaxy"
    assert g.galaxy.size == "medium"
    assert g.galaxy.seed == 123
