"""Turn resolution context."""

from collections.abc import Iterable

from openstars.engine.component_catalogue import ComponentCatalogue
from openstars.engine.galaxy import galaxy_max_coord
from openstars.engine.ids import create_id
from openstars.engine.models import (
    Design,
    Fleet,
    Galaxy,
    GameEvent,
    GameMeta,
    GlobalState,
    PlanetState,
)


class TurnContext:
    """Holds all state and derived lookups for a single turn resolution.

    Created at the start of resolve_turn from the current GlobalState and Galaxy.
    Each resolve step reads from and writes back to the context.
    Call build_result() at the end to produce the new GlobalState.
    """

    def __init__(
        self,
        game_id: str,
        global_state: GlobalState,
        galaxy: Galaxy,
        designs: list[Design],
        component_catalogue: ComponentCatalogue | None = None,
    ) -> None:
        """Args:
        designs: Snapshot of all ship designs (registry); not read from ``global_state``.
        """
        self.game_id = game_id
        self.global_state = global_state
        self.galaxy = galaxy
        self.component_catalogue = component_catalogue

        # Mutable working copies
        self.fleets_by_id: dict[str, Fleet] = {f.id: f.model_copy() for f in global_state.fleets}
        self.planets_by_id: dict[str, PlanetState] = {
            p.id: p.model_copy() for p in global_state.planets
        }
        self.designs_by_id: dict[str, Design] = {d.id: d for d in designs}

        # Galaxy-derived lookups (snapshotted once at init)
        self.max_coord: int = galaxy_max_coord(galaxy)
        self.planet_coords: set[tuple[int, int]] = {(gp.x, gp.y) for gp in galaxy.planets}
        self.planet_names: dict[str, str] = {gp.id: gp.name for gp in galaxy.planets}
        self.planet_coordinates_by_id: dict[str, tuple[int, int]] = {
            gp.id: (gp.x, gp.y) for gp in galaxy.planets
        }
        self.planets_by_coord: dict[tuple[int, int], PlanetState] = {
            (gp.x, gp.y): self.planets_by_id[gp.id]
            for gp in galaxy.planets
            if gp.id in self.planets_by_id
        }

        # ID generation state
        self._next_id: int = global_state.game.next_id

        # Accumulated outputs (populated during resolution)
        self.owner_events: dict[str, list[GameEvent]] = {}
        self.planet_resources: dict[str, int] = {}
        self.pop_growth: dict[str, int] = {}
        self.fleets: list[Fleet] = []

    def build_result(self) -> GlobalState:
        """Assemble the new GlobalState from the resolved context."""
        return GlobalState(
            game=GameMeta(
                seed=self.global_state.game.seed,
                turn=self.global_state.game.turn + 1,
                next_id=self._next_id,
                combat_ruleset=self.global_state.game.combat_ruleset,
            ),
            players=self.global_state.players,
            planets=[self.planets_by_id[p.id] for p in self.global_state.planets],
            fleets=self.fleets,
            events=self.owner_events,
            planet_resources=self.planet_resources,
            pop_growth=self.pop_growth,
        )

    def append_event(self, event: GameEvent) -> None:
        self.owner_events.setdefault(event.owner, []).append(event)

    def append_events(self, events: Iterable[GameEvent]) -> None:
        for event in events:
            self.append_event(event)

    def allocate_id(self, prefix: str) -> str:
        """Allocate an entity ID.

        Args:
            prefix: 2-char uppercase prefix (PL, FL, DE).

        Returns:
            entity_id
        """

        result = create_id(self._next_id, self.global_state.game.seed, prefix)
        self._next_id = self._next_id + 1
        return result

    def planet_coordinates(self, planet_id: str) -> tuple[int, int] | None:
        return self.planet_coordinates_by_id.get(planet_id)
