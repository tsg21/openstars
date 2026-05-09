from pathlib import Path

import pytest

from openstars.engine.component_catalogue import load_component_catalogue
from openstars.engine.designs import DesignValidationError, build_design
from openstars.engine.race.models import LRT
from openstars.engine.race.presets import default_race
from openstars.engine.research.costs import FIELDS


def _catalogue():
    base_dir = Path(__file__).resolve().parents[2] / "openstars" / "data"
    return load_component_catalogue(base_dir)


def _race(*lrts: LRT):
    return default_race().model_copy(update={"lrts": frozenset(lrts)})


def _levels(level: int = 26) -> dict[str, int]:
    return {field: level for field in FIELDS}


def test_fuel_mizer_requires_ife() -> None:
    with pytest.raises(DesignValidationError) as error:
        build_design(
            design_id="DE1",
            owner="alice",
            name="Fuel Mizer Scout",
            hull_id="scout",
            components=[
                {"slot_number": 1, "component_id": "fuel_mizer", "component_count": 1},
                {"slot_number": 2, "component_id": "bat_scanner", "component_count": 1},
            ],
            catalogue=_catalogue(),
            player_levels=_levels(),
            race=_race(),
        )

    assert error.value.code == "RACE_RESTRICTED"


def test_fuel_mizer_builds_for_ife() -> None:
    design = build_design(
        design_id="DE1",
        owner="alice",
        name="Fuel Mizer Scout",
        hull_id="scout",
        components=[
            {"slot_number": 1, "component_id": "fuel_mizer", "component_count": 1},
            {"slot_number": 2, "component_id": "bat_scanner", "component_count": 1},
        ],
        catalogue=_catalogue(),
        player_levels=_levels(),
        race=_race(LRT.IMPROVED_FUEL_EFFICIENCY),
    )

    assert design.fuel_usage[4] == 35


def test_galaxy_scoop_builds_for_ife() -> None:
    design = build_design(
        design_id="DE1",
        owner="alice",
        name="Galaxy Scout",
        hull_id="scout",
        components=[
            {"slot_number": 1, "component_id": "galaxy_scoop", "component_count": 1},
            {"slot_number": 2, "component_id": "bat_scanner", "component_count": 1},
        ],
        catalogue=_catalogue(),
        player_levels=_levels(),
        race=_race(LRT.IMPROVED_FUEL_EFFICIENCY),
    )

    assert design.fuel_usage[8] == 60
