"""Population growth and death simulation (PRD 14).


Each turn, planet populations grow or die based on habitability — the
compatibility between a planet's environment and the owner's race parameters.
"""

import logging
from math import floor

from openstars.engine.models import GameEvent, Habitability
from openstars.engine.race.models import PRT, RaceHabitability, RaceHabitabilityFactor
from openstars.engine.turn_context import TurnContext

log = logging.getLogger(__name__)

BASE_MAX_POPULATION: int = 1_000_000
_POPULATION_CAP_FACTOR: dict[PRT, float] = {
    PRT.HYPER_EXPANSION: 0.5,
    PRT.JACK_OF_ALL_TRADES: 1.2,
    PRT.ALTERNATE_REALITY: 0.0,
}
_GROWTH_MULTIPLIER: dict[PRT, float] = {PRT.HYPER_EXPANSION: 2.0}


def population_cap_factor(prt: PRT) -> float:
    return _POPULATION_CAP_FACTOR.get(prt, 1.0)


def growth_multiplier(prt: PRT) -> float:
    return _GROWTH_MULTIPLIER.get(prt, 1.0)


# --- Pure calculation functions ---


def factor_contribution(v: int, low: int, high: int) -> float:
    """Return the habitability contribution of one environmental factor.

    Returns a value in:
      [0.0, 33.333] when v is within [low, high]
      [-15.0, 0.0)  when v is outside [low, high]
    """
    ideal = (low + high) / 2
    half_width = (high - low) / 2
    if half_width == 0:
        return 33.333 if v == ideal else -15.0

    if low <= v <= high:
        return (1.0 - abs(v - ideal) / half_width) * 33.333
    elif v < low:
        distance = low - v
        return -(distance / max(low, 1)) * 15.0
    else:  # v > high
        distance = v - high
        return -(distance / max(100 - high, 1)) * 15.0


def _factor_value(value: int, factor: RaceHabitabilityFactor) -> float:
    if factor.immune:
        return 33.333
    low, high = factor.range
    return factor_contribution(value, low, high)


def calculate_hab_value(hab: Habitability, race_hab: RaceHabitability) -> int:
    """Return the combined habitability score for a planet, range [-45, +100]."""
    total = (
        _factor_value(hab.gravity, race_hab.gravity)
        + _factor_value(hab.temperature, race_hab.temperature)
        + _factor_value(hab.radiation, race_hab.radiation)
    )
    return round(total)


def max_population(
    hab: Habitability, race_hab: RaceHabitability, *, cap_factor: float = 1.0
) -> int:
    """Return the maximum population this planet can support.

    Returns 0 for uninhabitable planets (hab_value <= 0).
    Planets with hab_value in [1, 4] are treated as 5% (50,000 people).
    """
    hv = calculate_hab_value(hab, race_hab)
    if hv <= 0:
        return 0
    return floor(BASE_MAX_POPULATION * max(hv, 5) / 100 * cap_factor)


def population_growth(
    population: int,
    hab: Habitability,
    race_hab: RaceHabitability,
    max_growth_rate: int,
    *,
    growth_multiplier: float = 1.0,
) -> int:
    """Return the population increase this turn (positive integer).

    Uses a logistic model: full exponential rate below 25% capacity,
    linear slowdown from 25% to 100%, zero at max_population.
    """
    hv = calculate_hab_value(hab, race_hab)
    max_pop = max_population(hab, race_hab)
    if hv <= 0 or population <= 0 or max_pop == 0:
        return 0

    growth_rate = (hv / 100) * (max_growth_rate / 100) * growth_multiplier

    if population <= 0.25 * max_pop:
        return floor(population * growth_rate)

    remaining = (max_pop - population) / (0.75 * max_pop)
    return floor(population * growth_rate * max(remaining, 0.0))


def population_death(population: int, hab: Habitability, race_hab: RaceHabitability) -> int:
    """Return the number of colonists killed by hostile environment this turn.

    Death rate = |hab_value| / 10 percent per year.
    e.g. hab_value -10 → 1% death rate.

    A minimum of 1 death is enforced on any hostile planet with living colonists,
    ensuring the population eventually reaches zero rather than stalling at a
    fractional-death floor.
    """
    hv = calculate_hab_value(hab, race_hab)
    if hv >= 0 or population <= 0:
        return 0
    death_rate = abs(hv) / 10 / 100
    return max(floor(population * death_rate), 1)


def overcrowding_deaths(population: int, max_pop: int) -> int:
    """Return deaths caused by overcrowding (population exceeding max_pop).

    Death rate scales from 0% at 100% capacity to a maximum of 12% at 400%+.
    """
    if max_pop == 0 or population <= max_pop:
        return 0
    ratio = population / max_pop
    if ratio <= 4.0:
        rate = (ratio - 1.0) / 3.0 * 0.12
    else:
        rate = 0.12
    return floor(population * rate)


# --- Step function ---


def grow_population(ctx: TurnContext) -> None:
    """Run population growth/death for all owned planets.

    Mutates ctx.planets_by_id in-place.
    Sets ctx.pop_growth and accumulates events into ctx.owner_events.
    pop_growth values are signed (positive = growth, negative = shrinkage).
    """
    for planet_id in sorted(ctx.planets_by_id.keys()):
        planet = ctx.planets_by_id[planet_id]
        if planet.owner is None:
            continue

        old_pop = planet.population
        hab = planet.habitability
        race = ctx.race_by_username[planet.owner]
        race_hab = race.habitability
        cap_factor = population_cap_factor(race.prt)
        growth_factor = growth_multiplier(race.prt)
        max_pop = max_population(hab, race_hab, cap_factor=cap_factor)
        hv = calculate_hab_value(hab, race_hab)

        new_pop = old_pop

        if hv > 0:
            # Grow then cap at max_population
            growth = population_growth(
                old_pop,
                hab,
                race_hab,
                race.max_growth_rate,
                growth_multiplier=growth_factor,
            )
            new_pop = min(old_pop + growth, max_pop)
        elif hv < 0:
            # Hostile environment — colonists die
            deaths = population_death(old_pop, hab, race_hab)
            new_pop = max(old_pop - deaths, 0)
            if deaths > 0:
                ctx.append_event(
                    GameEvent(
                        owner=planet.owner,
                        source_id=planet.id,
                        code="population.colonists_died",
                        values=[
                            deaths,
                            "hostile_environment",
                            ctx.planet_names.get(planet.id, planet.id),
                        ],
                    )
                )

        # Overcrowding deaths (can happen after growth if pop exceeded max)
        od = overcrowding_deaths(new_pop, max_pop)
        if od > 0:
            new_pop = max(new_pop - od, 0)
            ctx.append_event(
                GameEvent(
                    owner=planet.owner,
                    source_id=planet.id,
                    code="population.colonists_died",
                    values=[
                        od,
                        "overcrowding",
                        ctx.planet_names.get(planet.id, planet.id),
                    ],
                )
            )

        if new_pop == 0 and old_pop > 0:
            # Planet abandoned
            ctx.append_event(
                GameEvent(
                    owner=planet.owner,
                    source_id=planet.id,
                    code="population.planet_abandoned",
                    values=[ctx.planet_names.get(planet.id, planet.id)],
                )
            )
            ctx.planets_by_id[planet_id] = planet.model_copy(
                update={"population": 0, "owner": None}
            )
            log.debug("population: planet=%s owner=%s abandoned (pop 0)", planet.id, planet.owner)
        else:
            ctx.planets_by_id[planet_id] = planet.model_copy(update={"population": new_pop})
            log.debug(
                "population: planet=%s owner=%s %d->%d (%+d)",
                planet.id,
                planet.owner,
                old_pop,
                new_pop,
                new_pop - old_pop,
            )

        ctx.pop_growth[planet_id] = new_pop - old_pop
