# TurnContext Refactor

Introduce a `TurnContext` class that bundles all current game state, the computed data structures derived at the start of `resolve_turn`, and the `next_id` counter. Steps in the resolution pipeline receive this context object instead of individual parameters, and accumulated outputs (events, planet resources, pop growth) are written back onto it. At the end of resolution, `build_result()` extracts everything into the new `GlobalState`.

## Step 1: Create `engine/turn_context.py`

- [x] Define `TurnContext` as a plain class in `backend/openstars/engine/turn_context.py`
- [x] `__init__(self, global_state: GlobalState, galaxy: Galaxy)` computes and stores:
  - Working copies: `fleets_by_id`, `planets_by_id`, `designs_by_id`
  - Galaxy-derived lookups: `max_coord`, `planet_coords`, `planet_names`, `planets_by_coord`
  - ID state: `next_id` (from `global_state.game.next_id`)
  - Empty accumulators: `owner_events`, `planet_resources`, `pop_growth`
  - `fleets: list[Fleet]` — empty list, populated by `move_fleets`
- [x] Add `build_result(self) -> GlobalState` that assembles the new state from all context fields
- [x] Move `galaxy_max_coord` to `engine/galaxy.py` (used by `TurnContext.__init__`)

Unit tests:
- [x] Add `tests/engine/test_turn_context.py` asserting that `TurnContext.__init__` correctly derives all lookups from a minimal `GlobalState` + `Galaxy`, and that `build_result()` produces a `GlobalState` with the expected turn number, `next_id`, planets, and fleets

Validation:
- [x] `cd backend && uv run pytest tests/engine/test_turn_context.py`

## Step 2: Update `apply_commands`

- [x] Change signature to `apply_commands(ctx: TurnContext, all_commands: dict[str, PlayerCommands]) -> None`
- [x] Read `fleets_by_id`, `planets_by_id`, `planet_coords`, `max_coord`, `global_state.game.seed`, and `next_id` from `ctx`; write updated `next_id` back to `ctx.next_id`
- [x] Internal sub-command handlers in `commands/` keep their current signatures — they are called from `apply_commands` with the individual fields

Unit tests:
- [x] Update `tests/engine/test_resolve.py` — direct calls to `apply_commands` now construct a `TurnContext` and pass it

Validation:
- [x] `cd backend && uv run pytest tests/engine/`

## Step 3: Update `move_fleets`

- [x] Change signature to `move_fleets(ctx: TurnContext) -> None`
- [x] Read `fleets_by_id`, `planets_by_coord`, `designs_by_id`, `planets_by_id`, `planet_names` from `ctx`
- [x] Set `ctx.fleets` to the sorted moved-fleet list; merge events into `ctx.owner_events`

Validation:
- [x] `cd backend && uv run pytest tests/engine/`

## Step 4: Update `mine_planets`, `calculate_planet_resources`, `resolve_production`, `grow_population`

- [x] `mine_planets(ctx: TurnContext) -> None` — reads `planets_by_id`, `planet_names`; merges events into `ctx.owner_events`
- [x] `calculate_planet_resources(ctx: TurnContext) -> None` — reads `planets_by_id`; sets `ctx.planet_resources`
- [x] `resolve_production(ctx: TurnContext) -> None` — reads `planets_by_id`, `planet_resources`, `planet_names`; merges events into `ctx.owner_events`
- [x] `grow_population(ctx: TurnContext) -> None` — reads `planets_by_id`, `planet_names`; sets `ctx.pop_growth`; merges events into `ctx.owner_events`

Validation:
- [x] `cd backend && uv run pytest tests/engine/`

## Step 5: Simplify `resolve_turn`

- [x] Replace the manual setup block and parameter-passing in `resolve_turn` with `ctx = TurnContext(global_state, galaxy)`
- [x] Call each step with `ctx`; return `ctx.build_result()`

Validation:
- [x] `cd backend && uv run pytest`

## Step 6: Final quality gate

- [x] `cd backend && uv run ruff check .`
- [x] `cd backend && uv run pytest`
