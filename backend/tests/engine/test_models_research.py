import pytest
from pydantic import ValidationError

from openstars.engine.models import PlanetState, Player, PlayerResearchState

_DEF_LEVELS = {
    "energy": 0,
    "weapons": 0,
    "propulsion": 0,
    "construction": 0,
    "electronics": 0,
    "biotechnology": 0,
}


def test_player_research_state_valid():
    state = PlayerResearchState(
        levels=_DEF_LEVELS,
        progress=_DEF_LEVELS,
        current_field="energy",
        next_field=None,
        allocation_percent=15,
    )
    assert state.current_field == "energy"


def test_player_research_state_validation_errors():
    with pytest.raises(ValidationError):
        PlayerResearchState(
            levels={k: v for k, v in _DEF_LEVELS.items() if k != "energy"},
            progress=_DEF_LEVELS,
            current_field="energy",
            allocation_percent=15,
        )
    with pytest.raises(ValidationError):
        PlayerResearchState(
            levels=_DEF_LEVELS,
            progress=_DEF_LEVELS,
            current_field="nonsense",
            allocation_percent=15,
        )
    with pytest.raises(ValidationError):
        PlayerResearchState(
            levels=_DEF_LEVELS,
            progress=_DEF_LEVELS,
            current_field="energy",
            allocation_percent=101,
        )


def test_player_and_planet_defaults():
    player = Player(username="tim", name="Tim")
    assert player.research_state.current_field == "energy"
    planet = PlanetState(id="PL1")
    assert planet.contribute_only_leftover_to_research is False
