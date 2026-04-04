"""Mine minerals and deplete concentrations for all owned planets."""

import logging

from openstars.engine.models import GameEvent, Minerals
from openstars.engine.resolve_steps import economy
from openstars.engine.turn_context import TurnContext

log = logging.getLogger(__name__)


def mine_planets(ctx: TurnContext) -> None:
    """Run the mining step on all owned planets with mines.

    Mutates ctx.planets_by_id in-place. Accumulates events into ctx.owner_events.
    Planets are processed in sorted ID order for determinism.
    """
    for planet_id in sorted(ctx.planets_by_id.keys()):
        planet = ctx.planets_by_id[planet_id]
        if planet.owner is None or planet.mines == 0:
            continue

        mines_op = economy.mines_operated(planet.mines, planet.population)
        mined = economy.mine_minerals(mines_op, planet.concentrations)

        new_minerals = Minerals(
            ironium=planet.minerals.ironium + mined.ironium,
            boranium=planet.minerals.boranium + mined.boranium,
            germanium=planet.minerals.germanium + mined.germanium,
        )

        min_conc = 30 if planet.is_homeworld else 1
        new_concs, new_mine_years = economy.deplete_concentrations(planet, mines_op, min_conc)

        ctx.planets_by_id[planet_id] = planet.model_copy(
            update={
                "minerals": new_minerals,
                "concentrations": new_concs,
                "mine_years": new_mine_years,
            }
        )
        log.debug(
            "mine: planet=%s owner=%s mined Fe=%d Bo=%d Ge=%d",
            planet.id,
            planet.owner,
            mined.ironium,
            mined.boranium,
            mined.germanium,
        )

        event = GameEvent(
            owner=planet.owner,
            source_id=planet.id,
            code="mining.complete",
            values=[
                ctx.planet_names.get(planet.id, planet.id),
                mined.ironium,
                mined.boranium,
                mined.germanium,
            ],
        )
        ctx.append_events([event])
