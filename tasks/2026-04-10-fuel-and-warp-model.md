# Fuel and Warp Model

**PRD:** [10 — Fleet Movement](../docs/prd/10-fleet-movement.md), [15 — Freight Transport](../docs/prd/15-freight-transport.md)

Replace the simple flat `speed` property on ship designs with the proper Stars! warp factor and fuel consumption model. Fleets now move at warp² parsecs per turn, burn fuel according to the per-ship formula from the manual, and auto-refuel at shipbuilding starbases.

---

## Step 1 — Update `EngineStats` in the component catalogue

**Files:** `backend/openstars/engine/component_catalogue.py`

- Remove `max_warp` field from `EngineStats`
- Add `fuel_usage: list[int]` — exactly 10 entries, warp 1..10 (index 0 = warp 1). All values ≥ 0.

Validation: the model validator must reject `fuel_usage` lists that are not exactly length 10.

The YAML files (`engines.yaml`) already have `fuel_usage` arrays added; no YAML changes needed.

- [x] Remove `max_warp` from `EngineStats`
- [x] Add `fuel_usage: list[int]` with length-10 validation
- [x] Update `ComponentCatalogueDocument` validator if it references `max_warp`
- [x] Unit tests in `test_component_catalogue.py`:
  - catalogue loads successfully with the updated YAML
  - rejects an engine with a `fuel_usage` list that is not length 10
  - rejects an engine with a negative `fuel_usage` value

---

## Step 2 — Update `Design` model: replace `speed` with `fuel_usage` + `fuel_capacity`

**Files:** `backend/openstars/engine/models.py`

`Design` stores derived values (like `scanner`, `cargo_capacity`, `cost`) — not component references. Follow the same pattern: derive `fuel_usage` from the fitted engine at design-creation time and store it directly, so the resolution engine never needs to look up the catalogue mid-turn.

- Remove `speed: int` from `Design`
- Add `fuel_usage: list[int]` — 10 entries copied from the engine component at design creation time
- Add `fuel_capacity: int` — mg per ship, derived from the hull definition at design creation time

`engine_id` lives only in `ShipDesign.components` (the full component loadout model in the designer API). It does not belong on `Design`.

Also update `ShipDesign` in the designer models if it still carries `speed`.

- [x] Remove `speed` from `Design`; add `fuel_usage: list[int]` and `fuel_capacity: int = Field(ge=0)`
- [x] Unit tests in `test_models.py`:
  - `Design` round-trips with `fuel_usage` and `fuel_capacity`
  - `Design` rejects `fuel_usage` lists that are not length 10

---

## Step 3 — Add `fuel` to `Fleet`; add `warp` to `Waypoint`

**Files:** `backend/openstars/engine/models.py`

- Add `fuel: int = 0` to `Fleet` — current fuel in mg, shared across all ships
- Add `warp: int | None = None` to `Waypoint` — desired warp for this leg; `None` = auto-optimum

Also update `PlayerFleet`:
- Add `fuel: int | None = None` — owner-only
- Add `fuel_capacity: int | None = None` — owner-only; total mg across all ships

- [x] Add `fuel` to `Fleet`
- [x] Add `warp` to `Waypoint`
- [x] Add `fuel` and `fuel_capacity` to `PlayerFleet`
- [x] Unit tests in `test_models.py`:
  - `Fleet` with `fuel` round-trips correctly
  - `Waypoint` with `warp` round-trips correctly

---

## Step 4 — Update `create_game.py`

**Files:** `backend/openstars/engine/create_game.py`

Replace all uses of `speed=` on `Design` with `engine_id=` and `fuel_capacity=`, and set `fuel` on each starting fleet to its full capacity (sum of `fuel_capacity * count` across composition).

Starting hull fuel capacities from the Stars! manual:
- Scout: `engine_id="trans_galactic_drive"`, `fuel_capacity=50`
- Small Freighter: `engine_id="ion_drive"`, `fuel_capacity=130`
- Colony Ship: `engine_id="ion_drive"`, `fuel_capacity=200`

Remove the `SCOUT_SPEED`, `SMALL_FREIGHTER_SPEED`, `COLONY_SHIP_SPEED` constants and replace with engine/fuel constants.

- [x] Replace `speed` constants with `engine_id` / `fuel_capacity` constants
- [x] Update each `Design(...)` call: remove `speed=`, add `engine_id=` and `fuel_capacity=`
- [x] Set `fuel=` on every `Fleet(...)` call to the fleet's full fuel capacity
- [x] Unit tests in `test_setup.py`:
  - Turn 0 scout design has `engine_id="trans_galactic_drive"` and `fuel_capacity=50`
  - Turn 0 scout fleet starts with `fuel=50`
  - Turn 0 freighter fleet starts with `fuel=130`

---

## Step 5 — Update the movement engine

**Files:** `backend/openstars/engine/resolve_steps/movement.py`

Replace the flat `speed`-based distance budget with the warp² model plus fuel deduction and auto-refuel.

### Warp resolution

A helper `_effective_warp(fleet, warp_requested, leg_distance_parsecs, engine, designs_by_id)` determines the warp the fleet actually travels at:

1. Start from `waypoint.warp` if set, else compute optimum (highest warp the fleet can afford for the full leg).
2. If the fleet has insufficient fuel for that warp, step down to the highest affordable warp ≥ 2.
3. If even warp 2 is unaffordable, use warp 1 (free; no fuel consumed).

### Fuel consumption

Per ship per movement step:

```python
ship_fuel_used = ((ship_mass * engine.fuel_usage[warp - 1] * distance_parsecs // 200) + 9) // 10
```

Where `ship_mass` = design mass (hull + components, to be derived from catalogue) + cargo mass (1 kT per kT of minerals, 1 kT per 100 colonists rounded up).

**For this step**, derive design mass as `sum(component.mass for component in fitted_components)`. Hull base mass is not yet modelled separately — use the component masses from the catalogue for now.

Fleet fuel deducted = sum of per-ship fuel × count for all composition entries.

### Auto-refuel

After executing waypoint tasks (transport, colonise, etc.), if the fleet is at a planet coordinate owned by the same player that has `starbase.can_build_ships == True`, top the fleet's `fuel` up to `fleet_fuel_capacity`.

### Fuel warning event

If effective warp < requested warp (or < optimum), emit a `fleet.fuel_warning` event with the fleet ID, requested warp, and actual warp traveled.

### Changes to `move_fleet`

- Remove: `speed = min(designs_by_id[...].speed ...)` lookup
- Add: `engine` lookup for each design via `catalogue.by_id[design.engine_id]`
- Change: `budget = speed * PARSEC` → `budget = warp * warp * PARSEC`
- After each movement step: deduct fuel from `fleet.fuel`
- After waypoint task execution: check for auto-refuel

- [x] Add `catalogue: ComponentCatalogue` parameter to `move_fleet` (or load it in `move_fleets` and pass down)
- [x] Implement `_effective_warp` helper with fuel-step-down logic
- [x] Implement `_fuel_for_leg` helper computing total fleet fuel cost for a given warp + distance
- [x] Implement `_ship_mass` helper (component masses + cargo mass)
- [x] Replace `budget = speed * PARSEC` with `budget = warp² * PARSEC`
- [x] Deduct fuel after each move step
- [x] Add auto-refuel after waypoint task execution
- [x] Emit `fleet.fuel_warning` event when warp is reduced
- [x] Unit tests in `test_resolve.py` or a new `test_movement.py`:
  - Fleet at warp 6 moves 36 parsecs and burns correct fuel
  - Fleet with insufficient fuel steps down to affordable warp
  - Fleet with no affordable warp travels at warp 1 for free
  - Fleet arriving at own shipbuilding starbase planet is refuelled to full
  - Fleet arriving at enemy planet is not refuelled
  - `fleet.fuel_warning` event is emitted when warp is reduced

---

## Step 6 — Update fog of war (player state)

**Files:** `backend/openstars/engine/fog.py`

Expose `fuel` and `fuel_capacity` on own fleets in `derive_player_state`.

`fleet_fuel_capacity` helper (analogous to the existing `fleet_cargo_capacity` in `freight.py`) computes `sum(design.fuel_capacity * entry.count for ...)`.

- [x] Add `fleet_fuel_capacity` computation (can live in `freight.py` or a new utility)
- [x] Populate `fuel=fleet.fuel` and `fuel_capacity=fleet_fuel_capacity(...)` in the own-fleet branch of `derive_player_state`
- [x] Unit tests in `test_resolve.py` or `test_setup.py`:
  - Player state for own fleet includes `fuel` and `fuel_capacity`
  - Player state for enemy fleet omits `fuel` and `fuel_capacity`

---

## Step 7 — Update designer API: remove `speed`, add fuel/engine derived stats

**Files:** `backend/openstars/server/` (designer endpoint), `backend/openstars/engine/models.py` (`ShipDesign`)

The designer API response currently includes `speed`. Replace with `fuel_capacity` (from hull definition) and leave warp implicit (derived from engine at runtime).

- [x] Remove `speed` from `ShipDesign` response model; add `fuel_capacity: int`
- [x] Update the derived-stat computation in the design creation endpoint
- [x] Update `test_designer_api.py` to assert on `fuel_capacity` instead of `speed`

---

## Step 8 — Integration test

**Files:** `backend/tests/engine/test_resolve.py`

End-to-end turn resolution test covering fuel:

- Create a two-planet game; give a fleet a waypoint with `warp: 4`
- Resolve one turn; assert the fleet moved `16` parsecs and its fuel decreased by the expected amount
- Give a fleet a waypoint it cannot reach with current fuel; assert it steps down to a lower warp and emits `fleet.fuel_warning`
- Resolve a fleet arriving at a home starbase; assert fuel is topped back to full

- [x] Integration test: correct distance and fuel deduction at warp 4
- [x] Integration test: fuel step-down and warning event
- [x] Integration test: auto-refuel at shipbuilding starbase

---

## Follow-up — Cache design mass

Movement now uses a derived `Design.mass` value computed when the design is created, so fuel calculations do not need to reconstruct fitted component mass during turn resolution.

- [x] Add `mass` to `Design` and populate it from hull + fitted component mass
- [x] Update starting designs to persist precomputed mass
- [x] Simplify movement fuel helpers to use stored design mass and remove the catalogue dependency from `_effective_warp`
