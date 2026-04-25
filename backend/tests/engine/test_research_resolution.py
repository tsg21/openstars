from openstars.engine.models import PlayerResearchState
from openstars.engine.resolve_steps.research import apply_research_points

_DEF_LEVELS = {
    "energy": 0,
    "weapons": 0,
    "propulsion": 0,
    "construction": 0,
    "electronics": 0,
    "biotechnology": 0,
}


def _state() -> PlayerResearchState:
    return PlayerResearchState(
        levels=dict(_DEF_LEVELS),
        progress=dict(_DEF_LEVELS),
        current_field="energy",
        next_field=None,
        allocation_percent=15,
    )


def _state_with_next_field() -> PlayerResearchState:
    state = _state()
    state.next_field = "weapons"
    return state


def test_apply_research_points_basic_behaviour():
    state = _state()
    unchanged, events = apply_research_points(state, 0)
    assert unchanged == state
    assert events == []

    updated, events = apply_research_points(state, 49)
    assert updated.progress["energy"] == 49
    assert events == []

    updated, events = apply_research_points(state, 50)
    assert updated.levels["energy"] == 1
    assert updated.progress["energy"] == 0
    assert events == [("energy", 1)]


def test_apply_research_points_switches_to_next_field_after_level_up():
    state = _state_with_next_field()

    updated, events = apply_research_points(state, 60)

    assert updated.levels["energy"] == 1
    assert updated.progress["energy"] == 0
    assert updated.current_field == "weapons"
    assert updated.next_field is None
    assert updated.progress["weapons"] == 10
    assert events == [("energy", 1)]
