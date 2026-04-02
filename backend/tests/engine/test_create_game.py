"""Tests focused on Turn 0 design/fleet defaults."""

from openstars.engine.create_game import create_initial_state
from openstars.engine.galaxy import generate_galaxy


def _make_state():
    galaxy = generate_galaxy("Test", "small", seed=42, num_planets=20)
    state = create_initial_state(galaxy, ["tim", "sara"], game_seed=12345)
    return galaxy, state


def test_turn_0_includes_colony_ship_design_per_player():
    _, state = _make_state()
    colony_designs = [d for d in state.designs if d.hull == "colony_ship"]
    assert len(colony_designs) == 2
    assert {d.owner for d in colony_designs} == {"tim", "sara"}


def test_turn_0_includes_colony_ship_fleet_per_player_at_homeworld():
    galaxy, state = _make_state()
    designs_by_id = {d.id: d for d in state.designs}
    planet_positions = {p.id: (p.x, p.y) for p in galaxy.planets}
    colony_fleets = [
        f
        for f in state.fleets
        if any(designs_by_id[c.design_id].hull == "colony_ship" for c in f.composition)
    ]
    assert len(colony_fleets) == 2
    for fleet in colony_fleets:
        home = next(p for p in state.planets if p.owner == fleet.owner)
        home_position = planet_positions[home.id]
        assert (fleet.position.x, fleet.position.y) == home_position


def test_colony_ship_design_defaults():
    _, state = _make_state()
    colony_designs = [d for d in state.designs if d.hull == "colony_ship"]
    assert colony_designs
    for design in colony_designs:
        assert design.speed == 6
        assert design.cargo_capacity == 25
        assert design.hull == "colony_ship"
