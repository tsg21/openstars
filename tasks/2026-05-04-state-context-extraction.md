# Extract StateContext for shared read-only lookups

**Date:** 2026-05-04
**Goal:** Pull the read-only state/galaxy/designs lookups currently built inside `TurnContext` (and rebuilt ad-hoc inside `derive_player_state`) into a smaller `StateContext` base class. `TurnContext` will extend it with resolution-only machinery; `derive_player_state` will accept a `StateContext` so the per-player loop in the resolve route shares one set of lookups.

While here, also drop init-time deep copies that turn out to be defensive overhead rather than load-bearing.

---

## Background

`resolve_turn` builds a [`TurnContext`](backend/openstars/engine/turn_context.py) which exposes `designs_by_id`, `planet_coordinates_by_id`, `planet_names`, `race_by_username`, `research_state_by_username`, and a few other lookups in addition to mutable working copies of fleets/planets and resolution accumulators (`owner_events`, `planet_resources`, `pop_growth`, `_next_id`).

`derive_player_state` in [`backend/openstars/engine/fog.py`](backend/openstars/engine/fog.py) rebuilds a similar set of lookups on every call: `galaxy_planets = {gp.id: gp for gp in galaxy.planets}`, a player-by-username scan via `next(...)`, a `design_scanners` dict, and a `designs_by_id` dict. The route in [`backend/openstars/server/routes/play.py`](backend/openstars/server/routes/play.py#L274-L287) calls `derive_player_state` once per player in a loop, so this rebuild is repeated N times per resolution.

### Why deep copies inside TurnContext are mostly unnecessary

A read of every write site shows:

- **`race_by_username`** — the only write is [select_race.py:64](backend/openstars/engine/resolve_steps/commands/select_race.py#L64) (`ctx.race_by_username[username] = selected_race`), which is a dict-slot reassignment of an already-deep-copied input race. All other sites read attributes (`.economy`, `.habitability`). The init-time `model_copy(deep=True)` of every player's race is pure defensive overhead.

- **`research_state_by_username`** — necessary today only because of one step. [turn_zero.py:118-128](backend/openstars/engine/resolve_steps/turn_zero.py#L118-L128) (`_apply_starting_tech_levels`) mutates the `levels` dict in place. Every other write site (`research.py:68`, `set_research.py:78`) returns a new state and reassigns the dict slot. Rewriting `_apply_starting_tech_levels` to do an immutable update lets us drop the deep copy.

- **`planets_by_id` / `fleets_by_id`** — shallow `model_copy()` at init. Writes through resolution use `model_copy(update={...})` plus dict-slot reassignment, but there are nested in-place mutations downstream (e.g. [production.py:483](backend/openstars/engine/resolve_steps/production.py#L483) does `updated_planet.production_queue.pop(queue_index)` on a planet returned from `resolve_planet_production`). It's plausible those copies are unnecessary too, but a full audit is wider in scope. **Out of scope for this task** — keep them as-is; revisit in a follow-up if desired.

- **`planets_by_coord`** — mutable working dict written alongside `planets_by_id` in [movement.py:53,83](backend/openstars/engine/resolve_steps/movement.py#L53). Stays on `TurnContext`. The static `planet_coords` set lives on `StateContext`.

---

## Design

### `StateContext` — new base class

Holds immutable references and lookups derived from a `(global_state, galaxy, designs)` triple. No copies, no accumulators, no ID generation.

Fields:
- `game_id: str`
- `global_state: GlobalState`
- `galaxy: Galaxy`
- `designs: list[Design]`
- `component_catalogue: ComponentCatalogue`
- Galaxy-derived: `max_coord: int`, `planet_coords: set[tuple[int, int]]`, `galaxy_planets_by_id: dict[str, GalaxyPlanet]` *(new)*, `planet_names: dict[str, str]`, `planet_coordinates_by_id: dict[str, tuple[int, int]]`
- State-derived: `designs_by_id: dict[str, Design]`, `players_by_username: dict[str, Player]` *(new)*

Methods:
- `planet_coordinates(planet_id) -> tuple[int, int] | None`

Note: `players_by_username` is the new entry point for fog code that currently uses `next((p for p in global_state.players if ...), None)`. It also gives consumers access to `.race` and `.research_state` without TurnContext's separate dicts — so `StateContext` itself does **not** expose `race_by_username` or `research_state_by_username`.

### `TurnContext` — now extends `StateContext`

After `super().__init__(...)`, sets up only resolution-specific state:
- Mutable working copies: `planets_by_id` (shallow `model_copy()`), `fleets_by_id` (shallow `model_copy()`).
- **Reference dicts (no copies)**: `race_by_username` and `research_state_by_username` — populated from the input state directly. Write sites already do their own copy where needed (`select_race` deep-copies the input; `apply_research_points` returns a new state).
- Coord lookup against the mutable working copies: `planets_by_coord`.
- ID generation: `_next_id`, `allocate_id`.
- Output accumulators: `owner_events`, `planet_resources`, `research_reserved_by_planet`, `research_leftover_by_planet`, `pop_growth`, `fleets`.
- Methods: `append_event`, `append_events`, `build_result`.

`build_result` continues to read `race_by_username.get(u)` and `research_state_by_username[u]` to assemble the new `Player` records. Because the dicts hold references rather than copies, the values seen there are the post-resolution objects — which is correct because every write site has already produced a new object before assigning into the dict.

### `derive_player_state` — new signature

```python
def derive_player_state(
    ctx: StateContext,
    username: str,
    *,
    previous_player_state: PlayerState | None = None,
) -> PlayerState
```

Replaces the current `(global_state, galaxy, username, designs, previous_player_state)` signature. Inside, replace:
- `galaxy_planets = {gp.id: gp for gp in galaxy.planets}` → `ctx.galaxy_planets_by_id`
- `next((p for p in global_state.players if p.username == username), None)` → `ctx.players_by_username.get(username)`
- `designs_by_id = {d.id: d for d in designs}` → `ctx.designs_by_id`
- `[d for d in designs if d.owner == username]` → derived from `ctx.designs`

`_scanner_positions` is updated to take `(ctx, username)` and read `ctx.global_state`, `ctx.galaxy`, `ctx.designs`, `ctx.players_by_username` directly. `_scan_level` is unchanged.

### `play.py` resolve route

Build the catalogue and a single `StateContext` once after `resolve_turn` returns, then reuse it across the per-player `derive_player_state` loop. (Turn 0 reloads the design registry; in that case rebuild the `StateContext` with the refreshed designs before deriving.)

---

## Step 1 — Make `_apply_starting_tech_levels` immutable

Rewrite [`_apply_starting_tech_levels`](backend/openstars/engine/resolve_steps/turn_zero.py#L116-L128) so it does not mutate `levels` in place. Build a new levels dict, then reassign:

```python
def _apply_starting_tech_levels(ctx: TurnContext, username: str, race: Race) -> None:
    state = ctx.research_state_by_username[username]
    new_levels = dict(state.levels)

    if race.prt == PRT.JACK_OF_ALL_TRADES:
        for field in new_levels:
            new_levels[field] = max(new_levels[field], 3)

    if race.research.start_at_tech_3:
        target = 4 if race.prt == PRT.JACK_OF_ALL_TRADES else 3
        for field, profile in race.research.field_profile.items():
            if profile == ResearchCostProfile.EXPENSIVE:
                new_levels[field] = max(new_levels[field], target)

    ctx.research_state_by_username[username] = state.model_copy(update={"levels": new_levels})
```

This is a behaviour-preserving rewrite — the existing JOAT / `start_at_tech_3` tests in `test_turn_zero_resolution.py` should pass unchanged.

- [ ] Rewrite `_apply_starting_tech_levels` to use immutable update.
- [ ] `cd backend && uv run pytest tests/engine/race/test_turn_zero_resolution.py` passes.

---

## Step 2 — Drop init-time deep copies in `TurnContext`

Change [`TurnContext.__init__`](backend/openstars/engine/turn_context.py#L30) so:

```python
self.race_by_username: dict[str, Race] = {
    p.username: p.race for p in global_state.players if p.race is not None
}
self.research_state_by_username: dict[str, PlayerResearchState] = {
    p.username: p.research_state for p in global_state.players
}
```

i.e. drop the `model_copy(deep=True)` calls. The `planets_by_id` and `fleets_by_id` shallow copies stay (out of scope, see Background).

- [ ] Drop the deep copies in `TurnContext.__init__`.
- [ ] Run the full backend suite — `cd backend && uv run pytest` — and confirm everything still passes. (If anything fails, the failure points to a hidden in-place mutation that needs fixing before this step lands.)

---

## Step 3 — Introduce `StateContext`

Create `backend/openstars/engine/state_context.py` with the `StateContext` class as designed above. `TurnContext` is not yet changed; this step adds a new module only.

- [ ] Create `backend/openstars/engine/state_context.py` defining `StateContext` with all fields and the `planet_coordinates` method.
- [ ] Unit tests in `backend/tests/engine/test_state_context.py`:
  - Construction populates `galaxy_planets_by_id`, `planet_names`, `planet_coordinates_by_id`, and `planet_coords` from a small galaxy.
  - `players_by_username` includes every player in `global_state.players` with the correct mapping.
  - `designs_by_id` indexes the designs list correctly.
  - `max_coord` matches `galaxy_max_coord(galaxy)` for several sizes.
  - `planet_coordinates(unknown_id)` returns `None`.

---

## Step 4 — Refactor `TurnContext` to extend `StateContext`

Change `TurnContext.__init__` to call `super().__init__(...)`, then set up only the resolution-specific fields. Remove from `TurnContext` the attribute assignments that `StateContext` now owns (`game_id`, `global_state`, `galaxy`, `component_catalogue`, `max_coord`, `planet_coords`, `planet_names`, `planet_coordinates_by_id`, `designs_by_id`).

`race_by_username` and `research_state_by_username` stay as TurnContext-only attributes (mutable reference dicts, no copies — already addressed in Step 2).

The constructor signature stays `(game_id, global_state, galaxy, designs, component_catalogue)` so existing call sites in `resolve.py` and tests don't change.

- [ ] Refactor `backend/openstars/engine/turn_context.py` to inherit from `StateContext`.
- [ ] `backend/tests/engine/test_turn_context.py` continues to pass without changes.
- [ ] Add a small assertion to `test_turn_context.py` that `TurnContext` exposes the inherited `players_by_username` and `galaxy_planets_by_id` lookups.
- [ ] `cd backend && uv run pytest tests/engine/test_turn_context.py tests/engine/test_resolve.py tests/engine/test_resolve_combat.py tests/engine/test_production.py tests/engine/test_merge_split_fleets.py` all pass.

---

## Step 5 — Refactor `derive_player_state` to accept `StateContext`

Change the signature to `derive_player_state(ctx, username, *, previous_player_state=None)`. Replace the inline lookup rebuilds inside the function body with `ctx.galaxy_planets_by_id`, `ctx.players_by_username`, `ctx.designs_by_id`, and `ctx.designs` as described in the design section.

Update `_scanner_positions` to take `(ctx, username)` and read `ctx.global_state`, `ctx.galaxy`, `ctx.designs`, `ctx.players_by_username` directly.

Update **all** existing callers in tests:
- `backend/tests/engine/test_fog_stale.py`
- `backend/tests/engine/test_economy.py`
- `backend/tests/engine/test_setup.py`
- (anywhere else a grep for `derive_player_state(` finds — there are no production callers besides `play.py`, which is updated in Step 6.)

For tests, the cleanest pattern is a small local helper:

```python
def _state_ctx(global_state, galaxy, designs):
    return StateContext("game1", global_state, galaxy, designs, load_component_catalogue())
```

- [ ] Update `derive_player_state` and `_scanner_positions` in `backend/openstars/engine/fog.py`.
- [ ] Update all test callers to construct a `StateContext` and pass it in.
- [ ] Existing fog-related unit tests continue to pass: `cd backend && uv run pytest tests/engine/test_fog_stale.py tests/engine/test_economy.py tests/engine/test_setup.py`.
- [ ] Add one new unit test (e.g. in `backend/tests/engine/test_fog_stale.py` or a new file) confirming that calling `derive_player_state` twice with the same `StateContext` produces identical `PlayerState` for both calls and does not mutate the context.

---

## Step 6 — Wire `StateContext` through the resolve route

In `backend/openstars/server/routes/play.py` `resolve()`:
1. After `resolve_turn` returns `new_state`, load the component catalogue once.
2. Build a single `StateContext(game_id, new_state, galaxy, designs, catalogue)`.
3. For the turn-0 special case where `designs` is reloaded, rebuild the `StateContext` with the refreshed list before deriving.
4. Loop over players using the shared context.

- [ ] Update `resolve()` in `backend/openstars/server/routes/play.py` to construct and reuse a `StateContext`.
- [ ] Existing route tests pass: `cd backend && uv run pytest tests/server/`.

---

## Step 7 — Lint, format, and integration test

- [ ] `cd backend && uv run ruff check .` clean.
- [ ] `cd backend && uv run ruff format --check .` clean.
- [ ] `cd backend && uv run pytest` passes.
- [ ] `./backend/int_tests/run.sh` passes.
