"""Mine minerals and deplete concentrations for all owned planets."""

import logging

from openstars.engine.models import GameEvent, Minerals, PlanetState
from openstars.engine.resolve_steps import economy

log = logging.getLogger(__name__)


def mine_planets(
    planets_by_id: dict[str, PlanetState],
    planet_names: dict[str, str],
    turn: int,
) -> dict[str, list[GameEvent]]:
    """Run the mining step on all owned planets with mines.

    Mutates planets_by_id in-place. Returns per-owner mining events.
    Planets are processed in sorted ID order for determinism.
    """
    owner_events: dict[str, list[GameEvent]] = {}

    for planet_id in sorted(planets_by_id.keys()):
        planet = planets_by_id[planet_id]
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

        planets_by_id[planet_id] = planet.model_copy(
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
                planet_names.get(planet.id, planet.id),
                mined.ironium,
                mined.boranium,
                mined.germanium,
            ],
            turn=turn,
        )
        owner_events.setdefault(planet.owner, []).append(event)

    return owner_events
