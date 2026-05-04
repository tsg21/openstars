"""Tests for JOAT built-in scanner augmentation in fog-of-war derivation."""

import pytest

from openstars.engine.fog import _scanner_positions
from openstars.engine.galaxy import LIGHT_YEAR
from openstars.engine.models import (
    Cargo,
    Design,
    DesignCost,
    Fleet,
    FleetComposition,
    Galaxy,
    GalaxyMetadata,
    GlobalState,
    Minerals,
    Player,
    Position,
    Scanner,
    default_research_state,
)
from openstars.engine.race.presets import HUMANOID

_EMPTY_GALAXY = Galaxy(
    galaxy=GalaxyMetadata(name="Test", size="small", seed=1),
    planets=[],
)

_DESIGN_COST = DesignCost(
    resources=0,
    minerals=Minerals(),
)


def _joat_state(username: str, electronics: int) -> GlobalState:
    rs = default_research_state()
    rs.levels["electronics"] = electronics
    return GlobalState(
        game={"seed": 1, "turn": 1, "next_id": 1},
        players=[Player(username=username, name=username, race=HUMANOID, research_state=rs)],
        planets=[],
        fleets=[],
    )


def _non_joat_state(username: str) -> GlobalState:
    # Until non-JOAT PRTs are implemented, force a non-JOAT prt value directly.
    race = HUMANOID.model_copy(update={"prt": "SS"})  # "SS" is not JOAT
    rs = default_research_state()
    rs.levels["electronics"] = 3
    return GlobalState(
        game={"seed": 1, "turn": 1, "next_id": 1},
        players=[Player(username=username, name=username, race=race, research_state=rs)],
        planets=[],
        fleets=[],
    )


def _fleet(fleet_id: str, owner: str, design_id: str) -> Fleet:
    return Fleet(
        id=fleet_id,
        name="Test Fleet",
        owner=owner,
        position=Position(x=0, y=0),
        composition=[FleetComposition(design_id=design_id, count=1)],
        cargo=Cargo(),
        fuel=50,
        waypoints=[],
        repeat=False,
        bearing=None,
    )


def _design(design_id: str, owner: str, hull: str, normal_ly: int = 0, pen_ly: int = 0) -> Design:
    return Design(
        id=design_id,
        owner=owner,
        name=hull.title(),
        hull=hull,
        cost=_DESIGN_COST,
        components=[],
        fuel_capacity=50,
        cargo_capacity=0,
        mass=10,
        scanner=Scanner(normal=normal_ly, penetrating=pen_ly),
    )


def test_joat_scout_gets_builtin_scanner_at_electronics_3() -> None:
    state = _joat_state("tim", electronics=3)
    state = state.model_copy(
        update={"fleets": [_fleet("FL1", "tim", "D1")]},
        deep=True,
    )
    designs = [_design("D1", "tim", "scout")]

    result = _scanner_positions(state, "tim", designs, _EMPTY_GALAXY)

    assert len(result) == 1
    _x, _y, normal, pen = result[0]
    assert normal == 60 * LIGHT_YEAR
    assert pen == 30 * LIGHT_YEAR


def test_joat_scout_no_range_at_electronics_0() -> None:
    state = _joat_state("tim", electronics=0)
    state = state.model_copy(
        update={"fleets": [_fleet("FL1", "tim", "D1")]},
        deep=True,
    )
    designs = [_design("D1", "tim", "scout")]

    result = _scanner_positions(state, "tim", designs, _EMPTY_GALAXY)

    assert result == []


@pytest.mark.parametrize("hull", ["frigate", "destroyer"])
def test_joat_builtin_hull_gets_scanner(hull: str) -> None:
    state = _joat_state("tim", electronics=3)
    state = state.model_copy(
        update={"fleets": [_fleet("FL1", "tim", "D1")]},
        deep=True,
    )
    designs = [_design("D1", "tim", hull)]

    result = _scanner_positions(state, "tim", designs, _EMPTY_GALAXY)

    assert len(result) == 1
    _x, _y, normal, pen = result[0]
    assert normal == 60 * LIGHT_YEAR
    assert pen == 30 * LIGHT_YEAR


def test_non_joat_scout_gets_no_builtin_scanner() -> None:
    state = _non_joat_state("tim")
    state = state.model_copy(
        update={"fleets": [_fleet("FL1", "tim", "D1")]},
        deep=True,
    )
    designs = [_design("D1", "tim", "scout")]

    result = _scanner_positions(state, "tim", designs, _EMPTY_GALAXY)

    assert result == []


def test_joat_non_builtin_hull_unaffected() -> None:
    state = _joat_state("tim", electronics=3)
    state = state.model_copy(
        update={"fleets": [_fleet("FL1", "tim", "D1")]},
        deep=True,
    )
    designs = [_design("D1", "tim", "cruiser")]

    result = _scanner_positions(state, "tim", designs, _EMPTY_GALAXY)

    assert result == []


def test_joat_builtin_does_not_override_higher_component_scanner() -> None:
    state = _joat_state("tim", electronics=3)
    state = state.model_copy(
        update={"fleets": [_fleet("FL1", "tim", "D1")]},
        deep=True,
    )
    # Component scanner exceeds JOAT built-in (60 ly normal, 30 ly pen)
    designs = [_design("D1", "tim", "scout", normal_ly=100, pen_ly=50)]

    result = _scanner_positions(state, "tim", designs, _EMPTY_GALAXY)

    assert len(result) == 1
    _x, _y, normal, pen = result[0]
    assert normal == 100 * LIGHT_YEAR
    assert pen == 50 * LIGHT_YEAR
