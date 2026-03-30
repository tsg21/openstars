"""Pure economy calculation functions (PRD 12)."""

from math import floor

from openstars.engine.models import Minerals, PlanetState

# --- Race economy defaults (JOAT) ---

COLONISTS_PER_RESOURCE = 1000
FACTORY_RATE = 1.0
FACTORY_COST_RESOURCES = 10
FACTORY_COST_GERMANIUM = 4
FACTORIES_PER_10K = 10
MINE_RATE = 1.0
MINE_COST_RESOURCES = 5
MINES_PER_10K = 10


# --- Pure calculation functions ---


def mines_operated(mines: int, population: int) -> int:
    """Return the number of mines actually operating given population."""
    return min(mines, floor(population / 10000) * MINES_PER_10K)


def factories_operated(factories: int, population: int) -> int:
    """Return the number of factories actually operating given population."""
    return min(factories, floor(population / 10000) * FACTORIES_PER_10K)


def mine_minerals(mines_op: int, concentrations: Minerals) -> Minerals:
    """Calculate minerals mined this turn given operating mines and concentrations."""
    return Minerals(
        ironium=floor(mines_op * MINE_RATE * concentrations.ironium / 100),
        boranium=floor(mines_op * MINE_RATE * concentrations.boranium / 100),
        germanium=floor(mines_op * MINE_RATE * concentrations.germanium / 100),
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


def calculate_resources(population: int, factories_op: int) -> tuple[int, int, int]:
    """Return (pop_resources, factory_resources, total_resources)."""
    pop_resources = floor(population / COLONISTS_PER_RESOURCE)
    factory_resources = floor(factories_op * FACTORY_RATE)
    return pop_resources, factory_resources, pop_resources + factory_resources


def mining_rate(mines_op: int, concentrations: Minerals) -> Minerals:
    """Convenience alias for mine_minerals — used for player state display."""
    return mine_minerals(mines_op, concentrations)
