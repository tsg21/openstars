"""Race advantage-point cost tables and validation."""

from pydantic import BaseModel

from openstars.engine.race.models import (
    LRT,
    PRT,
    LeftoverBonus,
    LeftoverBonusKind,
    Race,
    RaceEconomy,
    RaceHabitability,
    RaceResearch,
    ResearchCostProfile,
)

POINTS_BUDGET = 1650

prt_cost: dict[PRT, int] = {
    PRT.HYPER_EXPANSION: 63,
    PRT.SUPER_STEALTH: 81,
    PRT.WAR_MONGER: 65,
    PRT.CLAIM_ADJUSTER: 53,
    PRT.INNER_STRENGTH: 17,
    PRT.SPACE_DEMOLITION: 0,
    PRT.PACKET_PHYSICS: 90,
    PRT.INTERSTELLAR_TRAVELLER: 100,
    PRT.ALTERNATE_REALITY: 80,
    PRT.JACK_OF_ALL_TRADES: 28,
}

lrt_cost: dict[LRT, int] = {
    LRT.IMPROVED_FUEL_EFFICIENCY: 78,
    LRT.TOTAL_TERRAFORMING: 140,
    LRT.ADVANCED_REMOTE_MINING: 53,
    LRT.IMPROVED_STARBASES: 67,
    LRT.GENERALIZED_RESEARCH: -13,
    LRT.ULTIMATE_RECYCLING: 80,
    LRT.MINERAL_ALCHEMY: 51,
    LRT.NO_RAMSCOOP_ENGINES: -53,
    LRT.CHEAP_ENGINES: 80,
    LRT.ONLY_BASIC_REMOTE_MINING: -85,
    LRT.NO_ADVANCED_SCANNERS: -95,
    LRT.LOW_STARTING_POPULATION: -60,
    LRT.BLEEDING_EDGE_TECHNOLOGY: -23,
    LRT.REGENERATING_SHIELDS: -10,
}

accelerator_cost = 60


def _interpolate(value: float, points: tuple[tuple[float, int], ...]) -> int:
    if value <= points[0][0]:
        return points[0][1]
    if value >= points[-1][0]:
        return points[-1][1]

    for (left_value, left_cost), (right_value, right_cost) in zip(points, points[1:], strict=False):
        if left_value <= value <= right_value:
            span = right_value - left_value
            ratio = (value - left_value) / span
            return round(left_cost + ((right_cost - left_cost) * ratio))

    raise ValueError("interpolation points are not ordered")


def hab_factor_cost(immune: bool, low: int, high: int) -> int:
    """Return the cost for one habitability factor.

    Width is the main price dial: the JOAT baseline is a centred 70-click band,
    while a single-value band returns roughly 60 points. Off-centre ranges past
    15 clicks return points at a diminishing rate.
    """
    if immune:
        return 75

    width = high - low
    centre = (low + high) / 2
    offset = abs(centre - 50)

    width_cost = _interpolate(
        width,
        (
            (0, -60),
            (35, -30),
            (70, 0),
            (100, -15),
        ),
    )
    if offset <= 15:
        offset_cost = 0
    else:
        offset_cost = _interpolate(offset, ((15, 0), (35, -20), (50, -30)))

    return width_cost + offset_cost


def hab_cost(hab: RaceHabitability) -> int:
    return sum(
        hab_factor_cost(factor.immune, factor.range[0], factor.range[1])
        for factor in (hab.gravity, hab.temperature, hab.radiation)
    )


def growth_cost(rate: int) -> int:
    return _interpolate(
        rate,
        (
            (1, -420),
            (5, -280),
            (10, -120),
            (15, 0),
            (16, 20),
            (17, 45),
            (18, 75),
            (19, 135),  # anchor: growth 18->19 costs about 60.
            (20, 260),  # anchor: growth 19->20 costs about 125.
        ),
    )


def economy_cost(eco: RaceEconomy) -> int:
    total = 0
    total += _interpolate(
        eco.colonists_per_resource,
        (
            (700, 600),
            (800, 400),
            (900, 200),  # anchor: 1000->900 costs about 200.
            (1000, 0),
            (1100, -40),  # anchor: 1000->1100 returns about 40.
            (1500, -120),
            (2500, -260),
        ),
    )
    total += _interpolate(
        eco.factory_output_per_10,
        (
            (5, -150),
            (10, 0),
            (11, 43),  # anchor: 10->11 costs about 43.
            (12, 83),  # anchor: 11->12 costs about 40.
            (13, 145),  # anchor: 12->13 costs about 62.
            (15, 270),
        ),
    )
    total += _interpolate(
        eco.factory_cost_resources,
        (
            (5, 240),
            (8, 120),
            (9, 60),
            (10, 0),
            (15, -50),
            (25, -140),
        ),
    )
    total += _interpolate(
        eco.factories_per_10k_colonists,
        (
            (5, -80),
            (10, 0),
            (15, 60),
            (25, 180),
        ),
    )
    if eco.factories_save_germanium:
        total += 58

    total += _interpolate(
        eco.mine_output_per_10,
        (
            (5, -80),
            (10, 0),
            (15, 45),
            (25, 135),
        ),
    )
    total += _interpolate(
        eco.mine_cost_resources,
        (
            (2, 156),  # anchor: 3->2 costs about 134.
            (3, 22),
            (4, 0),  # anchor: 4->3 costs about 22.
            (5, 0),
            (10, -50),
            (15, -100),
        ),
    )
    total += _interpolate(
        eco.mines_per_10k_colonists,
        (
            (5, -50),
            (10, 0),
            (15, 35),
            (25, 105),
        ),
    )
    total += _interpolate(
        eco.ar_resource_divisor,
        (
            (5, 120),
            (10, 0),
            (15, -40),
            (25, -110),
        ),
    )
    return total


def research_cost(research: RaceResearch) -> int:
    profile_cost = {
        ResearchCostProfile.CHEAP: 175,
        ResearchCostProfile.STANDARD: 0,
        ResearchCostProfile.EXPENSIVE: -150,
    }
    total = sum(profile_cost[profile] for profile in research.field_profile.values())
    if research.start_at_tech_3:
        total += accelerator_cost
    return total


def leftover_bonus_cost(bonus: LeftoverBonus | None) -> int:
    return bonus.points if bonus is not None else 0


class RaceCostBreakdown(BaseModel):
    prt: int
    lrts: int
    habitability: int
    growth: int
    economy: int
    research: int
    leftover: int
    total: int
    points_left: int


def race_cost_breakdown(race: Race) -> RaceCostBreakdown:
    prt = prt_cost[race.prt]
    lrts = sum(lrt_cost[lrt] for lrt in race.lrts)
    habitability = hab_cost(race.habitability)
    growth = growth_cost(race.max_growth_rate)
    economy = economy_cost(race.economy)
    research = research_cost(race.research)
    leftover = leftover_bonus_cost(race.leftover_bonus)
    total = prt + lrts + habitability + growth + economy + research
    points_left = POINTS_BUDGET - total - leftover
    return RaceCostBreakdown(
        prt=prt,
        lrts=lrts,
        habitability=habitability,
        growth=growth,
        economy=economy,
        research=research,
        leftover=leftover,
        total=total,
        points_left=points_left,
    )


class RaceValidationError(Exception):
    def __init__(self, code: str, detail: str) -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}")


def _validate_leftover_bonus(race: Race, breakdown: RaceCostBreakdown) -> None:
    if race.leftover_bonus is None:
        return
    if race.prt == PRT.ALTERNATE_REALITY and race.leftover_bonus.kind in {
        LeftoverBonusKind.MINES,
        LeftoverBonusKind.FACTORIES,
    }:
        raise RaceValidationError(
            "RACE_INVALID_BONUS",
            "alternate reality races cannot spend leftover points on mines or factories",
        )
    if race.leftover_bonus.points > breakdown.points_left + race.leftover_bonus.points:
        raise RaceValidationError(
            "RACE_INVALID_BONUS",
            "leftover bonus points cannot exceed available points",
        )


def validate_race(race: Race) -> RaceCostBreakdown:
    breakdown = race_cost_breakdown(race)
    if breakdown.points_left < 0:
        raise RaceValidationError("RACE_OVERSPENT", "race spends more points than available")
    if race.prt != PRT.JACK_OF_ALL_TRADES:
        raise RaceValidationError(
            "RACE_PRT_NOT_AVAILABLE",
            "only Jack of All Trades is available in Phase A",
        )
    if race.lrts:
        raise RaceValidationError(
            "RACE_LRT_NOT_AVAILABLE",
            "lesser racial traits are not available in Phase A",
        )
    if race.leftover_bonus is not None:
        _validate_leftover_bonus(race, breakdown)
        raise RaceValidationError(
            "RACE_BONUS_NOT_AVAILABLE",
            "leftover bonuses are not available in Phase A",
        )
    return breakdown
