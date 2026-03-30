"""Calculate per-planet resources for the current turn."""

from openstars.engine.models import PlanetState
from openstars.engine.resolve_steps import economy


def calculate_planet_resources(
    planets_by_id: dict[str, PlanetState],
) -> dict[str, int]:
    """Return a mapping of planet_id → total resources for all owned planets."""
    planet_resources: dict[str, int] = {}
    for planet_id in sorted(planets_by_id.keys()):
        planet = planets_by_id[planet_id]
        if planet.owner is None:
            continue
        factories_op = economy.factories_operated(planet.factories, planet.population)
        _, _, total = economy.calculate_resources(planet.population, factories_op)
        planet_resources[planet_id] = total
    return planet_resources
