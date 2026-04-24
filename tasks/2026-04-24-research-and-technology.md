# Research & Technology — backend implementation

**Date:** 2026-04-24
**Goal:** Implement the research system described in PRD 21. Players gain six-field tech state, planetary resources are diverted to research each turn, level-ups fire events, component/hull tech prerequisites gate design creation, and miniaturisation is applied at build time in production (so new builds of an existing design get cheaper as the owner's tech advances). Commands are added for `set_research` and `set_planet_production_mode`. UI is deferred.
**Relevant PRDs:** [21 — Research & Technology](docs/prd/21-research-and-technology.md), [05 — Global State](docs/prd/05-global-state.md), [07 — Turn Mechanics](docs/prd/07-turn-mechanics.md), [12 — Economy & Resources](docs/prd/12-economy-and-resources.md), [13 — Production](docs/prd/13-production.md), [18 — Ship Design](docs/prd/18-ship-design.md), [19 — Hull Slot Definitions](docs/prd/19-hull-slot-definitions.md), [20 — Component Catalogue](docs/prd/20-component-catalogue.md), [51 — Event Codes](docs/prd/51-event-codes.md)

---

## Preamble — naming reconciliation

The PRD uses `biotechnology` as the canonical sixth-field id (appears in commands, events, player state, and YAML `tech:` blocks). The existing `TechRequirements` Pydantic model in [component_catalogue.py](backend/openstars/engine/component_catalogue.py) uses `bio_tech`, and hull YAML files use `tech_requirements:` with a `bio_tech` key.

Decision for this task: **rename to match PRD 21.**

- Rename the Pydantic field `bio_tech` → `biotechnology` on `TechRequirements`.
- Rename the YAML key `bio_tech` → `biotechnology` across all YAML files under `backend/openstars/data/`.
- Keep the block's YAML key as `tech_requirements` (already established in YAML). The PRD example uses `tech:` as shorthand; align PRD wording with the YAML via a small PRD edit, rather than churn the YAML.
- Rename the keyword argument `bio_tech` on `resolve_planetary_scanner_tier` and its callers.

Step 1 does the rename cleanly before any research-specific work lands.

---

## Step 1 — Rename `bio_tech` → `biotechnology`

- [ ] Rename `bio_tech` to `biotechnology` on `TechRequirements` in [component_catalogue.py](backend/openstars/engine/component_catalogue.py).
- [ ] Rename the `bio_tech:` key to `biotechnology:` throughout [data/hulls.yaml](backend/openstars/data/hulls.yaml) and any component YAMLs under [data/components/](backend/openstars/data/components/).
- [ ] Rename the `bio_tech` kwarg on `resolve_planetary_scanner_tier` in [production.py](backend/openstars/engine/resolve_steps/production.py) and update callers in [fog.py](backend/openstars/engine/fog.py).
- [ ] Update the PRD 21 YAML example block key from `tech:` to `tech_requirements:` in [docs/prd/21-research-and-technology.md](docs/prd/21-research-and-technology.md) so PRD and code agree.
- [ ] Update tests in [test_component_catalogue.py](backend/tests/engine/test_component_catalogue.py) and [test_production.py](backend/tests/engine/test_production.py) that reference `bio_tech`.

Unit tests in this step:
- [ ] `load_component_catalogue()` loads all YAMLs without error after rename.
- [ ] A fixture YAML with a `biotechnology: 3` prerequisite parses and surfaces on the catalogue entry.
- [ ] A fixture YAML using the old `bio_tech:` key fails validation (confirms the rename is not silently accepted).

---

## Step 2 — Research cost formula module

New pure module: `backend/openstars/engine/research/costs.py`.

- [ ] `FIELDS: tuple[str, ...] = ("energy", "weapons", "propulsion", "construction", "electronics", "biotechnology")` — module-level canonical order.
- [ ] `MAX_LEVEL: int = 26`.
- [ ] `BASE_COST: tuple[int, ...]` — 26 entries, the Fibonacci table from PRD 21 (`50, 80, 130, …, 8320400`). Build via a short recurrence at module load, not a hand-typed list, so the constants can't drift.
- [ ] `def base_cost(level: int) -> int` — returns `BASE_COST[level]`. Raises for `level < 0` or `level >= MAX_LEVEL`.
- [ ] `def level_up_cost(current_level: int, total_levels: int) -> int` — returns `base_cost(current_level) + 10 * total_levels`. Raises for `current_level == MAX_LEVEL` (caller must check cap first).
- [ ] `def total_levels(levels: Mapping[str, int]) -> int` — sum over `FIELDS`.

Unit tests in this step (`backend/tests/engine/research/test_costs.py`):
- [ ] `BASE_COST[0] == 50` and `BASE_COST[1] == 80`.
- [ ] `BASE_COST[L] == BASE_COST[L-1] + BASE_COST[L-2]` for every `L` in `2..25`.
- [ ] `len(BASE_COST) == 26`; `BASE_COST[25] == 8_320_400`.
- [ ] `level_up_cost(0, 0) == 50` and `level_up_cost(0, 12) == 50 + 120`.
- [ ] `level_up_cost(25, 0) == 8_320_400`; `level_up_cost(26, 0)` raises.
- [ ] `FIELDS` is ordered and contains exactly the six canonical ids.

---

## Step 3 — `PlayerResearchState` and `PlanetState` research toggle

Add research state to the engine models in [models.py](backend/openstars/engine/models.py).

- [ ] New `PlayerResearchState(BaseModel)`:
  - `levels: dict[str, int]` — keys = `FIELDS`, values `0..26`.
  - `progress: dict[str, int]` — keys = `FIELDS`, values `>= 0`.
  - `current_field: str` — must be in `FIELDS`.
  - `next_field: str | None` — must be in `FIELDS` when set.
  - `allocation_percent: int` — `0..100`.
  - `@model_validator(mode="after")` enforces key coverage (every canonical field appears in both `levels` and `progress`) and ranges.
- [ ] Add `research_state: PlayerResearchState` to `Player` (required — Turn 0 fills it).
- [ ] Add `contribute_only_leftover_to_research: bool = False` to `PlanetState`.
- [ ] Add `PlayerStateResearch(BaseModel)` for the projection view (used in Step 12):
  - `levels`, `progress`, `current_field`, `next_field`, `allocation_percent`, `cost_to_next_level: int`, `estimated_resources_this_turn: int`.
- [ ] Add `research: PlayerStateResearch | None` to `PlayerState` (optional only because tests may build partial states; defaults to `None` on the model but the projection always fills it for real games).
- [ ] Add `contribute_only_leftover_to_research: bool | None = None` to `PlayerPlanet` (populated only for the viewing owner's planets).

Unit tests in this step (`backend/tests/engine/test_models_research.py`):
- [ ] Constructing `PlayerResearchState` with all six `levels` and `progress` keys succeeds.
- [ ] Missing one `levels` key raises.
- [ ] A `current_field` not in `FIELDS` raises.
- [ ] `allocation_percent=101` raises; `-1` raises.
- [ ] `next_field=None` is accepted.
- [ ] A `Player` can be constructed with a `research_state`.
- [ ] `PlanetState` defaults `contribute_only_leftover_to_research` to `False`.

---

## Step 4 — Turn 0 defaults and state migration

- [ ] In [create_game.py](backend/openstars/engine/create_game.py), construct each `Player` with a fresh `PlayerResearchState`:
  - `levels` = all six fields at 0.
  - `progress` = all six fields at 0.
  - `current_field = "energy"`.
  - `next_field = None`.
  - `allocation_percent = 15`.
- [ ] In [state_versioning.py](backend/openstars/storage/state_versioning.py), extend `upgrade_global_state_payload`:
  - For each `player` in `payload["players"]`, if `research_state` is missing, insert the default turn-0 record.
  - For each `planet` in `payload["planets"]`, if `contribute_only_leftover_to_research` is missing, insert `False`.
- [ ] Keep `STATE_VERSION = 1` (per PRD 21's migration note — no formal bump).

Unit tests in this step:
- [ ] `create_initial_state(...)` returns a state whose every `Player` has `research_state.current_field == "energy"` and `allocation_percent == 15`.
- [ ] `create_initial_state(...)` returns planets with `contribute_only_leftover_to_research == False`.
- [ ] A payload persisted without `research_state` round-trips via `upgrade_global_state_payload` with defaults applied, and `GlobalState.model_validate` accepts the result.
- [ ] A payload persisted without `contribute_only_leftover_to_research` on a planet round-trips with `False`.

---

## Step 5 — `set_research` command

- [ ] Add `SetResearchCommand` to [models.py](backend/openstars/engine/models.py):
  - `type: Literal["set_research"] = "set_research"`.
  - `current_field: str | None = None`.
  - `next_field: str | None | Literal["__unset__"] = "__unset__"` — trick to distinguish "absent" from "explicit `null`"; see below.
  - `allocation_percent: int | None = None`.
  - Validator: if `current_field` or `next_field` is a string, it must be in `FIELDS`. `allocation_percent` must be `0..100`.
- [ ] Simpler alternative if the sentinel is ugly: accept the command as a free-form `dict[str, Any]` at the command-application layer and branch on key presence. Either is fine — pick whichever plays nicely with `PlayerCommand` union and the frontend encoding.
- [ ] Add to the `PlayerCommand` discriminated union.
- [ ] New module `backend/openstars/engine/resolve_steps/commands/set_research.py`:
  - `def apply_set_research_command(ctx, username, cmd) -> None`.
  - Look up the player by username; if not a real player, raise a validation-style error matching existing command patterns.
  - Update only the fields present on the command. If `current_field == next_field` post-update, set `next_field = None`.
  - Field progress is **not** reset on switch (per PRD — per-field progress is retained).
- [ ] Wire into [apply_commands.py](backend/openstars/engine/resolve_steps/apply_commands.py).
- [ ] Add error codes per PRD: `RESEARCH_FIELD_UNKNOWN`, `RESEARCH_ALLOCATION_OUT_OF_RANGE` (surface via HTTP 400 consistent with other commands; see existing `production` commands for the pattern).
- [ ] The engine needs mutable per-player research state. `TurnContext` currently lacks player copies — add `research_state_by_username: dict[str, PlayerResearchState]` populated from `global_state.players` and written back in `build_result()` (rebuild the `players` list with updated `research_state`).

Unit tests in this step:
- [ ] Applying `{current_field: "weapons"}` to a player currently on `energy` updates `current_field` and preserves `progress["energy"]`.
- [ ] Applying `{allocation_percent: 60}` to a player updates only that field.
- [ ] Applying `{next_field: null}` clears `next_field`.
- [ ] Applying `{current_field: "weapons", next_field: "weapons"}` results in `next_field == None`.
- [ ] Applying `{current_field: "nonsense"}` raises the field-unknown error.
- [ ] Applying `{allocation_percent: 150}` raises the out-of-range error.
- [ ] Multiple `set_research` commands in one turn are applied in order — the last one wins.
- [ ] The built `GlobalState` reflects the updated `research_state` on the named player.

---

## Step 6 — `set_planet_production_mode` command

- [ ] Add `SetPlanetProductionModeCommand` with `planet_id: str` and `contribute_only_leftover_to_research: bool`.
- [ ] Wire into the `PlayerCommand` union and `apply_commands.py`.
- [ ] New command handler in `resolve_steps/commands/set_planet_production_mode.py`.
- [ ] Validation: planet must exist and be owned by `username`, else `PLANET_NOT_OWNED`.
- [ ] Mutates `ctx.planets_by_id[planet_id].contribute_only_leftover_to_research`.

Unit tests in this step:
- [ ] Applying to an owned planet flips the flag.
- [ ] Applying to someone else's planet raises `PLANET_NOT_OWNED`.
- [ ] Applying to an unknown planet id raises.
- [ ] The built `GlobalState` reflects the change on the named planet.

---

## Step 7 — Research reservation in the resources step

The resources step ([resources.py](backend/openstars/engine/resolve_steps/resources.py)) currently writes `ctx.planet_resources[planet_id] = total_resources`. Research needs to pre-subtract the reserved allocation **before** production runs, and production leftovers need to flow to research in Step 8.

- [ ] Introduce a new bookkeeping dict on `TurnContext`: `research_reserved_by_planet: dict[str, int]` and `research_leftover_by_planet: dict[str, int]` (production mutates the latter when it finishes; see next bullet).
- [ ] In the resources step, for each owned planet compute `total_resources` as today. Then:
  - If `planet.contribute_only_leftover_to_research`: `reserved = 0`, `production_budget = total_resources`.
  - Else: `reserved = floor(total_resources * player.research_state.allocation_percent / 100)`, `production_budget = total_resources - reserved`.
  - Store `ctx.planet_resources[planet_id] = production_budget` (production reads this unchanged).
  - Store `ctx.research_reserved_by_planet[planet_id] = reserved`.
- [ ] In [production.py](backend/openstars/engine/resolve_steps/production.py), after `resolve_planet_production` returns, record `ctx.research_leftover_by_planet[planet_id] = remaining_resources_after_production` (the value `available_resources` at return time).
- [ ] Planets not owned by any player contribute nothing to research — leave both dicts unset for them.

Unit tests in this step:
- [ ] A planet with `total_resources=100`, `allocation_percent=15`, toggle off → `planet_resources=85`, `research_reserved=15`.
- [ ] A planet with `total_resources=100`, toggle on → `planet_resources=100`, `research_reserved=0`.
- [ ] A planet with `allocation_percent=100` → `planet_resources=0`, `research_reserved=100`.
- [ ] After production, `research_leftover_by_planet[planet_id]` equals the resources that production didn't spend.
- [ ] `research_leftover_by_planet` is zero for a planet whose queue consumed its whole budget.

---

## Step 8 — Research resolution step

New module: `backend/openstars/engine/resolve_steps/research.py`. Pure logic for the resolution procedure, plus the top-level step that walks players.

- [ ] `def apply_research_points(state: PlayerResearchState, points: int) -> tuple[PlayerResearchState, list[tuple[str, int]]]`:
  - Implements the Research Resolution Procedure exactly as spelled out in PRD 21.
  - Uses `level_up_cost` from `engine/research/costs.py`.
  - Returns the updated state and an ordered list of `(field_id, new_level)` tuples for each level-up that fired (so the caller can emit events).
  - Pure function — no side effects — so it can be unit-tested cleanly.
- [ ] `def resolve_research(ctx: TurnContext) -> None`:
  - For each username in **alphabetical order** (per PRD):
    - `research_points = 0`.
    - For each owned planet in **lexicographic planet_id order**:
      - `research_points += ctx.research_reserved_by_planet.get(planet_id, 0) + ctx.research_leftover_by_planet.get(planet_id, 0)`.
    - Call `apply_research_points(ctx.research_state_by_username[username], research_points)`.
    - Write the updated state back.
    - For each `(field, new_level)` returned, append a `GameEvent(owner=username, source_id=None, code="research.level_up", values=[field, new_level])`.

Unit tests in this step (`backend/tests/engine/test_research_resolution.py`):
- [ ] `apply_research_points` with `points=0` is a no-op.
- [ ] Cost to reach level 1 from 0 with `total_levels=0` is 50; spending exactly 50 levels up, progress resets to 0, one event fired.
- [ ] Spending 49 accumulates in `progress["energy"]` and fires no event.
- [ ] Spending enough to level up twice in one call fires two events in order.
- [ ] When the current field caps at 26 and `next_field` is set to an uncapped field, the switch happens and remaining points feed into the new field's existing progress.
- [ ] When the current field caps at 26 and no viable `next_field` is set, leftover points are discarded silently (no event).
- [ ] Progress is per-field: switching mid-resolution retains the old field's progress.
- [ ] `total_levels` penalty applies at the moment of level-up (not next-turn-delayed).
- [ ] `resolve_research` sums reserved + leftover across all the player's planets in lex order.
- [ ] `resolve_research` orders per-player processing alphabetically by username.

---

## Step 9 — Wire into `resolve_turn`

- [ ] Update `resolve_turn` in [resolve.py](backend/openstars/engine/resolve.py) to invoke `resolve_research(ctx)` after `resolve_production(ctx)` and before combat. Note: PRD 21 says "research runs after production". Current pipeline order is: combat → mining → resources → production. Insert research **between production and combat on the next turn**, i.e. immediately after `resolve_production(ctx)` and before `grow_population(ctx)`. Combat presently runs earlier in the turn (post-movement); that's fine — research only consumes resources, not combat outcomes.
- [ ] `TurnContext.build_result` must project the updated `research_state_by_username` back into the `players` list.

Unit tests in this step:
- [ ] A two-turn simulation where one player has `allocation_percent=50` on a 100-resource planet advances `energy` from 0 to 1 after enough cumulative turns; turn counter increments normally.
- [ ] A turn with no research allocation (all planets toggle-only-leftover and production empty) still levels up the current field from leftovers.
- [ ] A player with no owned planets has `research_state` unchanged and emits no events.

---

## Step 10 — Design creation: tech gating (no miniaturisation here)

Design cost is the **base** catalogue cost. Miniaturisation does not apply at design creation — designs are immutable (PRD 18), but new builds of a design get cheaper as the owner's tech advances, so the discount must be computed at build time (Step 10b), not baked into the design.

- [ ] In [designs.py](backend/openstars/engine/designs.py) `build_design`, look up the commanding player's research levels and:
  - For each assigned component and the hull, check every `tech_requirements` field against the player's `levels`. If any requirement is unmet, raise `DesignValidationError` with code `TECH_LOCKED` and a message naming the first unmet component/hull and the first unmet field.
  - Otherwise, proceed to sum hull + component catalogue cost unchanged (no discount applied). The stored `Design.cost` is the un-miniaturised base cost.
- [ ] Thread the player's `research_state.levels` into `build_design` — the simplest shape is a new keyword arg `player_levels: Mapping[str, int]`. Update callers in [create_game.py](backend/openstars/engine/create_game.py) (turn-0 starter designs pass all-zero levels, which matches the 0-prereq starter designs) and [routes/designs.py](backend/openstars/server/routes/designs.py) (pull from the player's `research_state`).
- [ ] Update [routes/designs.py](backend/openstars/server/routes/designs.py) to surface `TECH_LOCKED` as HTTP 400.

Unit tests in this step:
- [ ] A design referencing a component whose `tech_requirements` exceed the player's levels is rejected with `TECH_LOCKED`.
- [ ] A design referencing a component exactly at the requirement is accepted.
- [ ] The stored `Design.cost` equals the base catalogue sum regardless of how far the player exceeds the requirements (no discount baked in at creation).
- [ ] A design with zero-prereq components is accepted for a player with all levels at 0.

---

## Step 10b — Miniaturisation at build time in production

Production consumes resources per queued ship. The per-ship cost is computed from the owner's **current** `research_state.levels` against the design's hull + components in the catalogue — not read from `Design.cost`.

- [ ] New helper in `backend/openstars/engine/research/miniaturisation.py`:
  - `def miniaturisation_discount(tech_req: Mapping[str, int], levels: Mapping[str, int]) -> float` — returns `min(excess, 19) * 0.04` where `excess = min(26 - max(tech_req.values(), default=0), min(levels[f] - tech_req[f] for f in FIELDS))`. Returns `0.0` if any requirement is unmet (should not normally happen at build time since gating ran at design creation, but defensive).
  - `def miniaturise_cost(base: CostLike, discount: float) -> CostLike` — applies `raw = cost * (1 - discount)`, round half-to-even to nearest int per field, clamp `>= 1` for any non-zero original field. Operates on each of `resources`, `ironium`, `boranium`, `germanium` uniformly.
  - `def design_build_cost(design: Design, catalogue: ComponentCatalogue, levels: Mapping[str, int]) -> ProductionCost` — walks the design's hull and each component entry, miniaturises each against `levels` with its own `tech_requirements`, sums the post-discount per-entry costs into a single `ProductionCost`.
- [ ] Update `get_ship_queue_item_cost` in [production.py](backend/openstars/engine/resolve_steps/production.py) to:
  - Fetch the design owner's `research_state.levels` from `ctx.research_state_by_username` (introduced in Step 5).
  - Return `design_build_cost(design, ctx.catalogue, levels)` instead of reading `design.cost`.
  - `design.cost` on the immutable design stays as the un-miniaturised base — still useful for the designer UI and audit, but not consulted here.
- [ ] Confirm `ctx.catalogue` (or the equivalent component-catalogue handle) is already on `TurnContext`; if not, wire it through.

Unit tests in this step (`backend/tests/engine/test_miniaturisation.py`):
- [ ] `miniaturisation_discount({"energy": 3}, {"energy": 3, ...})` returns `0.0` (exact match, no excess).
- [ ] One level above every requirement gives `0.04`.
- [ ] 19 levels above gives `0.76`; 20 levels above is still `0.76` (cap).
- [ ] `excess` is bounded by `26 - max(tech_req.values())`, so a `tech_req = {energy: 22}` caps excess at 4 regardless of the player's energy level.
- [ ] `miniaturise_cost` applies the discount uniformly to all four cost fields.
- [ ] A component whose original `resources` cost is non-zero still has at least `1` after heavy miniaturisation (floor clamp).
- [ ] A zero cost field stays zero (no `max(1, 0)` misapplied).
- [ ] Round half-to-even is used (assert on a value on a .5 boundary).
- [ ] `design_build_cost` for a design with a component at `tech_req = {energy: 3}` and a player at `energy = 4` returns the expected discounted cost; the same design for a player at `energy = 3` returns the base cost.
- [ ] A component with no `tech_requirements` (all zero) miniaturises based on the player's lowest field level — e.g. player with `min(levels) = 5` gets a 20% discount on such a component.
- [ ] Hull cost is miniaturised using the hull's own `tech_requirements`, independently of component-level discounts.
- [ ] Integration: `get_ship_queue_item_cost` returns a lower cost after the owner research levels up vs. before, for the same design — covering the core mechanic that dynamic miniaturisation exists to deliver.

---

## Step 11 — PlayerState research projection

- [ ] In [fog.py](backend/openstars/engine/fog.py) `derive_player_state`, populate `PlayerState.research`:
  - `levels`, `progress`, `current_field`, `next_field`, `allocation_percent` — from `global_state.players[viewer].research_state`.
  - `cost_to_next_level = level_up_cost(levels[current_field], total_levels)` when `levels[current_field] < 26`, else `0`.
  - `estimated_resources_this_turn` — sum over the viewer's owned planets of `floor(planet_resources_last_turn * allocation_percent / 100)`. The "last turn's total resources" value is already computed during resource calc — simplest source: use the current-turn `total_resources` the fog layer can recompute from `planet.population`, `planet.factories`, `planet.mines`, and habitability (same formulae as the resources step). If reusing the formula is awkward, store `planet_resources` on the `GlobalState` (already present as `GlobalState.planet_resources`) and read that.
- [ ] For each `PlayerPlanet` on the viewer's own planets, set `contribute_only_leftover_to_research` from the corresponding `PlanetState`. Leave `None` for planets the viewer doesn't own.

Unit tests in this step:
- [ ] Derived `PlayerState.research` matches the player's stored `research_state`.
- [ ] `cost_to_next_level` equals `level_up_cost(L, total)` for the viewer's current field.
- [ ] `cost_to_next_level == 0` when the viewer has maxed the current field.
- [ ] `estimated_resources_this_turn` aggregates across multiple owned planets.
- [ ] Non-owners' planets don't carry `contribute_only_leftover_to_research` in the derived state.

---

## Step 12 — Event codes registry

- [ ] Add `research.level_up` to [PRD 51](docs/prd/51-event-codes.md) — the registry entry with `values[0] = field_id`, `values[1] = new_level`, `source_id = null`. (Documentation-only; no code change here.)
- [ ] If there's an `EventCode` enum/Literal in the engine, extend it to include `research.level_up`. Grep for existing event codes to confirm the pattern.

---

## Step 13 — Lint and full test run

- [ ] `cd backend && uv run ruff check .` clean.
- [ ] `cd backend && uv run ruff format --check .` clean.
- [ ] `cd backend && uv run pytest` passes end-to-end.

---

## Step 14 — Integration test

Full-stack coverage through the HTTP API.

- [ ] Extend or add `backend/int_tests/test_research.py`:
  - Two players in a new game.
  - Player A submits `set_research` with `allocation_percent=100, current_field="propulsion"`.
  - Player B leaves defaults.
  - Both players submit empty turn files otherwise; resolve the turn.
  - Assert Player A's `research_state.progress["propulsion"]` equals the turn's planet resources (all 100% went to propulsion, nothing left to spend) or Player A levelled up if resources were sufficient.
  - Assert Player B did **not** change fields.
  - Repeat turns until Player A levels propulsion; assert a `research.level_up` event appears in Player A's event list for that turn and contains `("propulsion", 1)`.
- [ ] Second scenario: set `set_planet_production_mode { contribute_only_leftover_to_research: true }` on Player A's homeworld; queue enough production to consume all resources; confirm research progress for that turn is `0` (no reserved, no leftover) via Player A's `PlayerState.research.progress`.
- [ ] Third scenario: design creation rejects a design that references a component with a tech prerequisite the player hasn't met, returning HTTP 400 with body `{"code": "TECH_LOCKED", ...}`.

---

## Explicitly out of scope

- **Race-trait research modifiers** — cost-per-field multipliers (`0.5` / `1.0` / `1.75`), `Generalized Research`, `Bleeding Edge Technology`, JOAT scanner auto-upgrade. PRD 21 defers these; they layer on top of the standard cost profile once races land.
- **Tech trading / stealing / espionage** — diplomacy gifts, killed-ship tech recovery, captured-planet tech, `SS` espionage, Mystery Trader, Artifact planets.
- **Auto-select least-researched field on cap** — if a player maxes their current field without a `next_field` queued, leftover points discard silently. PRD 21 lists the auto-select as a backlog item.
- **Auto-upgrade of deployed components in existing fleets** — designs remain immutable; already-built ships do not get cheaper retroactively.
- **Hull-level prereqs beyond `construction`** — hull YAML supports the `tech_requirements` shape, but existing hull prereqs stay where they are; we do not author additional prereqs in this task.
- **Starbase miniaturisation** — starbase cost lookup in [production.py](backend/openstars/engine/resolve_steps/production.py) uses fixed `STARBASE_TOTAL_COSTS`. PRD 21 defers starbase miniaturisation until the starbase design editor exists.
- **Research dialog UI** — frontend editing of research allocation, leftover toggle, cost preview, and the Technology Browser are deferred to a separate frontend task.
- **PlayerState fog of `next_field` for other players** — `research` is always and only the viewer's own state.
- **Formal `state_version: 2` bump** — per PRD 21, the research-state additions use missing-field defaults on load; no bump is required in this task.
