from types import SimpleNamespace

from openstars.engine.galaxy import LIGHT_YEAR
from openstars.engine.models import (
    Design,
    DesignCost,
    Fleet,
    FleetComposition,
    Minerals,
    Position,
    Scanner,
    Waypoint,
)
from openstars.engine.race.models import LRT
from openstars.engine.race.presets import default_race
from openstars.engine.resolve_steps.movement import (
    _effective_warp,
    _fuel_for_leg,
    _fuel_multiplier_x100,
    move_fleet,
)


def _race_with_lrts(*lrts: LRT):
    return default_race().model_copy(update={"lrts": frozenset(lrts)})


def _design(*, mass: int = 20, fuel_usage: list[int] | None = None) -> Design:
    return Design(
        id="DE1",
        owner="alice",
        name="Scout",
        hull="scout",
        components=[],
        mass=mass,
        fuel_usage=fuel_usage or [0, 25, 100, 100, 100, 100, 500, 800, 900, 1080],
        fuel_capacity=50,
        scanner=Scanner(normal=0),
        cargo_capacity=0,
        cost=DesignCost(resources=10, minerals=Minerals()),
    )


def _fleet(*, fuel: int = 50, waypoint: Waypoint | None = None) -> Fleet:
    return Fleet(
        id="FL1",
        name="Fleet 1",
        owner="alice",
        position=Position(x=0, y=0),
        composition=[FleetComposition(design_id="DE1", count=1)],
        fuel=fuel,
        waypoints=[] if waypoint is None else [waypoint],
    )


def _movement_ctx(*, design: Design, race=None):
    return SimpleNamespace(
        designs_by_id={design.id: design},
        race_by_username={} if race is None else {"alice": race},
        fleets_by_id={},
        planets_by_coord={},
        planets_by_id={},
        planet_names={},
    )


def test_fuel_multiplier_defaults_without_ife() -> None:
    assert _fuel_multiplier_x100(_race_with_lrts()) == 100
    assert _fuel_multiplier_x100(_race_with_lrts(LRT.TOTAL_TERRAFORMING)) == 100


def test_fuel_multiplier_uses_ife_discount() -> None:
    assert _fuel_multiplier_x100(_race_with_lrts(LRT.IMPROVED_FUEL_EFFICIENCY)) == 85


def test_fuel_for_leg_keeps_existing_value_without_multiplier() -> None:
    design = _design(mass=20)
    fleet = _fleet()

    assert _fuel_for_leg(fleet, {design.id: design}, warp=6, distance_light_years=10) == 10


def test_fuel_for_leg_applies_multiplier_per_ship() -> None:
    design = _design(mass=200)
    fleet = _fleet()
    non_ife = _fuel_for_leg(
        fleet,
        {design.id: design},
        warp=6,
        distance_light_years=10,
        fuel_multiplier_x100=100,
    )

    assert (
        _fuel_for_leg(
            fleet,
            {design.id: design},
            warp=6,
            distance_light_years=10,
            fuel_multiplier_x100=85,
        )
        == non_ife * 85 // 100
    )


def test_move_fleet_consumes_less_fuel_for_ife_owner() -> None:
    design = _design(mass=200)
    waypoint = Waypoint(x=10 * LIGHT_YEAR, y=0, warp=6)
    non_ife_fleet = _fleet(fuel=50, waypoint=waypoint)
    ife_fleet = _fleet(fuel=50, waypoint=waypoint)

    moved_non_ife, _events = move_fleet(
        _movement_ctx(design=design, race=_race_with_lrts()),
        non_ife_fleet,
    )
    moved_ife, _events = move_fleet(
        _movement_ctx(design=design, race=_race_with_lrts(LRT.IMPROVED_FUEL_EFFICIENCY)),
        ife_fleet,
    )

    assert moved_non_ife is not None
    assert moved_ife is not None
    non_ife_consumed = non_ife_fleet.fuel - moved_non_ife.fuel
    assert ife_fleet.fuel - moved_ife.fuel == non_ife_consumed * 85 // 100


def test_effective_warp_uses_ife_discount_for_auto_warp_down() -> None:
    design = _design(mass=100, fuel_usage=[0, 0, 0, 8, 10, 20, 30, 40, 50, 60])
    waypoint = Waypoint(x=10 * LIGHT_YEAR, y=0, warp=5)
    fleet = _fleet(fuel=4, waypoint=waypoint)

    assert _effective_warp(fleet, waypoint, 10, {design.id: design}) == (5, 4)
    assert _effective_warp(
        fleet,
        waypoint,
        10,
        {design.id: design},
        fuel_multiplier_x100=85,
    ) == (5, 5)
