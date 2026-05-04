"""Turn resolution context."""

from collections.abc import Iterable

from openstars.engine.component_catalogue import ComponentCatalogue
from openstars.engine.ids import create_id
from openstars.engine.models import (
    Design,
    Fleet,
    Galaxy,
    GameEvent,
    GameMeta,
    GlobalState,
    PlanetState,
    Player,
    PlayerResearchState,
)
from openstars.engine.race.models import Race
from openstars.engine.state_context import StateContext


class TurnContext(StateContext):
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
        component_catalogue: ComponentCatalogue,
    ) -> None:
        """Args:
        designs: Snapshot of all ship designs (registry); not read from ``global_state``.
        """
        super().__init__(game_id, global_state, galaxy, designs, component_catalogue)

        # Mutable working copies
        self.fleets_by_id: dict[str, Fleet] = {f.id: f.model_copy() for f in global_state.fleets}
        self.planets_by_id: dict[str, PlanetState] = {
            p.id: p.model_copy() for p in global_state.planets
        }
        self.research_state_by_username: dict[str, PlayerResearchState] = {
            player.username: player.research_state for player in global_state.players
        }
        self.race_by_username: dict[str, Race] = {
            player.username: player.race
            for player in global_state.players
            if player.race is not None
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
        self.research_reserved_by_planet: dict[str, int] = {}
        self.research_leftover_by_planet: dict[str, int] = {}
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
            players=[
                Player(
                    username=player.username,
                    name=player.name,
                    race=self.race_by_username.get(player.username),
                    research_state=self.research_state_by_username[player.username],
                )
                for player in self.global_state.players
            ],
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
