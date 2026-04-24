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
