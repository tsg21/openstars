"""Mine minerals and deplete concentrations for all owned planets."""

from openstars.engine.models import GameEvent, Minerals, PlanetState
from openstars.engine.resolve_steps import economy


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

        planets_by_id[planet_id] = PlanetState(
            id=planet.id,
            owner=planet.owner,
            population=planet.population,
            mines=planet.mines,
            factories=planet.factories,
            minerals=new_minerals,
            concentrations=new_concs,
            mine_years=new_mine_years,
            is_homeworld=planet.is_homeworld,
        )

        event = GameEvent(
            type="mining_complete",
            turn=turn,
            planet_id=planet.id,
            planet_name=planet_names.get(planet.id),
            ironium=mined.ironium,
            boranium=mined.boranium,
            germanium=mined.germanium,
        )
        owner_events.setdefault(planet.owner, []).append(event)

    return owner_events
