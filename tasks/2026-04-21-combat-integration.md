# Combat integration — wire the Altair engine into turn resolution

**Date:** 2026-04-21
**Goal:** Connect the existing Altair combat engine to the main game. After movement each turn, detect co-located fleets with different owners, run the engine on each battle site, persist the combat log as a standalone file, apply casualties back to the fleets, and emit a `combat.resolved` event per participating owner. UI changes are deliberately deferred.
**Relevant PRDs:** [80 — Combat Fundamentals](docs/prd/80-combat-fundamentals.md), [82 — Altair combat](docs/prd/82-combat-altair.md), [07 — Turn mechanics](docs/prd/07-turn-mechanics.md), [05 — Global State](docs/prd/05-global-state.md), [51 — Event codes](docs/prd/51-event-codes.md), [04 — Engine conventions](docs/prd/04-engine-conventions.md)
**Depends on:** [2026-04-21-altair-combat-tokens](tasks/2026-04-21-altair-combat-tokens.md) (completed)

---

## Step 1 — `combat_ruleset` on `GameMeta`

Add the combat ruleset id to the game-level metadata so the resolver can dispatch to the right engine.

- [x] Add `combat_ruleset: Literal["altair", "classic"] = "altair"` to `GameMeta` in `backend/openstars/engine/models.py`.
- [x] Thread it through `create_initial_state` so turn-0 state carries the default.
- [x] Update `upgrade_global_state_payload` in `backend/openstars/storage/state_versioning.py` to default missing `combat_ruleset` to `"altair"` on load (old saves stay loadable without bumping `STATE_VERSION`).
- [x] Update `TurnContext.build_result` to preserve `combat_ruleset` on the new state.

Unit tests in this step:
- [x] `create_initial_state(...)` returns a state with `game.combat_ruleset == "altair"`.
- [x] `GlobalState.model_validate` accepts `game.combat_ruleset = "classic"`.
- [x] A persisted payload written without `combat_ruleset` round-trips via `upgrade_global_state_payload` with the default applied.
- [x] `resolve_turn` preserves `combat_ruleset` across turns.

---

## Step 2 — Combat log storage

Persist `CombatLog` as a standalone JSON file per battle under `{game_id}/combat/{battle_id}.json`.

- [x] Extend the `GameStorage` abstract base with `save_combat_log(game_id, battle_id, log)`, `load_combat_log(game_id, battle_id)`, and `list_combat_logs(game_id) -> list[str]`.
- [x] Implement in `MemoryStorage` (`backend/openstars/storage/memory.py`).
- [x] Implement in `LocalStorage` (`backend/openstars/storage/local.py`) using `game_object_name` / `validate_segment` for path safety (reject battle ids that do not match the standard entity-id pattern).
- [x] Implement in `GCSStorage` (`backend/openstars/storage/gcs.py`) mirroring the path layout.
- [x] Import target for the log type: `openstars.combat.altair.models.CombatLog` — wrap reads with `CombatLog.model_validate_json` so the log's own schema version is respected.

Unit tests in this step:
- [x] `MemoryStorage.save_combat_log` + `load_combat_log` round-trip preserves events.
- [x] `LocalStorage` writes to `{base_path}/{game_id}/combat/{battle_id}.json` and reads it back.
- [x] `validate_segment` rejects a battle id containing `..` or `/`.
- [x] `list_combat_logs` returns stored battle ids for a game, empty list for a game with none.

---

## Step 3 — Battle detection and snapshot builder

New module `backend/openstars/engine/resolve_steps/combat.py`. This step focuses on the pure-input logic; Step 4 wires it to the resolver.

- [x] `def detect_battle_sites(fleets: Iterable[Fleet]) -> list[list[Fleet]]` — group by `(position.x, position.y)`; return only groups with two or more distinct owners. Groups are returned in ascending `"x,y"` lexicographic order; fleets within a group are sorted by `id`.
- [x] `def arena_entry_positions(owners: list[str], arena_size: int) -> dict[str, Position]` — deterministic placement on a circle of radius `arena_size * 4 // 10` around the arena centre. `owners` is passed in already lexicographically sorted; use an integer-safe sin/cos over `θ = 2π·i/N` (reuse the scaled-integer trig helper if one exists, otherwise add one in `openstars.combat.altair.geometry` and unit-test it). For `N == 1` (shouldn't arise — detection filters single-owner sites — but guard it) place at the centre.
- [x] `def build_battle_snapshot(fleets, designs_by_id, catalogue, config) -> BattleSnapshot` — materialise tokens via `tokens_from_fleet` with per-owner entry positions and a `token_id_prefix` derived from the battle id (passed in by the caller).
- [x] `def apply_casualties(snap_before: BattleSnapshot, log: CombatLog, fleets_by_id: dict[str, Fleet]) -> tuple[dict[str, Fleet], dict[str, int]]` — apply the PRD 80 proportional rule, return `(updated_fleets_by_id_entries, ships_lost_by_owner)`. Dissolve fleets whose composition totals zero. `initial_hp` for each token comes from the pre-battle snapshot; remaining HP comes from the final token state reconstructed by replaying `DamageAppliedEvent` / `TokenDestroyedEvent` in the log (so the engine need not be changed to return survivors separately).

Unit tests in this step:
- [x] Two fleets from different owners at the same `(x, y)` → one battle site.
- [x] Two fleets from the same owner at the same `(x, y)` → no battle site.
- [x] Three owners at one site → one battle site with three fleet groups.
- [x] Two sites at different coordinates → both detected, deterministic order.
- [x] `arena_entry_positions(["a", "b"], 10000)` places the two owners on opposite sides of the centre, both at radius `4000` (±1 for integer trig rounding).
- [x] `arena_entry_positions` is invariant under repeated calls (determinism).
- [x] `apply_casualties` with a token that lost half its HP reduces ship count by `ceil(n * 0.5)`.
- [x] `apply_casualties` dissolves a fleet when all its tokens hit HP 0.
- [x] `apply_casualties` preserves `position`, `waypoints`, `cargo`, `fuel`, `name` on survivors.
- [x] `ships_lost_by_owner` sums destroyed ships across all fleets of that owner at the site.

---

## Step 4 — Ruleset dispatch and resolve step

Complete `resolve_steps/combat.py` with the top-level `resolve_combat(ctx)` function and a ruleset dispatcher.

- [x] `def run_combat(ruleset: str, snap: BattleSnapshot, *, cfg: AltairCombatConfig | None = None) -> CombatLog`. For `"altair"`, call `openstars.combat.altair.engine.run_battle`. For `"classic"`, raise `NotImplementedError("classic ruleset not implemented")` with a clear message — no silent fallback.
- [x] `def resolve_combat(ctx: TurnContext, storage: GameStorage) -> None`:
  - Detect battle sites from `ctx.fleets_by_id`.
  - For each site (in deterministic order):
    - Allocate `battle_id = ctx.allocate_id("BT")`.
    - Build snapshot using `ctx.designs_by_id` and a loaded component catalogue (see helper below).
    - Call `run_combat(ctx.global_state.game.combat_ruleset, snap)`.
    - Persist the log via `storage.save_combat_log(game_id, battle_id, log)`.
    - Apply casualties back to `ctx.fleets_by_id` (dissolving destroyed fleets).
    - Append one `combat.resolved` event per participating owner with values `[battle_id, location_name, ships_lost]`. `source_id` is the lexicographically first participating fleet id for that owner from the pre-battle site group. `location_name` is the planet name, or the string `"deep space"`.
- [x] Component catalogue loading: resolve_combat accepts the catalogue (don't load per-battle). Pass it in from `resolve_turn` — load once using the existing `load_component_catalogue()`.
- [x] `resolve_combat` needs the `game_id`; thread it through by adding a `game_id: str` to `TurnContext.__init__` (or a new optional argument on `resolve_turn`). Prefer `TurnContext` so all resolve steps have access; Step 5 covers the wiring.

Unit tests in this step:
- [x] `run_combat("altair", snap)` returns a `CombatLog`; `run_combat("classic", snap)` raises `NotImplementedError`.
- [x] `resolve_combat` with no co-located fleets is a no-op: no logs written, no events emitted, `next_id` unchanged.
- [x] `resolve_combat` with one battle site writes exactly one log file named `BT…`, emits one `combat.resolved` event per participating owner, and updates `ctx.fleets_by_id` according to the log.
- [x] `resolve_combat` with two battle sites in the same turn allocates distinct `BT` ids in lexicographic site order and writes two log files.
- [x] `ships_lost` in the event equals the sum of ships destroyed across that owner's fleets at the site.
- [x] Event `source_id` is the recipient owner's lexicographically first participating fleet id from the pre-battle site group.
- [x] A fleet wiped out in combat no longer appears in `ctx.build_result().fleets`.

---

## Step 5 — Wire into `resolve_turn`

Plug the new step into the main pipeline between movement and mining.

- [x] Update `resolve_turn(...)` in `backend/openstars/engine/resolve.py` to accept `game_id: str` and `storage: GameStorage` (caller provides them; see next bullet), load the component catalogue once, and invoke `resolve_combat(ctx, storage)` after `move_fleets(ctx)` and before `mine_planets(ctx)`.
- [x] Update callers of `resolve_turn` in `backend/openstars/server/` (see `routes/play.py` for the turn-resolution call site) to pass the `game_id` and `storage` through.
- [x] `TurnContext` gains `game_id: str` and stores the catalogue snapshot so resolve steps can share a single instance.

Unit tests in this step:
- [x] `resolve_turn` with two co-located enemy fleets produces a new `GlobalState` whose `fleets` reflect casualties and whose `events` include a `combat.resolved` entry for each owner.
- [x] `resolve_turn` with no colliding fleets writes no combat logs and keeps all fleets.
- [x] `resolve_turn` with `combat_ruleset = "classic"` raises `NotImplementedError` when a battle would occur (and passes cleanly when no battle occurs).
- [x] Turn counter still increments after combat resolves.
- [x] `next_id` after the turn accounts for every `BT` id allocated during combat.

---

## Step 6 — Integration test

End-to-end coverage through the real resolver + storage interface.

- [x] Write `backend/tests/engine/test_resolve_combat.py` (or extend an existing integration test):
  - Two players, one fleet each, waypoints that converge on the same deep-space coordinate in turn 1.
  - Run `resolve_turn` with `MemoryStorage`.
  - Assert: exactly one log saved under a `BT…` id, contents parse as `CombatLog`, both players' event lists contain a `combat.resolved` event carrying the same `battle_id`, and the losing fleet is gone from `GlobalState.fleets`.
- [x] Second scenario in the same file: battle over a planet — assert the event's `source_id` is the participating fleet id and `values[1]` is the planet name.

---

## Step 7 — Lint and full test run

- [x] `uv run ruff check .` and `uv run ruff format --check .` clean.
- [x] `uv run pytest` passes end-to-end.

---

## Explicitly out of scope

- **UI** — the API for clients to fetch a combat log (`GET /api/v1/games/{game_id}/combat/{battle_id}`) is a separate task, as is the frontend replay viewer. The backend writes logs; clients can't read them yet.
- **Starbases in combat** — PRD 82 models them but Phase 1 integration ignores any starbase at the battle location. Covered separately.
- **Classic ruleset** — dispatcher raises `NotImplementedError`; no engine work here.
- **Per-fleet battle plans / stances** — the Altair engine uses its built-in AI with no per-fleet orders. Battle-plan commands come later.
- **Fog-of-war filtering of combat events** — `combat.resolved` goes to every participating owner only, which is the Phase 1 rule. Non-participant spectators are a later concern.
- **Player-state exposure of combat logs** — logs are stored server-side; player-state derivation changes are deferred to the UI pass.
- **Battle over existing colocation** — detection runs on post-movement positions; any fleets that were already colocated before movement fight on this turn too, which matches the intent (the prior turn's movement step produced that state).
