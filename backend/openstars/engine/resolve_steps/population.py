"""Population growth and death simulation (PRD 14).

Each turn, planet populations grow or die based on habitability — the
compatibility between a planet's environment and the owner's race parameters.
"""

from math import floor

from openstars.engine.models import GameEvent, Habitability, PlanetState

# --- JOAT race defaults (hardcoded until race design is implemented) ---

GRAVITY_RANGE: tuple[int, int] = (15, 85)
TEMPERATURE_RANGE: tuple[int, int] = (15, 85)
RADIATION_RANGE: tuple[int, int] = (15, 85)
MAX_GROWTH_RATE: float = 0.15
BASE_MAX_POPULATION: int = 1_000_000

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


def calculate_hab_value(hab: Habitability) -> int:
    """Return the combined habitability score for a planet, range [-45, +100]."""
    g_low, g_high = GRAVITY_RANGE
    t_low, t_high = TEMPERATURE_RANGE
    r_low, r_high = RADIATION_RANGE

    total = (
        factor_contribution(hab.gravity, g_low, g_high)
        + factor_contribution(hab.temperature, t_low, t_high)
        + factor_contribution(hab.radiation, r_low, r_high)
    )
    return round(total)


def max_population(hab: Habitability) -> int:
    """Return the maximum population this planet can support.

    Returns 0 for uninhabitable planets (hab_value <= 0).
    Planets with hab_value in [1, 4] are treated as 5% (50,000 people).
    """
    hv = calculate_hab_value(hab)
    if hv <= 0:
        return 0
    return BASE_MAX_POPULATION * max(hv, 5) // 100


def population_growth(population: int, hab: Habitability) -> int:
    """Return the population increase this turn (positive integer).

    Uses a logistic model: full exponential rate below 25% capacity,
    linear slowdown from 25% to 100%, zero at max_population.
    """
    hv = calculate_hab_value(hab)
    max_pop = max_population(hab)
    if hv <= 0 or population <= 0 or max_pop == 0:
        return 0

    growth_rate = (hv / 100) * MAX_GROWTH_RATE

    if population <= 0.25 * max_pop:
        return floor(population * growth_rate)

    remaining = (max_pop - population) / (0.75 * max_pop)
    return floor(population * growth_rate * max(remaining, 0.0))


def population_death(population: int, hab: Habitability) -> int:
    """Return the number of colonists killed by hostile environment this turn.

    Death rate = |hab_value| / 10 percent per year.
    e.g. hab_value -10 → 1% death rate.

    A minimum of 1 death is enforced on any hostile planet with living colonists,
    ensuring the population eventually reaches zero rather than stalling at a
    fractional-death floor.
    """
    hv = calculate_hab_value(hab)
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


def grow_population(
    planets_by_id: dict[str, PlanetState],
    planet_names: dict[str, str],
    turn: int,
) -> tuple[dict[str, list[GameEvent]], dict[str, int]]:
    """Run population growth/death for all owned planets.

    Mutates planets_by_id in-place.
    Returns (owner_events, pop_growth_by_planet_id).
    pop_growth values are signed (positive = growth, negative = shrinkage).
    """
    owner_events: dict[str, list[GameEvent]] = {}
    pop_growth_map: dict[str, int] = {}

    for planet_id in sorted(planets_by_id.keys()):
        planet = planets_by_id[planet_id]
        if planet.owner is None:
            continue

        old_pop = planet.population
        hab = planet.habitability
        max_pop = max_population(hab)
        hv = calculate_hab_value(hab)

        new_pop = old_pop

        if hv > 0:
            # Grow then cap at max_population
            growth = population_growth(old_pop, hab)
            new_pop = min(old_pop + growth, max_pop)
        elif hv < 0:
            # Hostile environment — colonists die
            deaths = population_death(old_pop, hab)
            new_pop = max(old_pop - deaths, 0)
            if deaths > 0:
                owner_events.setdefault(planet.owner, []).append(
                    GameEvent(
                        type="colonists_died",
                        turn=turn,
                        planet_id=planet.id,
                        planet_name=planet_names.get(planet.id),
                        deaths=deaths,
                        cause="hostile_environment",
                    )
                )

        # Overcrowding deaths (can happen after growth if pop exceeded max)
        od = overcrowding_deaths(new_pop, max_pop)
        if od > 0:
            new_pop = max(new_pop - od, 0)
            owner_events.setdefault(planet.owner, []).append(
                GameEvent(
                    type="colonists_died",
                    turn=turn,
                    planet_id=planet.id,
                    planet_name=planet_names.get(planet.id),
                    deaths=od,
                    cause="overcrowding",
                )
            )

        if new_pop == 0 and old_pop > 0:
            # Planet abandoned
            owner_events.setdefault(planet.owner, []).append(
                GameEvent(
                    type="planet_abandoned",
                    turn=turn,
                    planet_id=planet.id,
                    planet_name=planet_names.get(planet.id),
                )
            )
            planets_by_id[planet_id] = planet.model_copy(update={"population": 0, "owner": None})
        else:
            planets_by_id[planet_id] = planet.model_copy(update={"population": new_pop})

        pop_growth_map[planet_id] = new_pop - old_pop

    return owner_events, pop_growth_map
