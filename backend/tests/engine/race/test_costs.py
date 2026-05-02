import pytest

from openstars.engine.race.costs import (
    POINTS_BUDGET,
    RaceValidationError,
    economy_cost,
    growth_cost,
    hab_factor_cost,
    research_cost,
    validate_race,
)
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
from openstars.engine.race.presets import HUMANOID, default_race
from openstars.engine.research.costs import FIELDS


def _race(**overrides: object) -> Race:
    values = default_race().model_dump()
    values.update(overrides)
    return Race(**values)


def test_humanoid_validates_as_zero_cost_reference() -> None:
    breakdown = validate_race(HUMANOID)

    assert breakdown.total == 0
    assert breakdown.points_left == POINTS_BUDGET


def test_habitability_factor_costs_hit_baseline_and_extremes() -> None:
    assert hab_factor_cost(False, 15, 85) == pytest.approx(0, abs=1)
    assert hab_factor_cost(True, 15, 85) == pytest.approx(75, abs=1)
    assert hab_factor_cost(False, 50, 50) < 0


def test_growth_cost_has_cliff_at_twenty_percent() -> None:
    assert growth_cost(15) == 0
    assert growth_cost(20) - growth_cost(19) > growth_cost(19) - growth_cost(18)


def test_economy_cost_reproduces_colonist_efficiency_cliff() -> None:
    default = economy_cost(RaceEconomy())
    stronger = economy_cost(RaceEconomy(colonists_per_resource=900))

    assert stronger - default == pytest.approx(200, abs=1)


def test_economy_cost_charges_for_germanium_saving_factories() -> None:
    default = economy_cost(RaceEconomy())
    g_box = economy_cost(RaceEconomy(factories_save_germanium=True))

    assert g_box - default == pytest.approx(58, abs=1)


def test_research_cost_profiles_use_fixed_per_field_values() -> None:
    cheap = RaceResearch(field_profile={field: ResearchCostProfile.CHEAP for field in FIELDS})
    expensive = RaceResearch(
        field_profile={field: ResearchCostProfile.EXPENSIVE for field in FIELDS}
    )

    assert research_cost(cheap) == 175 * 6
    assert research_cost(expensive) == -150 * 6


def test_validate_race_rejects_overspent_race() -> None:
    race = _race(
        habitability=RaceHabitability(
            gravity=RaceHabitabilityFactor(immune=True),
            temperature=RaceHabitabilityFactor(immune=True),
            radiation=RaceHabitabilityFactor(immune=True),
        ),
        max_growth_rate=20,
        economy=RaceEconomy(
            colonists_per_resource=700,
            factory_output_per_10=15,
            factory_cost_resources=5,
            factories_per_10k_colonists=25,
            factories_save_germanium=True,
            mine_output_per_10=25,
            mine_cost_resources=2,
            mines_per_10k_colonists=25,
            ar_resource_divisor=5,
        ),
        research=RaceResearch(
            field_profile={field: ResearchCostProfile.CHEAP for field in FIELDS},
            start_at_tech_3=True,
        ),
    )

    with pytest.raises(RaceValidationError) as error:
        validate_race(race)

    assert error.value.code == "RACE_OVERSPENT"


def test_validate_race_rejects_unavailable_prt() -> None:
    race = _race(prt=PRT.HYPER_EXPANSION)

    with pytest.raises(RaceValidationError) as error:
        validate_race(race)

    assert error.value.code == "RACE_PRT_NOT_AVAILABLE"


def test_validate_race_rejects_unavailable_lrt() -> None:
    race = _race(lrts={LRT.IMPROVED_FUEL_EFFICIENCY})

    with pytest.raises(RaceValidationError) as error:
        validate_race(race)

    assert error.value.code == "RACE_LRT_NOT_AVAILABLE"


def test_validate_race_rejects_unavailable_leftover_bonus() -> None:
    race = _race(leftover_bonus=LeftoverBonus(kind="mines", points=10))

    with pytest.raises(RaceValidationError) as error:
        validate_race(race)

    assert error.value.code == "RACE_BONUS_NOT_AVAILABLE"
