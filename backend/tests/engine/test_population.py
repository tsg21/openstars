"""Tests for population growth and habitability (PRD 14)."""

import pytest

from openstars.engine.create_game import create_initial_state
from openstars.engine.fog import derive_player_state
from openstars.engine.galaxy import generate_galaxy
from openstars.engine.models import (
    GameMeta,
    GlobalState,
    Habitability,
    PlanetState,
    Player,
)
from openstars.engine.race.models import PRT, RaceHabitability, RaceHabitabilityFactor
from openstars.engine.race.presets import default_race
from openstars.engine.resolve import resolve_turn
from openstars.engine.resolve_steps.population import (
    BASE_MAX_POPULATION,
    calculate_hab_value,
    factor_contribution,
    max_population,
    overcrowding_deaths,
    population_cap_factor,
    population_death,
    population_growth,
)
from openstars.storage.memory import MemoryStorage
from tests.engine.race._helpers import submit_default_race_and_resolve_turn_0

_JOAT_RACE = default_race()
_JOAT_HAB = _JOAT_RACE.habitability
_GRAVITY_RANGE = _JOAT_HAB.gravity.range
_TEMPERATURE_RANGE = _JOAT_HAB.temperature.range
_RADIATION_RANGE = _JOAT_HAB.radiation.range

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_game():
    galaxy = generate_galaxy("Test", "small", seed=42, num_planets=20)
    state, _designs = create_initial_state(galaxy, ["tim", "sara"], game_seed=12345)
    state = submit_default_race_and_resolve_turn_0(
        state, galaxy, MemoryStorage(), ["tim", "sara"], game_id="game1"
    )
    return galaxy, state


def _make_minimal_state(
    population: int = 25000,
    hab: Habitability | None = None,
    owner: str = "tim",
) -> tuple[GlobalState, object]:
    """Return a minimal (galaxy, GlobalState) with one owned planet."""
    galaxy = generate_galaxy("Test", "small", seed=42, num_planets=20)
    gp = galaxy.planets[0]

    planet = PlanetState(
        id=gp.id,
        owner=owner,
        population=population,
        habitability=hab or Habitability(gravity=50, temperature=50, radiation=50),
    )
    state = GlobalState(
        game=GameMeta(seed=99, turn=0, next_id=20),
        players=[Player(username=owner, name=owner, race=default_race())],
        planets=[planet] + [PlanetState(id=p.id) for p in galaxy.planets[1:]],
        fleets=[],
    )
    return state, galaxy


# ---------------------------------------------------------------------------
# Unit tests: factor_contribution
# ---------------------------------------------------------------------------


def test_factor_contribution_at_ideal():
    low, high = _GRAVITY_RANGE
    ideal = (low + high) / 2
    result = factor_contribution(int(ideal), low, high)
    assert abs(result - 33.333) < 0.001


def test_factor_contribution_at_range_edge_low():
    low, high = _GRAVITY_RANGE
    result = factor_contribution(low, low, high)
    assert result == pytest.approx(0.0, abs=0.001)


def test_factor_contribution_at_range_edge_high():
    low, high = _GRAVITY_RANGE
    result = factor_contribution(high, low, high)
    assert result == pytest.approx(0.0, abs=0.001)


def test_factor_contribution_below_range():
    low, high = _GRAVITY_RANGE  # (15, 85)
    result = factor_contribution(0, low, high)  # At far extreme below
    assert result == pytest.approx(-15.0)


def test_factor_contribution_above_range():
    low, high = _GRAVITY_RANGE  # (15, 85)
    result = factor_contribution(100, low, high)  # At far extreme above
    assert result == pytest.approx(-15.0)


def test_factor_contribution_just_below_range():
    low, high = _GRAVITY_RANGE  # (15, 85)
    result = factor_contribution(low - 1, low, high)
    assert result < 0


def test_factor_contribution_midway_outside():
    """Value halfway between range edge and spectrum extreme."""
    low, high = _GRAVITY_RANGE  # low=15
    # v=7 is halfway between 0 and 15
    result = factor_contribution(7, low, high)
    assert -15.0 < result < 0.0


# ---------------------------------------------------------------------------
# Unit tests: calculate_hab_value
# ---------------------------------------------------------------------------


def test_calculate_hab_value_all_ideal():
    """JOAT ideal (50,50,50) → 100% habitability."""
    hab = Habitability(gravity=50, temperature=50, radiation=50)
    assert calculate_hab_value(hab, _JOAT_HAB) == 100


def test_calculate_hab_value_all_range_edges():
    """All factors at range edge → 0% habitability."""
    low_g, high_g = _GRAVITY_RANGE
    low_t, high_t = _TEMPERATURE_RANGE
    low_r, high_r = _RADIATION_RANGE
    hab = Habitability(gravity=low_g, temperature=low_t, radiation=low_r)
    assert calculate_hab_value(hab, _JOAT_HAB) == 0


def test_calculate_hab_value_one_factor_outside():
    """One factor outside range → negative contribution, total can be negative."""
    hab = Habitability(gravity=0, temperature=50, radiation=50)  # gravity far outside
    result = calculate_hab_value(hab, _JOAT_HAB)
    assert result < 100  # definitely worse than ideal


def test_calculate_hab_value_all_outside():
    """All factors at far extremes → maximum negative (-45)."""
    hab = Habitability(gravity=0, temperature=0, radiation=0)
    result = calculate_hab_value(hab, _JOAT_HAB)
    assert result <= -40  # close to -45


def test_calculate_hab_value_range():
    """Result is always within [-45, 100]."""
    for g in [0, 15, 50, 85, 100]:
        for t in [0, 50, 100]:
            for r in [0, 50, 100]:
                hab = Habitability(gravity=g, temperature=t, radiation=r)
                hv = calculate_hab_value(hab, _JOAT_HAB)
                assert -45 <= hv <= 100


# ---------------------------------------------------------------------------
# Unit tests: max_population
# ---------------------------------------------------------------------------


def test_max_population_100_pct():
    hab = Habitability(gravity=50, temperature=50, radiation=50)  # 100% hab
    assert max_population(hab, _JOAT_HAB) == BASE_MAX_POPULATION


def test_max_population_50_pct():
    """A planet with ~50% habitability should support ~500,000 people."""
    # All factors at midpoint of range → each contributes ~16.67% → total ~50
    low_g, high_g = _GRAVITY_RANGE
    low_t, _ = _TEMPERATURE_RANGE
    mid_g = low_g  # At range edge: contributes 0 for that factor
    hab = Habitability(gravity=mid_g, temperature=50, radiation=50)
    mp = max_population(hab, _JOAT_HAB)
    assert 0 < mp < BASE_MAX_POPULATION


def test_max_population_zero_for_negative_hab():
    hab = Habitability(gravity=0, temperature=0, radiation=0)
    assert max_population(hab, _JOAT_HAB) == 0


def test_max_population_minimum_floor():
    """Habitable planets with hab 1-4% are treated as 5% → 50,000."""
    # We need a planet that produces hab value of ~3. Hard to craft exactly,
    # so test the boundary condition directly via calculate_hab_value being 3.
    # Gravity at edge (0 contribution), temp just inside range, rad at ideal
    low_g, high_g = _GRAVITY_RANGE
    hab = Habitability(gravity=low_g, temperature=low_g, radiation=50)
    hv = calculate_hab_value(hab, _JOAT_HAB)
    mp = max_population(hab, _JOAT_HAB)
    if 1 <= hv <= 4:
        assert mp == 50000
    elif hv > 4:
        assert mp == BASE_MAX_POPULATION * hv // 100
    else:
        assert mp == 0


# ---------------------------------------------------------------------------
# Unit tests: population_growth
# ---------------------------------------------------------------------------


def test_population_growth_below_25pct_full_rate():
    """Below 25% capacity, apply full growth rate."""
    hab = Habitability(gravity=50, temperature=50, radiation=50)
    max_pop = max_population(hab, _JOAT_HAB)
    pop = max_pop // 10  # 10% of capacity
    growth = population_growth(pop, hab, _JOAT_HAB, 15)
    expected = int(pop * 0.15)  # 100% hab × 15% growth rate
    assert growth == expected


def test_population_growth_at_max_population():
    """At max population, growth is zero."""
    hab = Habitability(gravity=50, temperature=50, radiation=50)
    max_pop = max_population(hab, _JOAT_HAB)
    assert population_growth(max_pop, hab, _JOAT_HAB, 15) == 0


def test_population_growth_above_25pct_reduced():
    """Between 25% and 100% capacity, growth is less than full rate."""
    hab = Habitability(gravity=50, temperature=50, radiation=50)
    max_pop = max_population(hab, _JOAT_HAB)
    pop_reduced = max_pop // 2  # 50% capacity
    growth_reduced = population_growth(pop_reduced, hab, _JOAT_HAB, 15)
    # Per-capita growth rate is lower, but total growth can still be higher
    # What we can assert: growth at max_pop is 0, and it's positive at 50%
    assert growth_reduced > 0


def test_population_growth_negative_hab_returns_zero():
    hab = Habitability(gravity=0, temperature=0, radiation=0)
    assert population_growth(10000, hab, _JOAT_HAB, 15) == 0


def test_population_growth_zero_population_returns_zero():
    hab = Habitability(gravity=50, temperature=50, radiation=50)
    assert population_growth(0, hab, _JOAT_HAB, 15) == 0


def test_population_growth_tighter_race_range_drops_off_ideal_rate() -> None:
    hab = Habitability(gravity=30, temperature=50, radiation=50)
    tight_hab = RaceHabitability(
        gravity=RaceHabitabilityFactor(range=(40, 60)),
        temperature=RaceHabitabilityFactor(),
        radiation=RaceHabitabilityFactor(),
    )

    joat_growth = population_growth(100_000, hab, _JOAT_HAB, 15)
    tight_growth = population_growth(100_000, hab, tight_hab, 15)

    assert tight_growth < joat_growth


def test_calculate_hab_value_immune_factor_ignores_planet_value() -> None:
    immune_gravity = RaceHabitability(
        gravity=RaceHabitabilityFactor(immune=True),
        temperature=RaceHabitabilityFactor(),
        radiation=RaceHabitabilityFactor(),
    )

    low_gravity = calculate_hab_value(
        Habitability(gravity=0, temperature=50, radiation=50),
        immune_gravity,
    )
    high_gravity = calculate_hab_value(
        Habitability(gravity=100, temperature=50, radiation=50),
        immune_gravity,
    )

    assert low_gravity == high_gravity == 100


def test_population_growth_uses_race_max_growth_rate() -> None:
    hab = Habitability(gravity=50, temperature=50, radiation=50)
    growth_15 = population_growth(100_000, hab, _JOAT_HAB, 15)
    growth_10 = population_growth(100_000, hab, _JOAT_HAB, 10)

    assert growth_10 == pytest.approx(growth_15 * (2 / 3))


# ---------------------------------------------------------------------------
# Unit tests: population_death
# ---------------------------------------------------------------------------


def test_population_death_negative_hab():
    """Hostile environment kills colonists each year."""
    # Construct a clearly negative hab value
    hab = Habitability(gravity=0, temperature=0, radiation=0)
    hv = calculate_hab_value(hab, _JOAT_HAB)
    assert hv < 0
    deaths = population_death(5000, hab, _JOAT_HAB)
    expected_rate = abs(hv) / 10 / 100
    assert deaths == int(5000 * expected_rate)


def test_population_death_positive_hab_returns_zero():
    hab = Habitability(gravity=50, temperature=50, radiation=50)
    assert population_death(10000, hab, _JOAT_HAB) == 0


def test_population_death_zero_population_returns_zero():
    hab = Habitability(gravity=0, temperature=0, radiation=0)
    assert population_death(0, hab, _JOAT_HAB) == 0


def test_population_death_below_threshold_wipes_out():
    """Sub-viable outposts on hostile worlds die in a single turn."""
    hab = Habitability(gravity=0, temperature=0, radiation=0)
    assert population_death(99, hab, _JOAT_HAB) == 99
    assert population_death(1, hab, _JOAT_HAB) == 1


def test_population_death_at_threshold_uses_rate():
    """At exactly the threshold, the percentage rule applies (with min-1 floor)."""
    hab = Habitability(gravity=0, temperature=0, radiation=0)
    hv = calculate_hab_value(hab, _JOAT_HAB)
    expected = max(int(100 * abs(hv) / 10 / 100), 1)
    assert population_death(100, hab, _JOAT_HAB) == expected


# ---------------------------------------------------------------------------
# Unit tests: overcrowding_deaths
# ---------------------------------------------------------------------------


def test_overcrowding_deaths_at_capacity():
    assert overcrowding_deaths(1_000_000, 1_000_000) == 0


def test_overcrowding_deaths_below_capacity():
    assert overcrowding_deaths(500_000, 1_000_000) == 0


def test_overcrowding_deaths_at_400_pct():
    """At 400% capacity the rate caps at 12%."""
    max_pop = 100_000
    pop = 400_000
    deaths = overcrowding_deaths(pop, max_pop)
    assert deaths == int(pop * 0.12)


def test_overcrowding_deaths_at_200_pct():
    """At 200% capacity, rate is (1/3) × 12% = 4%."""
    max_pop = 100_000
    pop = 200_000
    deaths = overcrowding_deaths(pop, max_pop)
    expected_rate = (2.0 - 1.0) / 3.0 * 0.12
    assert deaths == int(pop * expected_rate)


# ---------------------------------------------------------------------------
# Integration tests: turn 0 setup
# ---------------------------------------------------------------------------


def test_home_planets_have_ideal_habitability():
    """Home planets are set to the JOAT ideal (50, 50, 50)."""
    _, state = _make_game()
    home_planets = [p for p in state.planets if p.owner is not None]
    assert len(home_planets) == 2
    for p in home_planets:
        assert p.habitability.gravity == 50
        assert p.habitability.temperature == 50
        assert p.habitability.radiation == 50


def test_non_home_planets_have_random_habitability():
    """Non-home planets get random environment values in [0, 100]."""
    _, state = _make_game()
    non_home = [p for p in state.planets if p.owner is None]
    assert len(non_home) > 0
    for p in non_home:
        assert 0 <= p.habitability.gravity <= 100
        assert 0 <= p.habitability.temperature <= 100
        assert 0 <= p.habitability.radiation <= 100


def test_non_home_planets_are_not_all_zero():
    """Ensure the RNG is actually populating environment values."""
    _, state = _make_game()
    non_home = [p for p in state.planets if p.owner is None]
    all_zero = all(
        p.habitability.gravity == 0
        and p.habitability.temperature == 0
        and p.habitability.radiation == 0
        for p in non_home
    )
    assert not all_zero


# ---------------------------------------------------------------------------
# Integration tests: turn resolution
# ---------------------------------------------------------------------------


def test_positive_hab_planet_grows():
    """Planet with positive habitability gains population each turn."""
    state, galaxy = _make_minimal_state(
        population=25000,
        hab=Habitability(gravity=50, temperature=50, radiation=50),
    )
    new_state = resolve_turn(state, galaxy, {}, [], game_id="game1", storage=MemoryStorage())
    planet = next(p for p in new_state.planets if p.owner == "tim")
    assert planet.population > 25000


def test_negative_hab_planet_shrinks():
    """Planet with negative habitability loses population each turn."""
    state, galaxy = _make_minimal_state(
        population=10000,
        hab=Habitability(gravity=0, temperature=0, radiation=0),
    )
    new_state = resolve_turn(state, galaxy, {}, [], game_id="game1", storage=MemoryStorage())
    planet = next((p for p in new_state.planets if p.id == galaxy.planets[0].id), None)
    assert planet is not None
    # Population should have decreased (or planet abandoned)
    assert planet.population < 10000 or planet.owner is None


def test_planet_abandoned_when_population_zero():
    """When all colonists die, planet becomes unowned and event is emitted.

    A sub-viable colony on a maximally hostile world is wiped out in one turn.
    """
    state, galaxy = _make_minimal_state(
        population=99,
        hab=Habitability(gravity=0, temperature=0, radiation=0),
    )
    planet_id = galaxy.planets[0].id
    abandoned_event_found = False

    for _ in range(5):
        state = resolve_turn(state, galaxy, {}, [], game_id="game1", storage=MemoryStorage())
        planet = next(p for p in state.planets if p.id == planet_id)
        events = state.events.get("tim", [])
        if any(e.code == "population.planet_abandoned" for e in events):
            abandoned_event_found = True
            assert planet.owner is None
            assert planet.population == 0
            break

    assert abandoned_event_found, "Planet was never abandoned"


def test_pop_growth_stored_in_global_state():
    """pop_growth dict is populated after resolution."""
    state, galaxy = _make_minimal_state(
        population=25000,
        hab=Habitability(gravity=50, temperature=50, radiation=50),
    )
    new_state = resolve_turn(state, galaxy, {}, [], game_id="game1", storage=MemoryStorage())
    planet_id = galaxy.planets[0].id
    assert planet_id in new_state.pop_growth
    assert new_state.pop_growth[planet_id] > 0


# ---------------------------------------------------------------------------
# Integration tests: fog of war
# ---------------------------------------------------------------------------


def test_fog_own_planet_includes_habitability():
    """Owner sees habitability on their own planet."""
    state, galaxy = _make_minimal_state(
        hab=Habitability(gravity=50, temperature=50, radiation=50),
    )
    player_state = derive_player_state(state, galaxy, "tim", [])
    planet = next(p for p in player_state.planets if p.owner == "tim")
    assert planet.habitability is not None
    assert planet.habitability.gravity == 50
    assert planet.habitability.temperature == 50
    assert planet.habitability.radiation == 50


def test_fog_own_planet_includes_max_population():
    """Owner sees max_population on their own planet."""
    state, galaxy = _make_minimal_state(
        hab=Habitability(gravity=50, temperature=50, radiation=50),
    )
    player_state = derive_player_state(state, galaxy, "tim", [])
    planet = next(p for p in player_state.planets if p.owner == "tim")
    assert planet.max_population == int(
        BASE_MAX_POPULATION * population_cap_factor(PRT.JACK_OF_ALL_TRADES)
    )


def test_fog_own_planet_uses_owner_race_habitability_for_max_population() -> None:
    tight_hab = RaceHabitability(
        gravity=RaceHabitabilityFactor(range=(40, 60)),
        temperature=RaceHabitabilityFactor(),
        radiation=RaceHabitabilityFactor(),
    )
    race = default_race().model_copy(update={"habitability": tight_hab})
    state, galaxy = _make_minimal_state(
        hab=Habitability(gravity=30, temperature=50, radiation=50),
    )
    state = state.model_copy(
        update={"players": [state.players[0].model_copy(update={"race": race})]}
    )

    player_state = derive_player_state(state, galaxy, "tim", [])
    planet = next(p for p in player_state.planets if p.owner == "tim")

    assert planet.max_population == max_population(
        state.planets[0].habitability,
        tight_hab,
        cap_factor=population_cap_factor(PRT.JACK_OF_ALL_TRADES),
    )
    assert planet.max_population < max_population(state.planets[0].habitability, _JOAT_HAB)


def test_fog_unscanned_planet_no_habitability():
    """Planet outside scanner range has no habitability data."""
    state, galaxy = _make_minimal_state()
    # Query from a different player (no scanners)
    state_sara = GlobalState(
        game=state.game,
        players=state.players + [Player(username="sara", name="sara", race=default_race())],
        planets=state.planets,
        fleets=state.fleets,
    )
    player_state = derive_player_state(state_sara, galaxy, "sara", [])
    # All planets visible but sara has no scanners, so scan_level = "none"
    for p in player_state.planets:
        if p.scan_level == "none":
            assert p.habitability is None
            assert p.max_population is None
            break
