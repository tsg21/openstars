from openstars.engine.component_catalogue import ComponentCatalogue
from openstars.engine.galaxy import galaxy_max_coord
from openstars.engine.models import Design, Galaxy, GalaxyPlanet, GlobalState, Player


class StateContext:
    """Read-only state/galaxy/design lookups shared across engine consumers."""

    def __init__(
        self,
        game_id: str,
        global_state: GlobalState,
        galaxy: Galaxy,
        designs: list[Design],
        component_catalogue: ComponentCatalogue,
    ) -> None:
        self.game_id = game_id
        self.global_state = global_state
        self.galaxy = galaxy
        self.designs = designs
        self.component_catalogue = component_catalogue

        self.max_coord: int = galaxy_max_coord(galaxy)
        self.planet_coords: set[tuple[int, int]] = {
            (planet.x, planet.y) for planet in galaxy.planets
        }
        self.galaxy_planets_by_id: dict[str, GalaxyPlanet] = {
            planet.id: planet for planet in galaxy.planets
        }
        self.planet_names: dict[str, str] = {planet.id: planet.name for planet in galaxy.planets}
        self.planet_coordinates_by_id: dict[str, tuple[int, int]] = {
            planet.id: (planet.x, planet.y) for planet in galaxy.planets
        }

        self.designs_by_id: dict[str, Design] = {design.id: design for design in designs}
        self.players_by_username: dict[str, Player] = {
            player.username: player for player in global_state.players
        }

    def planet_coordinates(self, planet_id: str) -> tuple[int, int] | None:
        return self.planet_coordinates_by_id.get(planet_id)
