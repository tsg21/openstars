"""Tests for Turn 0 generation and fog of war."""

from openstars.engine.create_game import STARTING_POPULATION, create_initial_state
from openstars.engine.fog import derive_player_state
from openstars.engine.galaxy import generate_galaxy


def _make_game():
    """Helper to create a 2-player small galaxy game."""
    galaxy = generate_galaxy("Test", "small", seed=42, num_planets=20)
    state = create_initial_state(galaxy, ["tim", "sara"], game_seed=12345)
    return galaxy, state


def test_player_count():
    _, state = _make_game()
    assert len(state.players) == 2
    assert state.players[0].username == "sara"  # sorted alphabetically
    assert state.players[1].username == "tim"


def test_designs():
    _, state = _make_game()
    assert len(state.designs) == 6  # scout + small freighter + colony ship per player
    owners = {d.owner for d in state.designs}
    assert owners == {"tim", "sara"}
    scouts = [d for d in state.designs if d.hull == "scout"]
    freighters = [d for d in state.designs if d.hull == "small_freighter"]
    colony_ships = [d for d in state.designs if d.hull == "colony_ship"]
    assert len(scouts) == 2
    assert len(freighters) == 2
    assert len(colony_ships) == 2
    for d in scouts:
        assert d.speed == 6
        assert d.scanner.normal == 150
        assert d.scanner.penetrating == 0
        assert d.id.startswith("DE")
    for d in colony_ships:
        assert d.speed == 6
        assert d.cargo_capacity == 25
        assert d.scanner.normal == 0
        assert d.scanner.penetrating == 0


def test_fleets():
    galaxy, state = _make_game()
    assert len(state.fleets) == 8  # 2 scout fleets + small freighter + colony ship per player
    owners = {f.owner for f in state.fleets}
    assert owners == {"tim", "sara"}
    for f in state.fleets:
        assert f.id.startswith("FL")
        assert len(f.composition) == 1
        assert f.waypoints == []
        assert f.cargo.colonists == 0


def test_fleet_names():
    """Starting fleets are named Fleet #1, #2, #3, #4 per player."""
    _, state = _make_game()
    for player in ("tim", "sara"):
        player_fleets = [f for f in state.fleets if f.owner == player]
        names = {f.name for f in player_fleets}
        assert names == {"Fleet #1", "Fleet #2", "Fleet #3", "Fleet #4"}


def test_two_starting_scouts_are_in_separate_fleets():
    """Each player starts with two one-scout fleets rather than one combined fleet."""
    _, state = _make_game()
    designs_by_id = {design.id: design for design in state.designs}

    for player in ("tim", "sara"):
      player_scout_fleets = [
          fleet
          for fleet in state.fleets
          if fleet.owner == player
          and any(
              designs_by_id[ship.design_id].hull == "scout"
              for ship in fleet.composition
          )
      ]
      assert len(player_scout_fleets) == 2
      for fleet in player_scout_fleets:
          assert len(fleet.composition) == 1
          assert fleet.composition[0].count == 1


def test_home_planets():
    _, state = _make_game()
    owned = [p for p in state.planets if p.owner is not None]
    assert len(owned) == 2
    for p in owned:
        assert p.population == STARTING_POPULATION
        assert p.starbase is not None
        assert p.starbase.type == "space_station"
        assert p.starbase.can_build_ships is True


def test_uncolonised_planets():
    _, state = _make_game()
    uncolonised = [p for p in state.planets if p.owner is None]
    assert len(uncolonised) == 18  # 20 - 2 home planets
    for p in uncolonised:
        assert p.population == 0
        assert p.starbase is None


def test_fleets_at_home_planets():
    """Each fleet should be at its owner's home planet."""
    galaxy, state = _make_game()
    planet_positions = {gp.id: (gp.x, gp.y) for gp in galaxy.planets}

    for fleet in state.fleets:
        # Find the owner's home planet
        home = next(p for p in state.planets if p.owner == fleet.owner)
        pos = planet_positions[home.id]
        assert fleet.position.x == pos[0]
        assert fleet.position.y == pos[1]


def test_turn_0():
    _, state = _make_game()
    assert state.game.turn == 0
    assert state.state_version == 1


def test_next_id_counter():
    galaxy, state = _make_game()
    # 20 planets + 6 designs + 8 fleets = 34
    assert state.game.next_id == 34


def test_home_planets_are_spread():
    """Home planets should be reasonably far apart."""
    galaxy, state = _make_game()
    planet_positions = {gp.id: (gp.x, gp.y) for gp in galaxy.planets}
    homes = [p for p in state.planets if p.owner is not None]
    assert len(homes) == 2
    h1 = planet_positions[homes[0].id]
    h2 = planet_positions[homes[1].id]
    dx = h1[0] - h2[0]
    dy = h1[1] - h2[1]
    dist_sq = dx * dx + dy * dy
    # Should be substantially more than 0
    assert dist_sq > 0


# --- Fog of war tests ---


def test_player_sees_own_planet():
    galaxy, state = _make_game()
    ps = derive_player_state(state, galaxy, "tim")
    own_planets = [p for p in ps.planets if p.owner == "tim"]
    assert len(own_planets) == 1
    assert own_planets[0].population == STARTING_POPULATION
    assert own_planets[0].starbase is not None


def test_player_sees_own_fleet():
    galaxy, state = _make_game()
    ps = derive_player_state(state, galaxy, "tim")
    own_fleets = [f for f in ps.fleets if f.owner == "tim"]
    assert len(own_fleets) == 4  # 2 scouts + small freighter + colony ship
    for f in own_fleets:
        assert f.composition is not None
        assert f.waypoints is not None


def test_own_designs_only():
    galaxy, state = _make_game()
    ps = derive_player_state(state, galaxy, "tim")
    for d in ps.designs:
        assert d.owner == "tim"
    assert len(ps.designs) == 3  # scout + small freighter + colony ship


def test_enemy_fleet_limited_info():
    """If enemy fleet is in scanner range, no composition/waypoints."""
    galaxy, state = _make_game()
    ps = derive_player_state(state, galaxy, "tim")
    enemy_fleets = [f for f in ps.fleets if f.owner != "tim"]
    for ef in enemy_fleets:
        assert ef.composition is None
        assert ef.waypoints is None


def test_turn_matches():
    galaxy, state = _make_game()
    ps = derive_player_state(state, galaxy, "tim")
    assert ps.state_version == 1
    assert ps.turn == 0
    assert ps.player == "tim"
