# Race Design Phase A — MVP economy, habitability & turn-0 selection

**Date:** 2026-04-26
**Goal:** Implement Phase A of PRD 22. Players gain a `Race` record (JOAT-only PRT, no LRTs, full economy / habitability / growth / research-profile tunables) selected during a dedicated turn-0 phase. The economy, mining, and population resolve steps read race parameters from `player.race` instead of module-level constants. Game-start no longer materialises homeworlds; turn-0 resolution does. Frontend ships a minimal preset-picker plus basic custom-race form on a new turn-0 screen.
**Relevant PRDs:** [22 — Race Design](docs/prd/22-race-design.md), [05 — Global State](docs/prd/05-global-state.md), [12 — Economy & Resources](docs/prd/12-economy-and-resources.md), [14 — Population & Habitability](docs/prd/14-population.md)

---

## Preamble — turn-numbering shift

Today, [create_initial_state](backend/openstars/engine/create_game.py#L90) produces a `T=0` `GlobalState` with home planets already populated (25,000 colonists, 10 mines, 10 factories, starbase, starting fleets). This task makes `T=0` the race-selection phase: at game-start no planet is owned or marked as a homeworld, and there are no installations, starbases, or fleets anywhere. Home-planet assignment and full homeworld materialisation both happen during the resolution that produces `T=1`.

This shifts the year/turn numbering by one against the original Stars! convention (year 2400 → first commands → year 2401), but keeps it internally consistent: the engine ticks `turn` from 0 to 1 when race-selection orders resolve, and from 1 to 2 when the first proper turn resolves. Existing engine tests that assume a populated homeworld at game start use a new `submit_default_race_and_resolve_turn_0` helper introduced in Step 7.

---

## Step 1 — Race models

New module: `backend/openstars/engine/race/models.py`. Pure Pydantic schema; no engine plumbing.

- [x] `class PRT(StrEnum)` — all ten PRTs present with descriptive member names (`JACK_OF_ALL_TRADES`, `HYPER_EXPANSION`, etc.) and short serialised values (`"JOAT"`, `"HE"`, etc.) so the schema is forward-compatible; the API validator gates non-JOAT.
- [x] `class LRT(StrEnum)` — all 14 ids from PRD 22 §"Lesser Racial Traits", with descriptive member names (`IMPROVED_FUEL_EFFICIENCY`, `NO_RAMSCOOP_ENGINES`, etc.) and short serialised values. All present; API validator rejects any non-empty `lrts`.
- [x] `class ResearchCostProfile(StrEnum)` — `cheap`, `standard`, `expensive`.
- [x] `class LeftoverBonusKind(StrEnum)` — `surface_minerals, mines, factories, defenses, concentrations`.
- [x] `class RaceHabitabilityFactor(BaseModel)`:
  - `immune: bool = False`
  - `range: tuple[int, int] = (15, 85)` — both ints in `0..100`, `low <= high`.
  - `@model_validator(mode="after")` enforces ordering and `[0, 100]` bounds; when `immune == True` the range is ignored but still stored as-is.
- [x] `class RaceHabitability(BaseModel)`:
  - `gravity: RaceHabitabilityFactor`
  - `temperature: RaceHabitabilityFactor`
  - `radiation: RaceHabitabilityFactor`
- [x] `class RaceEconomy(BaseModel)`:
  - `colonists_per_resource: int = Field(ge=700, le=2500, default=1000)`
  - `factory_output_per_10: int = Field(ge=5, le=15, default=10)`
  - `factory_cost_resources: int = Field(ge=5, le=25, default=10)`
  - `factories_per_10k_colonists: int = Field(ge=5, le=25, default=10)`
  - `factories_save_germanium: bool = False`
  - `mine_output_per_10: int = Field(ge=5, le=25, default=10)`
  - `mine_cost_resources: int = Field(ge=2, le=15, default=5)`
  - `mines_per_10k_colonists: int = Field(ge=5, le=25, default=10)`
  - `ar_resource_divisor: int = Field(ge=5, le=25, default=10)` — only meaningful when PRT==AR; not exposed by the UI.
- [x] `class RaceResearch(BaseModel)`:
  - `field_profile: dict[str, ResearchCostProfile]` — keys = the canonical six fields from `engine/research/costs.py::FIELDS`. Validator enforces full key coverage. Default factory yields `{f: standard for f in FIELDS}`.
  - `start_at_tech_3: bool = False`
- [x] `class LeftoverBonus(BaseModel)`:
  - `kind: LeftoverBonusKind`
  - `points: int = Field(ge=1, le=50)`
- [x] `class Race(BaseModel)`:
  - `name: str = Field(min_length=1, max_length=32)`
  - `plural_name: str = Field(min_length=1, max_length=32)`
  - `emblem: int = Field(ge=0, le=31)`
  - `prt: PRT`
  - `lrts: frozenset[LRT] = Field(default_factory=frozenset)`
  - `habitability: RaceHabitability`
  - `max_growth_rate: int = Field(ge=1, le=20, default=15)`
  - `economy: RaceEconomy = Field(default_factory=RaceEconomy)`
  - `research: RaceResearch = Field(default_factory=RaceResearch)`
  - `leftover_bonus: LeftoverBonus | None = None`

Unit tests in this step (`backend/tests/engine/race/test_models.py`):

- [x] A minimal `Race` constructed with `prt=PRT.JACK_OF_ALL_TRADES` and default habitability validates, serialising `prt` as `"JOAT"`.
- [x] `RaceHabitabilityFactor(range=(60, 40))` raises (range out of order).
- [x] `RaceHabitabilityFactor(range=(-5, 50))` raises (low below 0).
- [x] `RaceEconomy(colonists_per_resource=600)` raises (below `ge=700`).
- [x] `RaceResearch` default factory produces all six fields at `standard`.
- [x] `RaceResearch(field_profile={"energy": "cheap"})` raises (missing five fields).
- [x] `LeftoverBonus(kind="mines", points=51)` raises.

---

## Step 2 — Race costs, validation, JOAT preset

New module: `backend/openstars/engine/race/costs.py`. Pure cost-table evaluation.

- [x] `POINTS_BUDGET = 1650`.
- [x] `prt_cost: dict[PRT, int]` — `PRT.JACK_OF_ALL_TRADES: 0`; the table still includes all ten (other entries placeholder, not exercised by the API since non-JOAT is rejected).
- [x] `lrt_cost: dict[LRT, int]` — placeholder zeros for all 14, exercised by future tasks.
- [x] `accelerator_cost = 60`.
- [x] `def hab_factor_cost(immune: bool, low: int, high: int) -> int`:
  - Width in `[0, 100]`. Wider band ⇒ cheaper. Band centred at 50 is cheapest; offsets ≥ 15 from centre return points back at diminishing rate.
  - Documented breakpoints (anchored to AutoHost guide): immunity ≈ +75 per factor; a ±0 (single value) band ≈ −60 (returned points); a ±35 (width 70) band ≈ baseline; widening past ±35 yields diminishing additional return.
  - Implementation: piecewise-linear over `width = high - low` and `offset = abs(((low + high) / 2) - 50)`. Tunable in this module.
- [x] `def hab_cost(hab: RaceHabitability) -> int` — sums the three factors.
- [x] `def growth_cost(rate: int) -> int` — table lookup. Honours the breakpoint anchors from PRD 22:
  - 18→19 marginal cost ≈ 50–70.
  - 19→20 marginal cost ≈ 100–150 (cliff at 20).
  - Below 15 returns negative (points back); above 15 costs increasingly.
- [x] `def economy_cost(eco: RaceEconomy) -> int` — sums per-parameter contributions, hitting the breakpoints in PRD 22 §"Breakpoint anchors":
  - `colonists_per_resource = 1000` baseline; 1000→900 cliff ≈ 200; 1000→1100 returns ≈ 40.
  - `factory_output_per_10 = 10` baseline; +1 ≈ 43; +2 ≈ 83; +3 ≈ 145 (cliff at 12→13 ≈ 62 marginal).
  - `factory_cost_resources = 10` baseline; 10→9 cliff ≈ 60.
  - `mine_cost_resources = 5` baseline; 4→3 ≈ 22; 3→2 ≈ 134 (cliff at 3).
  - `factories_save_germanium` ≈ 58 if `True`.
  - The other three params (`factories_per_10k_colonists`, `mines_per_10k_colonists`, `mine_output_per_10`) interpolate linearly off their defaults; precise breakpoints captured in inline `# anchor:` comments to guide future re-tuning.
- [x] `def research_cost(research: RaceResearch) -> int`:
  - Per field: `expensive ⇒ −150`, `standard ⇒ 0`, `cheap ⇒ +175`.
  - Plus `accelerator_cost` if `research.start_at_tech_3` is `True`.
- [x] `def leftover_bonus_cost(bonus: LeftoverBonus | None) -> int` — returns `bonus.points` if set else `0`.
- [x] `class RaceCostBreakdown(BaseModel)` — Pydantic API-facing model with `prt, lrts, habitability, growth, economy, research, leftover, total, points_left`.
- [x] `def race_cost_breakdown(race: Race) -> RaceCostBreakdown` — returns the Pydantic breakdown model. Used by the preview endpoint and the validator.
- [x] `class RaceValidationError(Exception)` with `code: str` and `detail: str`. Codes per PRD 22 §"Validation": `RACE_OVERSPENT`, `RACE_INVALID_BONUS`, plus three Phase-A gating codes used by the API validator: `RACE_PRT_NOT_AVAILABLE`, `RACE_LRT_NOT_AVAILABLE`, `RACE_BONUS_NOT_AVAILABLE`.
- [x] `def validate_race(race: Race) -> RaceCostBreakdown`:
  - Computes the breakdown.
  - Raises `RACE_OVERSPENT` if `points_left < 0`.
  - Rejects `prt != PRT.JACK_OF_ALL_TRADES` (`RACE_PRT_NOT_AVAILABLE`), any non-empty `lrts` (`RACE_LRT_NOT_AVAILABLE`), and any non-null `leftover_bonus` (`RACE_BONUS_NOT_AVAILABLE`).
  - Raises `RACE_INVALID_BONUS` if a leftover bonus is incompatible (kept here for forward-compat even though Phase A rejects bonuses outright).
  - Returns the breakdown on success.

New module: `backend/openstars/engine/race/presets.py`.

- [x] `HUMANOID: Race` — the JOAT preset matching the PRD §"Predefined races" table. Defaults: ranges `(15, 85)` per factor, `max_growth_rate=15`, default economy, all research `standard`, no `start_at_tech_3`, no leftover bonus, `name="Humanoid"`, `plural_name="Humanoids"`, `emblem=0`, `prt=PRT.JACK_OF_ALL_TRADES`, `lrts=()`.
- [x] `PREDEFINED_RACES: dict[str, Race] = {"humanoid": HUMANOID}` — the only available preset. Other ids return 404 from the API.
- [x] `def default_race() -> Race` — returns a fresh deep copy of `HUMANOID`. Used by the test helper in Step 7.

Unit tests in this step (`backend/tests/engine/race/test_costs.py`):

- [x] `validate_race(HUMANOID)` returns a breakdown whose `total == 0` and `points_left == 1650`. The Humanoid preset is the canonical zero-cost reference, so any drift in cost constants makes this test fail loudly.
- [x] `hab_factor_cost(False, 15, 85)` ≈ 0 (baseline width).
- [x] `hab_factor_cost(True, *)` ≈ 75 (immunity).
- [x] `hab_factor_cost(False, 50, 50)` returns negative (single-value band returns points).
- [x] `growth_cost(15) == 0`; `growth_cost(20)` is materially higher than `growth_cost(19)` (cliff at 20).
- [x] `economy_cost(RaceEconomy(colonists_per_resource=900, ...))` reproduces the ≈ 200-point cliff vs default.
- [x] `economy_cost(RaceEconomy(factories_save_germanium=True, ...))` adds ≈ 58 vs default.
- [x] `research_cost(RaceResearch(field_profile={f: cheap for f in FIELDS}))` returns `+175 * 6`; with all `expensive`, returns `-150 * 6`.
- [x] `validate_race(Race(... overspent ...))` raises `RACE_OVERSPENT`.
- [x] `validate_race(Race(prt=PRT.HYPER_EXPANSION, ...))` raises `RACE_PRT_NOT_AVAILABLE`.
- [x] `validate_race(Race(prt=PRT.JACK_OF_ALL_TRADES, lrts={LRT.IMPROVED_FUEL_EFFICIENCY}, ...))` raises `RACE_LRT_NOT_AVAILABLE`.
- [x] `validate_race(Race(prt=PRT.JACK_OF_ALL_TRADES, leftover_bonus=LeftoverBonus(kind=mines, points=10)))` raises `RACE_BONUS_NOT_AVAILABLE`.

---

## Step 3 — `Player.race` field

- [x] In [models.py](backend/openstars/engine/models.py), import `Race` from `engine.race.models` and add `race: Race | None = None` to `Player`. Field is `None` for the duration of `T=0`, populated at turn-0 resolution.
- [x] Add `race: Race | None = None` to `PlayerState` (PRD 22 §"Schema Changes" — viewer's own race fully visible). Populate it in [fog.py](backend/openstars/engine/fog.py) `derive_player_state` from the viewer's `Player.race`.

Unit tests in this step (`backend/tests/engine/race/test_player_race.py`):

- [x] A `Player(username="alice", name="Alice")` constructed without `race` has `race is None`.
- [x] A `Player(..., race=default_race())` constructs successfully and round-trips through JSON.
- [x] `derive_player_state` for a viewer with `Player.race == HUMANOID` populates `PlayerState.race` with the same record.
- [x] `derive_player_state` for a viewer with `Player.race is None` (turn-0 phase) yields `PlayerState.race is None`.

---

## Step 4 — Engine resolve steps read `race`

The plumbing change. Module-level constants in [economy.py](backend/openstars/engine/resolve_steps/economy.py) and [population.py](backend/openstars/engine/resolve_steps/population.py) are removed and read from the planet owner's race.

- [x] In [turn_context.py](backend/openstars/engine/turn_context.py), populate `self.race_by_username: dict[str, Race]` from `global_state.players` at init (mirroring `research_state_by_username`). Players whose `race is None` (turn-0 phase) are not added — for all turns `>= 1`, every player has a race by invariant.
- [x] Update `build_result()` to project `race` back onto each `Player`. The race only mutates during turn-0 resolution (Step 7); for other turns it's a passthrough.
- [x] [economy.py](backend/openstars/engine/resolve_steps/economy.py): remove the module-level `COLONISTS_PER_RESOURCE`, `FACTORY_RATE`, `FACTORY_COST_RESOURCES`, `FACTORY_COST_GERMANIUM`, `FACTORIES_PER_10K`, `MINE_RATE`, `MINE_COST_RESOURCES`, `MINES_PER_10K` constants. Replace each call site:
  - `mines_operated(mines, population, race_economy)` and `factories_operated(...)` take a `RaceEconomy` and read `mines_per_10k_colonists` / `factories_per_10k_colonists`.
  - `mine_minerals(mines_op, concentrations, race_economy)` reads `mine_output_per_10` (multiplier `mine_output_per_10 / 10`).
  - `calculate_resources(population, factories_op, race_economy)` reads `colonists_per_resource` and `factory_output_per_10` (multiplier `factory_output_per_10 / 10`).
  - These are pure helpers — they take a `RaceEconomy` directly rather than a full `Race` or context, so the unit tests stay simple.
- [x] Caller sites in [resources.py](backend/openstars/engine/resolve_steps/resources.py), [mining.py](backend/openstars/engine/resolve_steps/mining.py), and [production.py](backend/openstars/engine/resolve_steps/production.py) look up the planet owner's `race.economy` from `ctx.race_by_username` and pass it through. A planet with no owner is skipped exactly as today.
- [x] [population.py](backend/openstars/engine/resolve_steps/population.py): remove the module-level `GRAVITY_RANGE`, `TEMPERATURE_RANGE`, `RADIATION_RANGE`, `MAX_GROWTH_RATE` constants. Replace each call site:
  - `factor_contribution(v, low, high)` is unchanged. Callers read the range from the owner's `race.habitability.<factor>.range`. When `race.habitability.<factor>.immune == True`, callers short-circuit to `33.333` per PRD 22 §"Habitability".
  - `calculate_hab_value(hab, race_hab)` — new signature, takes the per-planet `Habitability` and the owner's `RaceHabitability`. Returns the rounded sum.
  - `max_population(hab, race_hab)` — calls `calculate_hab_value` with the race ranges.
  - `population_growth(population, hab, race_hab, max_growth_rate)` — uses `max_growth_rate / 100.0` instead of `MAX_GROWTH_RATE`.
- [x] `grow_population(ctx)` in [population.py](backend/openstars/engine/resolve_steps/population.py) looks up `ctx.race_by_username[planet.owner].habitability` and `.max_growth_rate` per planet.
- [x] Existing tests in [test_economy.py](backend/tests/engine/test_economy.py) and [test_population.py](backend/tests/engine/test_population.py) construct a JOAT `RaceEconomy` / `RaceHabitability` fixture and pass it through. Behaviour must be unchanged for JOAT (the constants previously used were exactly the JOAT defaults).
- [x] [fog.py](backend/openstars/engine/fog.py) uses the relevant owner's race when deriving detailed planet values: mining rate calls `mines_operated(..., owner_race.economy)`, and `max_population` calls `max_population(..., owner_race.habitability)`. At `T=0`, the empty command-phase player-state rule from Step 7 avoids calling these helpers while races are unset.

Unit tests in this step (additions, not just migrations of existing):

- [x] `calculate_resources(population=10000, factories_op=10, RaceEconomy(colonists_per_resource=800, factory_output_per_10=12))` returns `(12, 12, 24)` — i.e. the lower colonists-per-resource and higher factory output both apply.
- [x] `mine_minerals(mines_op=10, concentrations=Minerals(100, 100, 100), RaceEconomy(mine_output_per_10=12))` returns `Minerals(12, 12, 12)`.
- [x] `mines_operated(50, 100_000, RaceEconomy(mines_per_10k_colonists=15))` returns `min(50, 10*15) = 50`; with population `30_000` returns `min(50, 3*15) = 45`.
- [x] `population_growth` with a tighter race range (e.g. `(40, 60)` for gravity) on an off-ideal planet drops the rate vs the JOAT (15, 85) range.
- [x] `calculate_hab_value` with `RaceHabitabilityFactor(immune=True)` on gravity returns the 33.333 contribution regardless of the planet's gravity value.
- [x] `population_growth` with `max_growth_rate=10` is two-thirds of the same call with `max_growth_rate=15`.
- [x] `derive_player_state` on a `T>=1` detailed owned planet reports `max_population` using that player's race habitability, not JOAT defaults.
- [x] `derive_player_state` on a `T>=1` detailed owned planet reports `mining_rate` using that player's `mine_output_per_10` and `mines_per_10k_colonists`, not JOAT defaults.

---

## Step 5 — `select_race` command

The command shape submitted through `POST /commands`. Mirrors how `set_research` wires into the command pipeline.

- [x] Add `class SelectRaceCommand(BaseModel)` to [models.py](backend/openstars/engine/models.py):
  - `type: Literal["select_race"] = "select_race"`
  - One of `predefined_id: str | None = None` or `race: Race | None = None`. Validator enforces exactly one is set.
- [x] Add `SelectRaceCommand` to the `PlayerCommand` discriminated union.
- [x] New module `backend/openstars/engine/resolve_steps/commands/select_race.py`:
  - `def apply_select_race_command(ctx, username, cmd) -> None`.
  - Resolve the command to a full `Race`: if `predefined_id`, look up in `PREDEFINED_RACES` (raise `PREDEFINED_RACE_UNKNOWN` on miss); else use `cmd.race`.
  - Re-validate via `validate_race(race)` — raises `RaceValidationError` on drift / overspend.
  - Write into `ctx.race_by_username[username]`. The next `build_result()` projects it onto the corresponding `Player.race`.
- [x] Wire into [apply_commands.py](backend/openstars/engine/resolve_steps/apply_commands.py).
- [x] Add error codes: `PREDEFINED_RACE_UNKNOWN`, `RACE_REVALIDATION_FAILED` (raised by the resolution path when re-validation fails — consumed in Step 7).

Unit tests in this step (`backend/tests/engine/race/test_select_race_command.py`):

- [x] Applying `{predefined_id: "humanoid"}` to a player with `race is None` sets that player's `race` to the Humanoid preset in the built `GlobalState`.
- [x] Applying `{race: <custom>}` with a valid custom race writes the canonical record.
- [x] Applying a command with neither field set raises a validation error.
- [x] Applying a command with both `predefined_id` and `race` set raises a validation error.
- [x] Applying `{predefined_id: "rabbitoid"}` raises `PREDEFINED_RACE_UNKNOWN` (only Humanoid is registered).
- [x] Applying `{race: <overspent custom>}` raises `RACE_OVERSPENT` via `validate_race`.
- [x] Multiple `select_race` commands in one turn — the last one wins.

---

## Step 6 — Race preview, predefined list, and rehydration endpoints

Race selection itself goes through the existing `POST /commands` pipeline as a `SelectRaceCommand` (Step 5); submit-time enforcement is wired in Step 8. The endpoints below are read-side conveniences plus a no-side-effect preview for live cost feedback while editing.

New router: `backend/openstars/server/routes/race.py`. Mounted under the existing `/api/v1` prefix.

- [x] `POST /api/v1/race/preview`:
  - Auth: any authenticated user (no game scope).
  - Body: `{ "race": Race }` (no `predefined_id` — preview is for editing custom races).
  - Calls `validate_race(race)` and returns the breakdown without persisting anything. On `RaceValidationError` returns 400 with the code; on success returns `{ "cost_breakdown": <...>, "points_left": <int> }`.
- [x] `GET /api/v1/games/{game_id}/race`:
  - Auth: caller must be a player in the game (`403 NOT_PLAYER` otherwise).
  - Convenience read of the caller's currently-saved turn-0 selection (if any). Used by the frontend to rehydrate the form after refresh.
  - Returns `{ "race": Race | null, "cost_breakdown": <...> | null }`. At `T=0`, reads from the on-disk turn-0 commands and returns `null` if no `SelectRaceCommand` has been saved yet. At `T>=1`, reads the immutable snapshotted `Player.race` from global state.
- [x] `GET /api/v1/race/predefined` — returns the list of predefined-race ids and their canonical `Race` records: `[{"id": "humanoid", "race": <HUMANOID>}]`. Unauthenticated since presets are static reference data.
- [x] Wire the new router in [main.py](backend/openstars/server/main.py).

Unit tests in this step (`backend/tests/server/test_race_routes.py`):

- [x] `POST /race/preview` returns the cost breakdown without persisting and without requiring a game id.
- [x] `POST /race/preview` on an overspent race returns 400 `RACE_OVERSPENT`.
- [x] `POST /race/preview` on a non-JOAT race returns 400 `RACE_PRT_NOT_AVAILABLE`.
- [x] `GET /games/{id}/race` returns `null` before any submission and the saved race after.
- [x] `GET /games/{id}/race` for a non-player returns 403.
- [x] `GET /race/predefined` returns Humanoid only.

---

## Step 7 — Bare `T=0` state and turn-0 resolution

`create_initial_state` is gutted: at game creation it produces only the bare `T=0` state, with no home-planet assignment, no ownership on any planet, no installations, no starting designs, and no fleets. The bulk of its current logic — `_assign_home_planets`, the home-planet concentration floor, `is_homeworld`, the starbase, designs and fleets — moves to `resolve_turn_zero` in this step.

- [x] In [create_game.py](backend/openstars/engine/create_game.py), reduce `create_initial_state` to:
  - Construct each `Player(username, name, race=None, research_state=default_research_state())`.
  - Build `PlanetState` for every galaxy planet with random concentrations and random habitability, `owner=None`, `is_homeworld=False`, no installations, no minerals, no starbase.
  - Return `(global_state, [])` — no starting designs.
- [x] Move `_assign_home_planets` (and its helpers) from this module to `backend/openstars/engine/resolve_steps/turn_zero.py`. The seeded RNG offsets used here continue to apply when called from turn-0 resolution.
- [x] Move the starting-fleet builder (today's inline four-fleet construction in `create_initial_state`) to `turn_zero.py` as well.
- [x] [routes/games.py](backend/openstars/server/routes/games.py) still calls `create_initial_state` once at game creation, then persists the bare `T=0` state, the galaxy, and metadata. It no longer calls `seed_player_design_registry` here — that moves into the turn-0 resolution path.
- [x] `GameMeta.turn = 0` is unchanged. The first proper turn becomes `T=1` after turn-0 resolution.

The turn-0 resolution path is structurally a normal `resolve_turn`, but only one resolve step runs: a brand-new `resolve_turn_zero` step. It executes only when `ctx.global_state.game.turn == 0`. All the homeworld / design / fleet seeding that used to live in `create_initial_state` runs here.

New module: `backend/openstars/engine/resolve_steps/turn_zero.py`. Lifts `_assign_home_planets` and the starting-fleet builder from `create_game.py`.

- [x] `def resolve_turn_zero(ctx: TurnContext, all_commands: dict[str, PlayerCommands], storage: GameStorage) -> None`:
  - **Phase 1 — galaxy-wide setup, runs once.**
    1. Compute home-planet assignments using the seeded `_assign_home_planets(galaxy, num_players, game_seed)` algorithm (the function moves here from `create_game.py`).
    2. For each assigned home planet: set `owner = username`, `is_homeworld = True`, and clamp `concentrations` to a minimum of 30 per mineral type.
  - **Phase 2 — per-player materialisation, alphabetical username order.**
    1. **Re-validate.** Resolve the player's last `select_race` command from `all_commands[username]` via `apply_select_race_command` — which calls `validate_race(...)` and writes into `ctx.race_by_username[username]`. If a player has no `select_race` command, raise `TURN_ZERO_INCOMPLETE`; if validation fails because constants drifted, raise `RACE_REVALIDATION_FAILED` for that player.
    2. **Snapshot.** No additional snapshot step is needed beyond `apply_select_race_command`; `build_result` writes `ctx.race_by_username` back onto `Player.race`.
    3. **Locate the home planet** assigned to this player in Phase 1.
    4. **Set ideal habitability** for non-immune factors. For each of `gravity`, `temperature`, `radiation`: if `race.habitability.<factor>.immune == True`, leave the planet's value as-is (random from game-start); else set it to `floor((low + high) / 2)`.
    5. **Set starting population.** `25_000`.
    6. **Set installations.** `mines = 10`, `factories = 10`.
    7. **Set starting minerals.** `Minerals(ironium=300, boranium=300, germanium=300)`.
    8. **Build starbase.** `PlanetStarbaseState(type="space_station", can_build_ships=True)`.
    9. **Seed starting designs.** Build Scout / SmallFreighter / ColonyShip designs (logic lifted from `create_initial_state`) and persist them via `seed_player_design_registry(storage, game_id, designs)`.
    10. **Seed starting fleets.** Build the four starting fleets (today's inline four-fleet construction, lifted from `create_initial_state`) into `ctx.fleets`.
    11. **Emit `race.saved` event** with `values=[race.prt]` and `source_id=None` to the player's per-turn event log.
- [x] Update [resolve.py](backend/openstars/engine/resolve.py) `resolve_turn`:
  - If `global_state.game.turn == 0`, call `resolve_turn_zero(ctx, all_commands, storage)` and skip every other resolve step (movement, combat, mining, resources, production, research, population). The standard pipeline starts at `T=1`.
  - The build_result still increments `turn` to 1.
- [x] Test helper: new `backend/tests/engine/race/_helpers.py`:
  - `def submit_default_race_and_resolve_turn_0(global_state, galaxy, storage, usernames) -> GlobalState` — builds a fake turn-0 commands set with `{predefined_id: "humanoid"}` per player, runs `resolve_turn`, returns the resulting `T=1` state. The designs registry is seeded into `storage` as a side-effect; tests that need the designs read them back via `storage.load_design_registry(game_id)`.
- [x] Player-state derivation at `T=0` returns a deliberately empty command-phase state: `PlayerState.race is None`, all planets are name/coordinates only with `scan_level="none"`, `fleets=[]`, `designs=[]`, `events=[]`, and `research=None`. Once `T=0` resolves, normal fog-of-war derivation resumes from `T=1`.

Unit tests in this step (`backend/tests/engine/race/test_turn_zero_resolution.py`):

- [x] `create_initial_state` produces a `GlobalState` with every player having `race is None`.
- [x] No planet has `is_homeworld=True` and no planet has an `owner`.
- [x] Every planet has random environment values and random concentrations (no home-planet floor of 30 is applied yet).
- [x] The returned `designs` list is empty.
- [x] `GlobalState.fleets` is empty.
- [x] `derive_player_state` for a fresh `T=0` state returns the deliberately empty command-phase shape described above.
- [x] After `resolve_turn` on a fresh `T=0` state where every player has submitted Humanoid, the resulting `T=1` state has:
  - `Player.race` set to the Humanoid preset for every player.
  - One home planet per player: `is_homeworld=True`, `owner == username`, `population == 25_000`, `mines == 10`, `factories == 10`, `minerals == Minerals(300, 300, 300)`, starbase populated, concentrations floored at 30.
  - Each home planet's habitability is exactly `(50, 50, 50)` — Humanoid ideals.
  - One `race.saved` event per player.
  - Three starting designs per player in the design registry; four starting fleets per player in `GlobalState.fleets`.
- [x] A custom race with `gravity.immune=True` leaves the home planet's gravity at the random game-start value; temperature and radiation are set to ideal.
- [x] A custom race with shifted ideal `temperature.range=(40, 60)` results in homeworld `temperature == 50` (midpoint).
- [x] When one player has not submitted a `select_race` command, `resolve_turn_zero` raises `TURN_ZERO_INCOMPLETE`. (The /resolve route surfaces this — Step 8.)
- [x] `resolve_turn` on `T=1` (or higher) does not call `resolve_turn_zero`; it runs the standard pipeline.
- [ ] A regression test freezes a known seed and asserts the full resulting `T=1` state byte-for-byte against a saved fixture.
- [x] Existing tests that asserted `population == 25_000` at game-start migrate to call the test helper from this step.

---

## Step 8 — Turn-0 phase enforcement and submit-time race validation

Wire phase rejections and submit-time race validation into the play route. Race selection is submitted via `POST /commands` carrying a `SelectRaceCommand` — this step makes that path enforce phase rules and surface the structured race-validation error codes synchronously.

- [x] In [play.py](backend/openstars/server/routes/play.py) `POST /commands`:
  - If `current_turn == 0`, every command in the submission must be a `SelectRaceCommand`. Any other type returns 400 `COMMAND_TURN_ZERO_RACE_ONLY` (with `detail` naming the offending type).
  - For each `SelectRaceCommand` in the submission: resolve `predefined_id` via `PREDEFINED_RACES` and run `validate_race(race)` at submit time. `RaceValidationError` becomes 400 with the corresponding code (`RACE_OVERSPENT`, `RACE_PRT_NOT_AVAILABLE`, `RACE_LRT_NOT_AVAILABLE`, `RACE_BONUS_NOT_AVAILABLE`, `RACE_INVALID_BONUS`); `PREDEFINED_RACE_UNKNOWN` becomes 404. Validation also runs at resolve time (Step 7) to catch drift between submit and resolve.
  - At `current_turn >= 1`, a `SelectRaceCommand` in the submission returns 400 `COMMAND_NOT_VALID_AT_THIS_TURN`.
- [x] In [play.py](backend/openstars/server/routes/play.py) `POST /resolve`:
  - If `current_turn == 0`, before invoking `resolve_turn`, check that every player listed in `meta["players"]` has a saved `SelectRaceCommand` in their `commands-T0-<username>.json`. If any player is missing, return 409 `TURN_ZERO_INCOMPLETE` with `detail` listing the missing usernames.
  - If `resolve_turn_zero` raises `RACE_REVALIDATION_FAILED` for any player (cost constants drift between submission and resolve), return 409 `RACE_REVALIDATION_FAILED` with the affected username(s); the resolution does not partially apply.

Unit tests in this step (extend `backend/tests/server/test_play_route.py` or analogous):

- [x] At `T=0`, a `POST /commands` payload containing a `set_research` command returns 400 `COMMAND_TURN_ZERO_RACE_ONLY`.
- [x] At `T=0`, a `POST /commands` payload containing only a `select_race` command with `{predefined_id: "humanoid"}` is accepted (writes through to the on-disk commands).
- [x] At `T=0`, a `POST /commands` carrying a `SelectRaceCommand` with an overspent custom race returns 400 `RACE_OVERSPENT`.
- [x] At `T=0`, a `POST /commands` carrying a `SelectRaceCommand` with serialised `prt="HE"` returns 400 `RACE_PRT_NOT_AVAILABLE`.
- [x] At `T=0`, a `POST /commands` carrying `{predefined_id: "rabbitoid"}` returns 404 `PREDEFINED_RACE_UNKNOWN`.
- [x] At `T=1`, a `POST /commands` payload with `set_research` is accepted; a `select_race` command at `T=1` is rejected with 400 `COMMAND_NOT_VALID_AT_THIS_TURN`.
- [x] `POST /resolve` at `T=0` with one player having no race submission returns 409 `TURN_ZERO_INCOMPLETE` and lists that player's username.
- [x] `POST /resolve` at `T=0` with all players submitting Humanoid succeeds and produces a `T=1` state.
- [x] `GET /turn-status` at `T=0` includes `playersAwaitingRace` with every player who has not saved a `select_race` command; after all players submit, the list is empty.
- [x] `GET /games` and `GET /games/{game_id}` treat a saved `select_race` command as the player's T0 submission for `all_turns_submitted` / `submitted` status.
- [x] At `T>=1`, `GET /turn-status`, `GET /games`, and `GET /games/{game_id}` keep their existing normal-turn submission semantics.

---

## Step 9 — Frontend turn-0 race-selection screen

Minimal UI surfacing the dedicated turn-0 phase.

The detection is server-driven: when the frontend fetches `/games/{id}/state`, if `current_turn == 0` and the viewer's `PlayerState.race == null`, render the `<RaceSelectionScreen />` instead of the normal galaxy/play layout. Once the viewer's race is saved, show a "waiting for other players" indicator. Once all players have submitted, the host's resolve button is enabled.

- [ ] New component: `frontend/src/components/RaceSelectionScreen.tsx`. Top-level shape:
  - **Preset picker** — single button for `Humanoid (JOAT)`. (Future presets are listed but disabled with "Coming soon" tooltips.)
  - **Custom race form** — a vertically stacked form covering:
    - Identity: `name`, `pluralName`, `emblem` (number input 0–31).
    - Habitability: three rows for gravity / temperature / radiation, each with `immune` checkbox and two number inputs for the low/high range.
    - Growth: `maxGrowthRate` slider 1–20.
    - Economy: eight number inputs with the documented ranges as `min`/`max`/`step`, plus a `factoriesSaveGermanium` toggle.
    - Research: six rows (one per field) with a three-button radio for `cheap | standard | expensive`, plus a `startAtTech3` toggle.
    - Leftover bonus: omitted from the UI — the field stays `null` server-side.
  - **Live cost preview** — calls `POST /api/v1/race/preview` debounced (250ms) on every edit. Renders `pointsLeft` prominently and the per-section breakdown below. Disables the "Save" button when `pointsLeft < 0`.
  - **Save button** — submits a `SelectRaceCommand` (`{type: "select_race", predefinedId, race}`) via the existing commands client (`POST /api/v1/games/{gameId}/commands`) and on success transitions to a "waiting" state. Surfaces the structured 400s from Step 8 (`RACE_OVERSPENT`, `RACE_PRT_NOT_AVAILABLE`, etc.) as inline errors.
  - **Cancel/reset** — reverts to the last saved selection (or the Humanoid preset if nothing saved).
- [ ] New API client functions in [client.ts](frontend/src/api/client.ts):
  - `previewRace(race): Promise<RaceCostBreakdown>`.
  - `getRace(gameId): Promise<{ race; costBreakdown } | null>`.
  - `getPredefinedRaces(): Promise<Array<{ id; race }>>`.
  - All converted via `keysToCamel` / `keysToSnake` per the existing API conventions. Race submission re-uses the existing commands client; no new save function.
- [ ] New types in `frontend/src/api/types.ts` (or wherever API types live): mirror the server-side `Race`, `RaceHabitability`, `RaceHabitabilityFactor`, `RaceEconomy`, `RaceResearch`, `LeftoverBonus`, `RaceCostBreakdown` shapes in camelCase.
- [ ] Routing in [App.tsx](frontend/src/App.tsx) — when the viewer's `playerState.race == null` and `currentTurn == 0`, render `<RaceSelectionScreen />` as the only top-level content. Preserve the topbar and any cross-cutting chrome.
- [ ] "Waiting for other players" indicator — read from a new field on the existing turn-status response. Server change: `GET /games/{id}/turn-status` adds `playersAwaitingRace: string[]` for `T=0` only. Frontend renders this list under the form once the viewer has saved.
- [ ] Host's resolve button gating: at `T=0`, the existing "End turn" / "Resolve" button shows as disabled with a tooltip naming the missing players when `playersAwaitingRace.length > 0`. When all players have submitted, it becomes the "Begin game" button and triggers `/resolve`.

Unit tests in this step (`frontend/src/components/RaceSelectionScreen.test.tsx` and `frontend/src/api/client.test.ts`):

- [ ] Selecting the Humanoid preset and clicking Save calls the commands client with a single `{type: "select_race", predefinedId: "humanoid"}` command.
- [ ] Editing a custom race triggers a debounced `previewRace` call after 250ms.
- [ ] When the preview returns `pointsLeft < 0`, the Save button is disabled.
- [ ] An overspent submission surfacing 400 `RACE_OVERSPENT` from the server displays the corresponding inline error.
- [ ] Setting `gravity.immune = true` disables the gravity range inputs.
- [ ] After a successful save, the screen transitions to the "waiting" state and `getRace` is called on remount to rehydrate.
- [ ] When `playersAwaitingRace` becomes empty for the host, the "Begin game" button is enabled.

---

## Step 10 — Backend lint, format, test

- [ ] `cd backend && uv run ruff check .` clean.
- [ ] `cd backend && uv run ruff format --check .` clean.
- [ ] `cd backend && uv run pytest` passes end-to-end.

---

## Step 11 — Frontend lint, typecheck, test

- [ ] `cd frontend && npm run lint` clean.
- [ ] `cd frontend && npm run typecheck` clean.
- [ ] `cd frontend && npm test` passes.

---

## Step 12 — Integration test

Full-stack coverage through the HTTP API. New file: `backend/int_tests/test_race_selection.py`.

- [x] **Scenario A — preset selection flow.**
  - Create a two-player game; assert `current_turn == 0`, `PlayerState.race == null`, `fleets == []`, `designs == []`, and every planet is name/coordinates only with no owner, population, installations, or starbase detail via `GET /games/{id}/state` for each player.
  - Player A: `POST /games/{id}/commands` with `[{type: "select_race", predefined_id: "humanoid"}]` returns 200.
  - Player B: same.
  - `GET /games/{id}/race` for Player A returns the saved Humanoid record with `points_left == 1650`.
  - `POST /games/{id}/resolve` returns 200 and produces `T=1`.
  - Assert each home planet has `population == 25_000`, `mines == 10`, `factories == 10`, `starbase != null`, `habitability == (50, 50, 50)`.
  - Assert each player has a `race.saved` event in their `T=0→T=1` event log.
- [x] **Scenario B — custom race round-trip.**
  - Create a single-player game.
  - `POST /race/preview` with a deliberately extreme custom race returns 400 `RACE_OVERSPENT`; use a combination that clearly exceeds the 1650-point budget (for example 20% growth, all six fields `cheap`, `colonists_per_resource = 700`, `factory_output_per_10 = 15`, `factory_cost_resources = 5`, `mine_output_per_10 = 25`, and `mine_cost_resources = 2`). Do not use `colonists_per_resource = 900` alone as the overspend proof: it is only a ~200-point move against a 1650-point budget.
  - `POST /race/preview` with `colonists_per_resource = 900` and enough compensating downgrades (for example `factory_output_per_10 = 9` plus other low-impact point-return settings if needed after calibration) returns 200 with `points_left >= 0`.
  - `POST /games/{id}/commands` with `[{type: "select_race", race: <that body>}]` persists; subsequent `GET /games/{id}/race` returns it.
  - Resolve; assert the resulting `T=1` planet's population matches `25_000` and the player's `race.economy.colonists_per_resource == 900`.
- [x] **Scenario C — phase enforcement.**
  - Create a two-player game.
  - Player A submits Humanoid via `POST /games/{id}/commands` with `[{type: "select_race", predefined_id: "humanoid"}]`.
  - Player A then attempts to submit a `set_research` command via `POST /commands` at `T=0` — assert HTTP 400 `COMMAND_TURN_ZERO_RACE_ONLY`.
  - Host attempts `POST /resolve` while Player B has no race submission — assert HTTP 409 `TURN_ZERO_INCOMPLETE` with Player B in the detail.
  - Player B submits Humanoid; `POST /resolve` succeeds.
  - At `T=1`, Player A attempts another `select_race` command via `POST /games/{id}/commands` — assert HTTP 400 `COMMAND_NOT_VALID_AT_THIS_TURN`.
- [x] **Scenario D — economy plumbing.**
  - Single-player game; player submits a custom Humanoid-shape race with `factory_output_per_10 = 12` (more output per factory, costs ≈ +83 vs default).
  - Resolve `T=0`; resolve `T=1` (no commands needed beyond the implicit pop/economy run).
  - Assert the player's planet `total_resources` at `T=1→T=2` reflects the higher factory output: `pop_resources = floor(25_000 / 1000) = 25`, `factory_resources = floor(10 * 12 / 10) = 12`, total = `37` (vs `35` for default). Cross-checked against `GET /state.planet.resources` if exposed; otherwise assert the production budget consumed across two turns.

---

## Explicitly out of scope

- **Other PRTs** — HE / SS / WM / CA / IS / SD / PP / IT / AR. Schema reserves the enum values; validator rejects them. Combat-side PRT effects are owned by the combat PRDs anyway.
- **Lesser racial traits** — all 14 LRTs. Schema reserves the enum values; validator rejects any non-empty `lrts`.
- **Leftover bonuses** — `surface_minerals`, `mines`, `factories`, `defenses`, `concentrations`. Schema reserves the field as nullable; validator rejects any non-null value.
- **Other predefined races** — Insectoid, Rabbitoid, Nucleotid, Silicanoid, Antethereal. Only Humanoid is registered.
- **AR-specific economy formula** — `ar_resource_divisor` ships on the schema but is unused (no AR PRT).
- **Engine consumption of the research cost profile and `start_at_tech_3`** — values are stored on the race and counted in the points budget but not yet consumed by the research engine. PRD 21 cross-update is deferred.
- **Population cap factors** (HE 0.5, JOAT 1.2, AR 0) — the factor is always 1.0 for now.
- **Two-homeworld PRTs (PP / IT)** — single-homeworld JOAT only.
- **Polished six-step custom-race wizard UI** — the form ships as a flat layout for now.
- **Account-level race library and lobby-side race design** — deferred. The `select_race` command payload is shaped so a future `account_race_id` input is purely additive.
- **Turn-0 timer / forced default on timeout** — no timer; host triggers `/resolve` once everyone has submitted.
- **Trait-detection intel for opposing races** — only the viewer's own `race` is exposed in `PlayerState`. Public fields on opposing players are not yet projected; that lands when the multi-player intel surface is built out.
