import pytest
from pydantic import ValidationError

from openstars.engine.race.models import (
    LRT,
    PRT,
    LeftoverBonus,
    Race,
    RaceEconomy,
    RaceHabitability,
    RaceHabitabilityFactor,
    RaceResearch,
    ResearchCostProfile,
)
from openstars.engine.research.costs import FIELDS


def default_habitability() -> RaceHabitability:
    return RaceHabitability(
        gravity=RaceHabitabilityFactor(),
        temperature=RaceHabitabilityFactor(),
        radiation=RaceHabitabilityFactor(),
    )


def test_minimal_joat_race_with_default_habitability_validates() -> None:
    race = Race(
        name="Humanoid",
        plural_name="Humanoids",
        emblem=0,
        prt=PRT.JACK_OF_ALL_TRADES,
        habitability=default_habitability(),
    )

    assert race.prt == PRT.JACK_OF_ALL_TRADES
    assert race.model_dump(mode="json")["prt"] == "JOAT"
    assert race.lrts == frozenset()
    assert race.max_growth_rate == 15
    assert race.economy == RaceEconomy()
    assert race.research == RaceResearch()


def test_race_trait_enums_use_full_member_names_and_short_values() -> None:
    assert PRT.JACK_OF_ALL_TRADES.value == "JOAT"
    assert PRT.HYPER_EXPANSION.value == "HE"
    assert LRT.IMPROVED_FUEL_EFFICIENCY.value == "IFE"
    assert LRT.NO_RAMSCOOP_ENGINES.value == "NRSE"


def test_habitability_factor_rejects_range_out_of_order() -> None:
    with pytest.raises(ValidationError):
        RaceHabitabilityFactor(range=(60, 40))


def test_habitability_factor_rejects_low_below_zero() -> None:
    with pytest.raises(ValidationError):
        RaceHabitabilityFactor(range=(-5, 50))


def test_race_economy_rejects_colonists_per_resource_below_minimum() -> None:
    with pytest.raises(ValidationError):
        RaceEconomy(colonists_per_resource=600)


def test_race_research_default_factory_produces_standard_for_all_fields() -> None:
    research = RaceResearch()

    assert research.field_profile == {field: ResearchCostProfile.STANDARD for field in FIELDS}


def test_race_research_rejects_missing_fields() -> None:
    with pytest.raises(ValidationError):
        RaceResearch(field_profile={"energy": "cheap"})


def test_leftover_bonus_rejects_points_above_maximum() -> None:
    with pytest.raises(ValidationError):
        LeftoverBonus(kind="mines", points=51)
