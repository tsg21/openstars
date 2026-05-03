"""Tests for the research projection in derive_player_state (PRD 21)."""

from openstars.engine.fog import derive_player_state
from openstars.engine.models import (
    Galaxy,
    GalaxyMetadata,
    GalaxyPlanet,
    GameMeta,
    GlobalState,
    PlanetState,
    Player,
    PlayerResearchState,
)
from openstars.engine.race.presets import default_race
from openstars.engine.research.costs import FIELDS, level_up_cost

_LEVELS_ZERO = {field: 0 for field in FIELDS}


def _player(
    levels: dict[str, int] | None = None,
    progress: dict[str, int] | None = None,
    current_field: str = "energy",
    allocation_percent: int = 15,
) -> Player:
    return Player(
        username="tim",
        name="Tim",
        race=default_race(),
        research_state=PlayerResearchState(
            levels=levels if levels is not None else dict(_LEVELS_ZERO),
            progress=progress if progress is not None else dict(_LEVELS_ZERO),
            current_field=current_field,
            next_field=None,
            allocation_percent=allocation_percent,
        ),
    )


def _galaxy(*planet_ids: str) -> Galaxy:
    return Galaxy(
        galaxy=GalaxyMetadata(name="Test", size="small", seed=42),
        planets=[GalaxyPlanet(id=pid, name=pid, x=0, y=0) for pid in planet_ids],
    )


def _state(
    player: Player,
    planets: list[PlanetState],
    planet_resources: dict[str, int] | None = None,
) -> GlobalState:
    return GlobalState(
        game=GameMeta(seed=42, turn=1, next_id=10),
        players=[player],
        planets=planets,
        fleets=[],
        planet_resources=planet_resources or {},
    )


def _planet(
    pid: str = "PL000001",
    *,
    owner: str | None = "tim",
    leftover_only: bool = False,
) -> PlanetState:
    return PlanetState(
        id=pid,
        owner=owner,
        contribute_only_leftover_to_research=leftover_only,
    )


def test_remaining_cost_per_non_capped_field():
    levels = {
        "energy": 2,
        "weapons": 0,
        "propulsion": 4,
        "construction": 1,
        "electronics": 3,
        "biotechnology": 0,
    }
    progress = {
        "energy": 40,
        "weapons": 0,
        "propulsion": 210,
        "construction": 0,
        "electronics": 95,
        "biotechnology": 0,
    }
    state = _state(_player(levels=levels, progress=progress), [])
    ps = derive_player_state(state, _galaxy(), "tim", designs=[])
    assert ps.research is not None
    total = sum(levels.values())  # 10
    for field in FIELDS:
        expected = max(0, level_up_cost(levels[field], total) - progress[field])
        assert ps.research.remaining_cost[field] == expected


def test_remaining_cost_zero_when_field_capped():
    levels = dict(_LEVELS_ZERO, propulsion=26)
    state = _state(_player(levels=levels, current_field="energy"), [])
    ps = derive_player_state(state, _galaxy(), "tim", designs=[])
    assert ps.research is not None
    assert ps.research.remaining_cost["propulsion"] == 0


def test_remaining_cost_clamped_at_zero_when_progress_exceeds_cost():
    progress = dict(_LEVELS_ZERO, energy=999_999)
    state = _state(_player(progress=progress), [])
    ps = derive_player_state(state, _galaxy(), "tim", designs=[])
    assert ps.research is not None
    assert ps.research.remaining_cost["energy"] == 0


def test_remaining_cost_includes_every_canonical_field():
    state = _state(_player(), [])
    ps = derive_player_state(state, _galaxy(), "tim", designs=[])
    assert ps.research is not None
    assert set(ps.research.remaining_cost.keys()) == set(FIELDS)


def test_reservable_resources_sums_owned_planets_with_toggle_off():
    planets = [
        _planet("PL000001"),
        _planet("PL000002"),
    ]
    state = _state(
        _player(),
        planets,
        planet_resources={"PL000001": 30, "PL000002": 70},
    )
    ps = derive_player_state(state, _galaxy("PL000001", "PL000002"), "tim", designs=[])
    assert ps.research is not None
    assert ps.research.reservable_resources_this_turn == 100


def test_reservable_resources_excludes_leftover_only_planets():
    planets = [
        _planet("PL000001"),
        _planet("PL000002", leftover_only=True),
    ]
    state = _state(
        _player(),
        planets,
        planet_resources={"PL000001": 30, "PL000002": 70},
    )
    ps = derive_player_state(state, _galaxy("PL000001", "PL000002"), "tim", designs=[])
    assert ps.research is not None
    assert ps.research.reservable_resources_this_turn == 30


def test_reservable_resources_zero_when_all_planets_leftover_only():
    planets = [_planet("PL000001", leftover_only=True)]
    state = _state(_player(), planets, planet_resources={"PL000001": 100})
    ps = derive_player_state(state, _galaxy("PL000001"), "tim", designs=[])
    assert ps.research is not None
    assert ps.research.reservable_resources_this_turn == 0


def test_reservable_resources_zero_when_player_owns_no_planets():
    state = _state(_player(), [_planet("PL000001", owner="sara")])
    ps = derive_player_state(state, _galaxy("PL000001"), "tim", designs=[])
    assert ps.research is not None
    assert ps.research.reservable_resources_this_turn == 0
