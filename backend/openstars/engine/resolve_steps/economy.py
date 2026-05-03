"""Pure economy calculation functions (PRD 12)."""

from math import floor

from openstars.engine.models import Minerals, PlanetState
from openstars.engine.race.models import RaceEconomy

# --- Pure calculation functions ---


def mines_operated(mines: int, population: int, race_economy: RaceEconomy) -> int:
    """Return the number of mines actually operating given population."""
    return min(mines, floor(population / 10000) * race_economy.mines_per_10k_colonists)


def factories_operated(factories: int, population: int, race_economy: RaceEconomy) -> int:
    """Return the number of factories actually operating given population."""
    return min(factories, floor(population / 10000) * race_economy.factories_per_10k_colonists)


def mine_minerals(mines_op: int, concentrations: Minerals, race_economy: RaceEconomy) -> Minerals:
    """Calculate minerals mined this turn given operating mines and concentrations."""
    mine_rate = race_economy.mine_output_per_10 / 10
    return Minerals(
        ironium=floor(mines_op * mine_rate * concentrations.ironium / 100),
        boranium=floor(mines_op * mine_rate * concentrations.boranium / 100),
        germanium=floor(mines_op * mine_rate * concentrations.germanium / 100),
    )


def deplete_concentrations(
    planet: PlanetState, mines_op: int, min_conc: int
) -> tuple[Minerals, Minerals]:
    """Apply concentration depletion for one turn.

    Returns updated (concentrations, mine_years).
    """
    conc_i = planet.concentrations.ironium
    conc_b = planet.concentrations.boranium
    conc_g = planet.concentrations.germanium
    my_i = planet.mine_years.ironium + mines_op
    my_b = planet.mine_years.boranium + mines_op
    my_g = planet.mine_years.germanium + mines_op

    def _deplete(conc: int, mine_years: int) -> tuple[int, int]:
        threshold = 12500 // conc
        while mine_years >= threshold and conc > min_conc:
            conc -= 1
            mine_years -= threshold
            threshold = 12500 // conc
        return conc, mine_years

    conc_i, my_i = _deplete(conc_i, my_i)
    conc_b, my_b = _deplete(conc_b, my_b)
    conc_g, my_g = _deplete(conc_g, my_g)

    return (
        Minerals(ironium=conc_i, boranium=conc_b, germanium=conc_g),
        Minerals(ironium=my_i, boranium=my_b, germanium=my_g),
    )


def calculate_resources(
    population: int,
    factories_op: int,
    race_economy: RaceEconomy,
) -> tuple[int, int, int]:
    """Return (pop_resources, factory_resources, total_resources)."""
    pop_resources = floor(population / race_economy.colonists_per_resource)
    factory_resources = floor(factories_op * (race_economy.factory_output_per_10 / 10))
    return pop_resources, factory_resources, pop_resources + factory_resources


def mining_rate(mines_op: int, concentrations: Minerals, race_economy: RaceEconomy) -> Minerals:
    """Convenience alias for mine_minerals — used for player state display."""
    return mine_minerals(mines_op, concentrations, race_economy)
