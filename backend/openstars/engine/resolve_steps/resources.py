"""Calculate per-planet resources for the current turn."""

from openstars.engine.resolve_steps import economy
from openstars.engine.turn_context import TurnContext


def calculate_planet_resources(ctx: TurnContext) -> None:
    """Populate per-planet production budgets and reserved research points."""
    for planet_id in sorted(ctx.planets_by_id.keys()):
        planet = ctx.planets_by_id[planet_id]
        if planet.owner is None:
            continue
        factories_op = economy.factories_operated(planet.factories, planet.population)
        _, _, total = economy.calculate_resources(planet.population, factories_op)
        research_state = ctx.research_state_by_username[planet.owner]
        if planet.contribute_only_leftover_to_research:
            reserved = 0
            production_budget = total
        else:
            reserved = (total * research_state.allocation_percent) // 100
            production_budget = total - reserved
        ctx.planet_resources[planet_id] = production_budget
        ctx.research_reserved_by_planet[planet_id] = reserved
