# Population & Habitability (PRD 14)

Implements planet environment values, habitability calculation, and per-turn population growth and death.

## Scope

Backend engine only. No frontend UI changes required — the planet detail panel already exists but population fields will be wired up when the data is available. UI notes in PRD 14 are deferred.

---

## Step 1: Extend models (`models.py`)

Add the `Habitability` type and extend `PlanetState`, `PlayerPlanet`, and `GameEvent`.

- [x] Add `Habitability` model with `gravity: int = 0`, `temperature: int = 0`, `radiation: int = 0` fields
- [x] Extend `PlanetState` with:
  - `habitability: Habitability = Field(default_factory=Habitability)`
- [x] Extend `PlayerPlanet` with optional fields:
  - `habitability: Habitability | None = None`
  - `max_population: int | None = None`
  - `pop_growth: int | None = None`
- [x] Add `colonists_died` and `planet_abandoned` event types to `GameEvent`:
  - `deaths: int | None = None`
  - `cause: str | None = None`

---

## Step 2: Population constants and calculations (`population.py`)

Create `backend/openstars/engine/population.py` with race defaults and pure calculation functions.

- [x] Define JOAT race habitability defaults:
  - `GRAVITY_RANGE = (15, 85)`
  - `TEMPERATURE_RANGE = (15, 85)`
  - `RADIATION_RANGE = (15, 85)`
  - `MAX_GROWTH_RATE = 0.15`
  - `BASE_MAX_POPULATION = 1_000_000`
- [x] `factor_contribution(v: int, low: int, high: int) -> float` — per-factor habitability score (see PRD 14 formula)
- [x] `calculate_hab_value(hab: Habitability) -> int` — sum of three factor contributions, rounded to int, using JOAT defaults
- [x] `max_population(hab: Habitability) -> int` — applies 5% floor for positive values; returns 0 for negative
- [x] `population_growth(population: int, hab: Habitability) -> int` — logistic growth formula; returns delta (positive)
- [x] `population_death(population: int, hab: Habitability) -> int` — hostile environment death; returns delta (positive = deaths)
- [x] `overcrowding_deaths(population: int, max_pop: int) -> int` — overcrowding death rate up to 12%

---

## Step 3: Turn 0 generation (`setup.py`)

Extend `create_initial_state` to generate environment values for all planets.

- [x] Use a seeded RNG with offset `0xAB_5EED` (distinct from economy's `0xEC0_5EED`) to avoid coupling
- [x] For each non-home planet: generate each of `gravity`, `temperature`, `radiation` as `rng.randint(0, 100)`
- [x] For home planets: set `gravity=50, temperature=50, radiation=50` (JOAT ideal — override random draw)

---

## Step 4: Population growth/death step (`resolve.py`)

Insert Step 6 (population) into the resolution pipeline after production.

- [x] After production (Step 5), add **Step 6: Population growth / death** — for each planet sorted by ID with `owner != null`:
  - Compute `max_pop` using `max_population(planet.habitability)`
  - If `calculate_hab_value(planet.habitability) >= 0`: apply `population_growth`; cap at `max_pop`
  - If `calculate_hab_value(planet.habitability) < 0`: apply `population_death`; if population reaches 0, set `owner = None` and emit `planet_abandoned` event
  - Apply `overcrowding_deaths` if `population > max_pop`
  - Store `pop_growth` delta (net change) for fog-of-war output
  - Emit `colonists_died` event when deaths > 0
- [x] Update turn counter (Step 7)
- [x] Add `pop_growth: dict[str, int]` to `GlobalState` for fog-of-war consumption

---

## Step 5: Fog of war (`fog.py`)

Extend `derive_player_state` to include population and habitability fields at the appropriate scan levels.

- [x] For `detailed` scan and own planets: include `habitability` (raw object)
- [x] For own planets only: include `max_population` and `pop_growth`
- [x] For `basic` and `none` scan levels: all new fields remain `None`
- [x] Include `colonists_died` and `planet_abandoned` events for the planet owner

---

## Step 6: Tests (`tests/engine/test_population.py`)

Cover pure functions and integration behaviour.

- [x] Unit tests for `factor_contribution`:
  - Value at ideal → +33.33
  - Value at range edge → 0
  - Value outside range → negative, scaled
  - Value at far extreme → −15
- [x] Unit tests for `calculate_hab_value`:
  - All three factors at JOAT ideal (50,50,50) → 100
  - All three at range edge (15 or 85) → 0
  - One factor outside range → negative contribution
- [x] Unit tests for `max_population`:
  - 100% → 1,000,000
  - 50% → 500,000
  - 3% → 50,000 (5% floor)
  - negative → 0
- [x] Unit tests for `population_growth`:
  - Below 25% capacity: full rate applied
  - Above 25% capacity: logistic slowdown
  - At max_population: zero growth
- [x] Unit tests for `population_death` and `overcrowding_deaths`
- [x] Integration test: turn 0 home planet has `gravity=50, temperature=50, radiation=50`
- [x] Integration test: turn 0 non-home planets have non-zero environment values
- [x] Integration test: positive-hab planet grows each turn
- [x] Integration test: negative-hab planet loses colonists each turn
- [x] Integration test: population reaches 0 → `owner` set to `null`, `planet_abandoned` event emitted
- [x] Integration test: fog of war exposes `habitability` at detailed scan level
- [x] Integration test: `max_population` and `pop_growth` visible to owner only

---

## Step 7: Lint and format

- [x] `cd backend && uv run ruff check .` — clean
- [x] `cd backend && uv run ruff format --check .` — clean

---

## Step 8: Run all tests

- [x] `cd backend && uv run pytest` — all passing

---

## Notes

- The derived habitability score is not stored — it is computed on demand from the `Habitability` object and race parameters
- Environment values in `PlanetState` are the current values; natural (pre-terraforming) values will be added when terraforming is implemented
- RNG seed offset `0xAB_5EED` keeps population generation independent from economy concentrations (which use `0xEC0_5EED`) and galaxy placement (SHA-256 based)
- Overcrowding productivity penalties (50% / 0% efficiency bands) are enforced during the resource calculation step (PRD 12) — `max_population` needs to be available at that point; call `max_population(planet.habitability)` from `economy.py` as needed
