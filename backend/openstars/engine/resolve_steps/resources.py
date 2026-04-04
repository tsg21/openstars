"""Calculate per-planet resources for the current turn."""

from openstars.engine.resolve_steps import economy
from openstars.engine.turn_context import TurnContext


def calculate_planet_resources(ctx: TurnContext) -> None:
    """Populate ctx.planet_resources with planet_id → total resources for all owned planets."""
    for planet_id in sorted(ctx.planets_by_id.keys()):
        planet = ctx.planets_by_id[planet_id]
        if planet.owner is None:
            continue
        factories_op = economy.factories_operated(planet.factories, planet.population)
        _, _, total = economy.calculate_resources(planet.population, factories_op)
        ctx.planet_resources[planet_id] = total
