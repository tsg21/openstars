"""Research resolution step."""

from openstars.engine.models import GameEvent, PlayerResearchState
from openstars.engine.research.costs import MAX_LEVEL, level_up_cost, total_levels
from openstars.engine.turn_context import TurnContext


def apply_research_points(
    state: PlayerResearchState,
    points: int,
) -> tuple[PlayerResearchState, list[tuple[str, int]]]:
    if points <= 0:
        return state.model_copy(deep=True), []

    updated = state.model_copy(deep=True)
    level_ups: list[tuple[str, int]] = []
    remaining = points

    while remaining > 0:
        field = updated.current_field
        current_level = updated.levels[field]
        if current_level >= MAX_LEVEL:
            next_field = updated.next_field
            if next_field is None or updated.levels[next_field] >= MAX_LEVEL:
                break
            updated.current_field = next_field
            updated.next_field = None
            continue

        cost = level_up_cost(current_level, total_levels(updated.levels))
        current_progress = updated.progress[field]
        needed = cost - current_progress
        if remaining < needed:
            updated.progress[field] = current_progress + remaining
            remaining = 0
            break

        remaining -= needed
        updated.progress[field] = 0
        updated.levels[field] = current_level + 1
        level_ups.append((field, updated.levels[field]))

    return updated, level_ups


def resolve_research(ctx: TurnContext) -> None:
    players_by_name = {player.username: player for player in ctx.global_state.players}
    for username in sorted(players_by_name.keys()):
        owned_planets = sorted(
            planet.id for planet in ctx.planets_by_id.values() if planet.owner == username
        )
        research_points = 0
        for planet_id in owned_planets:
            research_points += ctx.research_reserved_by_planet.get(planet_id, 0)
            research_points += ctx.research_leftover_by_planet.get(planet_id, 0)

        updated_state, level_ups = apply_research_points(
            ctx.research_state_by_username[username], research_points
        )
        ctx.research_state_by_username[username] = updated_state
        for field, new_level in level_ups:
            ctx.append_event(
                GameEvent(
                    owner=username,
                    source_id=None,
                    code="research.level_up",
                    values=[field, new_level],
                )
            )
