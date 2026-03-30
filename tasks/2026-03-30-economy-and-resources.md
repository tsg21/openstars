# Economy & Resources (PRD 12)

Implements the planetary economy simulation: minerals, concentrations, mines, factories, and resources. This is the foundational production system.

## Scope

Backend engine only (no frontend UI changes required — the planet detail panel already exists but economy fields will be wired up when the data is available). UI notes in PRD 12 are deferred.

---

## Step 1: Extend models (`models.py`) ✅ [ ]

Add the `Minerals` shared model and extend `PlanetState` and `PlayerPlanet`.

- [ ] Add `Minerals` model with `ironium`, `boranium`, `germanium` fields (all `int = 0`)
- [ ] Extend `PlanetState` with:
  - `mines: int = 0`
  - `factories: int = 0`
  - `minerals: Minerals = Field(default_factory=Minerals)`
  - `concentrations: Minerals = Field(default_factory=Minerals)`
  - `mine_years: Minerals = Field(default_factory=Minerals)`
  - `is_homeworld: bool = False`
- [ ] Extend `PlayerPlanet` with optional economy fields:
  - `mines: int | None = None`
  - `factories: int | None = None`
  - `minerals: Minerals | None = None`
  - `concentrations: Minerals | None = None`
  - `resources: int | None = None`
  - `mining_rate: Minerals | None = None`
- [ ] Add `mining_complete` event fields to `GameEvent`:
  - The existing `type` field covers the event type string
  - Add `ironium: int | None = None`, `boranium: int | None = None`, `germanium: int | None = None` to `GameEvent`

---

## Step 2: Economy constants (`economy.py`) ✅ [ ]

Create `backend/openstars/engine/economy.py` with the race economy defaults and the pure calculation functions.

- [ ] Define race economy constants (JOAT defaults from PRD 12):
  ```python
  COLONISTS_PER_RESOURCE = 1000
  FACTORY_RATE = 1.0
  FACTORY_COST_RESOURCES = 10
  FACTORY_COST_GERMANIUM = 4
  FACTORIES_PER_10K = 10
  MINE_RATE = 1.0
  MINE_COST_RESOURCES = 5
  MINES_PER_10K = 10
  ```
- [ ] `mines_operated(mines: int, population: int) -> int` — `min(mines, floor(population / 10000) * MINES_PER_10K)`
- [ ] `factories_operated(factories: int, population: int) -> int` — analogous
- [ ] `mine_minerals(mines_op: int, concentrations: Minerals) -> Minerals` — per-type: `floor(mines_op * MINE_RATE * conc / 100)`
- [ ] `deplete_concentrations(planet: PlanetState, mines_op: int, min_conc: int) -> tuple[Minerals, Minerals]` — returns updated `(concentrations, mine_years)` after applying the while-loop depletion algorithm per mineral type
- [ ] `calculate_resources(population: int, factories_op: int) -> tuple[int, int, int]` — returns `(pop_resources, factory_resources, total_resources)`
- [ ] `mining_rate(mines_op: int, concentrations: Minerals) -> Minerals` — same formula as `mine_minerals` (convenience for player state display)

---

## Step 3: Turn 0 generation (`setup.py`) ✅ [ ]

Extend `create_initial_state` to set concentrations and home planet economy.

- [ ] Pass `game_seed` into a local seeded RNG (use `random.Random(game_seed)` — same pattern as galaxy generation) to generate concentrations
- [ ] For each planet in the galaxy:
  - Generate `concentrations` — each mineral type: `rng.randint(1, 200)`
  - If home planet: clamp each concentration to `max(value, 30)`
- [ ] For home planets, set:
  - `mines = 10`, `factories = 10`
  - `minerals = Minerals(ironium=300, boranium=300, germanium=300)`
  - `mine_years = Minerals()` (all zero)
  - `is_homeworld = True`
  - `concentrations` already clamped above
- [ ] All other planets: `mines=0, factories=0, minerals=Minerals(), mine_years=Minerals(), is_homeworld=False`
- [ ] Update `PlanetState` construction in `create_initial_state` accordingly

**Note on RNG:** Check how `galaxy.py` seeds its RNG to ensure the approach is consistent. Use a distinct seed offset if needed to avoid sequence coupling (e.g. `random.Random(game_seed ^ 0xECON_SEED)`). Check PRD 04 for guidance on determinism.

---

## Step 4: Mining & resource steps (`resolve.py`) ✅ [ ]

Insert Steps 3 and 4 into the resolution pipeline, shifting the turn increment.

- [ ] Import `economy` module and `Minerals` model
- [ ] After fleet movement (Step 2), add **Step 3: Mining** — for each planet sorted by ID:
  - Skip if `planet.owner is None` or `planet.mines == 0`
  - `mines_op = economy.mines_operated(planet.mines, planet.population)`
  - `mined = economy.mine_minerals(mines_op, planet.concentrations)`
  - Add `mined` to `planet.minerals` (per field)
  - `new_concs, new_mine_years = economy.deplete_concentrations(planet, mines_op, min_conc)`
    - `min_conc = 30 if planet.is_homeworld else 1`
  - Update `planet.concentrations` and `planet.mine_years`
  - Append a `mining_complete` event to a per-owner event list
- [ ] After mining, add **Step 4: Calculate Resources** — for each planet with owner:
  - `factories_op = economy.factories_operated(planet.factories, planet.population)`
  - `_, _, total = economy.calculate_resources(planet.population, factories_op)`
  - Store `total` in a `planet_resources` dict (keyed by planet ID) for use during player state derivation
- [ ] Pass accumulated events and `planet_resources` through to `GlobalState` output (events are per-player, collate by owner; resources are transient — pass separately or store on the planet temporarily)
- [ ] Update turn counter (Step 5, was Step 3)

**Design note:** `resolve_turn` currently returns only `GlobalState`. Economy events need to reach `derive_player_state`. Options:
- (a) Add an `events: dict[str, list[GameEvent]]` field to `GlobalState` (simplest, clean)
- (b) Return a separate events dict alongside `GlobalState`

Option (a) is preferred — it keeps the state self-contained and the field can be cleared each turn. Add `events: dict[str, list[GameEvent]] = Field(default_factory=dict)` to `GlobalState`.

---

## Step 5: Fog of war (`fog.py`) ✅ [ ]

Extend `derive_player_state` to include economy fields at the appropriate scan level.

- [ ] For **own planets** (`is_own = True`), include:
  - `mines`, `factories`, `minerals`, `concentrations`
  - `resources` (look up from `planet_resources` dict passed through)
  - `mining_rate` (compute from `mines_op` and `concentrations`)
- [ ] For **detailed scan** (enemy planet in penetrating range), include:
  - Same economy fields as own planets
- [ ] For **basic** and **none** scan levels: no economy fields (remain `None`)
- [ ] Include `mining_complete` events from `global_state.events[username]` in the player's `events` list
- [ ] Update `derive_player_state` signature if needed to accept `planet_resources` dict (or read from `GlobalState` if stored there)

---

## Step 6: Tests (`tests/engine/test_economy.py`) ✅ [ ]

Cover the pure functions in `economy.py` and integration behaviour in `resolve.py` / `setup.py`.

### `test_economy.py` — pure unit tests
- [ ] `test_mines_operated_capped_by_population` — more mines than pop can operate → capped
- [ ] `test_mines_operated_uncapped` — mines < max → returns mines
- [ ] `test_mine_minerals_at_concentration_100` — output = mines_op × MINE_RATE
- [ ] `test_mine_minerals_scales_with_concentration` — concentration 50 → half output
- [ ] `test_mine_minerals_floors_result` — fractional output is floored
- [ ] `test_deplete_concentration_basic` — after enough mine-years, concentration drops by 1
- [ ] `test_deplete_concentration_homeworld_floor` — never drops below 30
- [ ] `test_deplete_concentration_normal_floor` — never drops below 1
- [ ] `test_deplete_threshold_recalculates` — threshold updates as concentration drops
- [ ] `test_calculate_resources_pop_only` — no factories → resources = pop / colonists_per_resource
- [ ] `test_calculate_resources_with_factories` — factories add to resource output
- [ ] `test_factories_operated_capped` — analogous to mines_operated

### Integration tests extending `test_resolve.py` / `test_setup.py`
- [ ] `test_setup_home_planet_has_concentrations` — home planet concentrations all ≥ 30
- [ ] `test_setup_other_planets_have_concentrations` — concentrations in [1, 200]
- [ ] `test_setup_home_planet_economy` — mines=10, factories=10, minerals=300/300/300
- [ ] `test_resolve_mining_step` — one turn with mines on home planet → surface minerals increase
- [ ] `test_resolve_mining_depletes_concentration` — enough turns → concentration drops
- [ ] `test_resolve_mining_events_generated` — `mining_complete` events appear in player state
- [ ] `test_resolve_resources_in_player_state` — `resources` field is populated for own planets
- [ ] `test_fog_economy_detailed_scan` — enemy planet in penetrating range shows economy data
- [ ] `test_fog_economy_basic_scan` — enemy planet in basic range hides economy data

---

## Step 7: Lint and format ✅ [ ]

- [ ] `cd backend && uv run ruff check .`
- [ ] `cd backend && uv run ruff format --check .`
- [ ] Fix any lint/format errors

---

## Step 8: Run all tests ✅ [ ]

- [ ] `cd backend && uv run pytest` — all tests pass

---

## Notes

- `mine_years` and `is_homeworld` are internal engine fields — never exposed in `PlayerPlanet`
- Resources are not stockpiled; they are generated and consumed within the same turn. Until the production queue PRD is implemented, `resources` is display-only (included in `PlayerPlanet` for the UI)
- Concentration depletion is **independent of mining efficiency** — the depletion algorithm uses `mines_operated` directly, not the yield
- The `mining_complete` event includes planet name (look up from galaxy) and mined amounts per mineral type
