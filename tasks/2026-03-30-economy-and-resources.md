# Economy & Resources (PRD 12)

Implements the planetary economy simulation: minerals, concentrations, mines, factories, and resources. This is the foundational production system.

## Scope

Backend engine only (no frontend UI changes required — the planet detail panel already exists but economy fields will be wired up when the data is available). UI notes in PRD 12 are deferred.

---

## Step 1: Extend models (`models.py`) ✅

Add the `Minerals` shared model and extend `PlanetState` and `PlayerPlanet`.

- [x] Add `Minerals` model with `ironium`, `boranium`, `germanium` fields (all `int = 0`)
- [x] Extend `PlanetState` with:
  - `mines: int = 0`
  - `factories: int = 0`
  - `minerals: Minerals = Field(default_factory=Minerals)`
  - `concentrations: Minerals = Field(default_factory=Minerals)`
  - `mine_years: Minerals = Field(default_factory=Minerals)`
  - `is_homeworld: bool = False`
- [x] Extend `PlayerPlanet` with optional economy fields:
  - `mines: int | None = None`
  - `factories: int | None = None`
  - `minerals: Minerals | None = None`
  - `concentrations: Minerals | None = None`
  - `resources: int | None = None`
  - `mining_rate: Minerals | None = None`
- [x] Add `mining_complete` event fields to `GameEvent`:
  - The existing `type` field covers the event type string
  - Add `ironium: int | None = None`, `boranium: int | None = None`, `germanium: int | None = None` to `GameEvent`
- [x] Move `GameEvent` before `GlobalState` and add `events: dict[str, list[GameEvent]]` to `GlobalState`

---

## Step 2: Economy constants (`economy.py`) ✅

Create `backend/openstars/engine/economy.py` with the race economy defaults and the pure calculation functions.

- [x] Define race economy constants (JOAT defaults from PRD 12)
- [x] `mines_operated(mines: int, population: int) -> int`
- [x] `factories_operated(factories: int, population: int) -> int`
- [x] `mine_minerals(mines_op: int, concentrations: Minerals) -> Minerals`
- [x] `deplete_concentrations(planet: PlanetState, mines_op: int, min_conc: int) -> tuple[Minerals, Minerals]`
- [x] `calculate_resources(population: int, factories_op: int) -> tuple[int, int, int]`
- [x] `mining_rate(mines_op: int, concentrations: Minerals) -> Minerals`

---

## Step 3: Turn 0 generation (`setup.py`) ✅

Extend `create_initial_state` to set concentrations and home planet economy.

- [x] Pass `game_seed` into a local seeded RNG (`random.Random(game_seed ^ _ECON_SEED_OFFSET)`) to generate concentrations, using offset `0xEC0_5EED` to avoid coupling with galaxy's SHA-256 RNG
- [x] For each planet in the galaxy:
  - Generate `concentrations` — each mineral type: `rng.randint(1, 200)`
  - If home planet: clamp each concentration to `max(value, 30)`
- [x] For home planets, set `mines=10`, `factories=10`, `minerals=Minerals(300,300,300)`, `mine_years=Minerals()`, `is_homeworld=True`
- [x] All other planets: defaults (mines=0, factories=0, minerals all 0, is_homeworld=False)

---

## Step 4: Mining & resource steps (`resolve.py`) ✅

Insert Steps 3 and 4 into the resolution pipeline, shifting the turn increment.

- [x] Import `economy` module and `Minerals`/`PlanetState`/`GameEvent` models
- [x] After fleet movement (Step 2), add **Step 3: Mining** — for each planet sorted by ID
- [x] After mining, add **Step 4: Calculate Resources** — store in `planet_resources` dict
- [x] Pass `events` and `planet_resources` into `GlobalState` output (added `planet_resources: dict[str, int]` to `GlobalState`)
- [x] Update turn counter (Step 5, was Step 3)

---

## Step 5: Fog of war (`fog.py`) ✅

Extend `derive_player_state` to include economy fields at the appropriate scan level.

- [x] For **own planets** (`is_own = True`), include `mines`, `factories`, `minerals`, `concentrations`, `resources`, `mining_rate`
- [x] For **detailed scan**, include same economy fields
- [x] For **basic** and **none** scan levels: no economy fields (remain `None`)
- [x] Include `mining_complete` events from `global_state.events[username]` in the player's `events` list
- [x] Reads `planet_resources` from `global_state.planet_resources` (no signature change needed)

---

## Step 6: Tests (`tests/engine/test_economy.py`) ✅

Cover the pure functions in `economy.py` and integration behaviour in `resolve.py` / `setup.py`.

- [x] All 12 pure unit tests for `economy.py`
- [x] All 9 integration tests (setup, resolve, fog)
- [x] 21 new tests, 140 total passing

---

## Step 7: Lint and format ✅

- [x] `cd backend && uv run ruff check .` — clean
- [x] `cd backend && uv run ruff format --check .` — clean (2 files auto-formatted: `economy.py`, `resolve.py`)

---

## Step 8: Run all tests ✅

- [x] `cd backend && uv run pytest` — 140 passed

---

## Notes

- `mine_years` and `is_homeworld` are internal engine fields — never exposed in `PlayerPlanet`
- Resources are not stockpiled; they are generated and consumed within the same turn. Until the production queue PRD is implemented, `resources` is display-only (included in `PlayerPlanet` for the UI)
- Concentration depletion is **independent of mining efficiency** — the depletion algorithm uses `mines_operated` directly, not the yield
- The `mining_complete` event includes planet name (look up from galaxy) and mined amounts per mineral type
