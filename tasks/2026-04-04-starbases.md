# Starbases (PRD 17)

Implements the first starbase system described in `docs/prd/17-starbases.md`: explicit planet-attached starbase state, home-world starbase seeding, starbase construction and upgrades through production, shipbuilding gating, owner/scanner-visible starbase data, and basic planet-detail UI.

## Scope

This task covers the narrow Phase 1 starbase model from `docs/prd/17-starbases.md`, building on the existing production system in `docs/prd/13-production.md`.

It includes backend engine work, turn-0 generation changes, player-state/API wiring, and frontend display for the new starbase state.

Out of scope for this task:

- Starbase design editor UI
- Custom starbase designs
- Fuel or refuelling
- Stargates, mass drivers, orbital scanners, cloaks, or other orbital components
- Bombing, invasion, starbase combat, or repair
- Race-trait-specific starbase rules beyond the two initial supported types

---

## Step 1: Extend engine models for planet starbases

Add the core starbase state to the backend schema layer.

- [ ] Add `PlanetStarbaseState` to [`backend/openstars/engine/models.py`](/Users/tim/code/openstars/backend/openstars/engine/models.py)
- [ ] Extend `PlanetState` with `starbase: PlanetStarbaseState | None = None`
- [ ] Constrain starbase `type` to the PRD 17 Phase 1 values: `orbital_fort` and `space_station`
- [ ] Add `can_build_ships: bool` to the starbase state
- [ ] Extend owner-visible player planet models with `starbase` data
- [ ] Extend scanned non-owner planet models with the starbase summary fields allowed by current scan level
- [ ] Add/update backend schema tests covering defaults, serialization, and validation for starbase state
- [ ] Run `cd backend && uv run pytest tests/engine tests/server`

---

## Step 2: Seed home-world starbases at turn 0

Make home-world shipbuilding capability explicit in authoritative game state.

- [ ] Update turn-0 generation so each player home world starts with `starbase.type = "space_station"`
- [ ] Set `can_build_ships = true` on seeded home-world starbases
- [ ] Ensure non-home planets still start with `starbase = None`
- [ ] Update any turn-0 fixture builders and test factories that currently assume implicit home-world shipbuilding
- [ ] Add/update backend tests covering home-world starbase seeding and non-home absence
- [ ] Run `cd backend && uv run pytest tests/engine tests/server`

---

## Step 3: Add starbases to the production queue model

Teach the queue and command schema about starbase production items.

- [ ] Extend `ProductionQueueItem` to support `item_type = "starbase"`
- [ ] Add `target_type: Literal["orbital_fort", "space_station"] | None` to queue items, required for `starbase` items and absent for others
- [ ] Extend production command validation so `add_production_item` accepts `starbase` items with a valid `target_type`
- [ ] Reject invalid combinations such as:
  - `starbase` without `target_type`
  - non-`starbase` queue items with `target_type`
  - unsupported starbase target types
- [ ] Keep queue item IDs server-generated and stable once created
- [ ] Add/update backend schema and command-validation tests for the new queue item shape
- [ ] Run `cd backend && uv run pytest tests/engine tests/server`

---

## Step 4: Implement starbase production costs and completion rules

Extend production resolution so planets can build and upgrade starbases deterministically.

- [ ] Define Phase 1 starbase cost tables for `orbital_fort` and `space_station`, documented in code and aligned with PRD 17
- [ ] Implement completion handling for:
  - constructing a first starbase on a planet with `starbase = None`
  - upgrading from one supported starbase type to the other
- [ ] Implement the PRD 17 upgrade credit rule:
  - reject upgrade to the same type
  - pay `target_cost - source_credit`
  - `source_credit = 50%` of the existing starbase's total value
- [ ] Keep all production resolution integer-only and deterministic
- [ ] Add focused unit tests covering:
  - starbase cost lookup
  - first-build completion
  - upgrade cost calculation
  - invalid same-type upgrade rejection
  - queue blocking/progress persistence for starbase builds
- [ ] Run `cd backend && uv run pytest tests/engine/test_production.py`

---

## Step 5: Apply starbase queue commands and shipbuilding gating

Wire starbase production into authoritative command application and enforce the new build gate for ships.

- [ ] Update production command application to accept and store valid starbase queue items
- [ ] Reject more than one unfinished `starbase` queue item on the same planet
- [ ] Reject starbase production commands on unowned planets
- [ ] Enforce PRD 17 shipbuilding gating:
  - planets without a starbase cannot queue ship production items
  - planets with `can_build_ships = false` cannot queue ship production items
  - planets with `can_build_ships = true` may queue ship production items once ship production exists or in any current validation surface that references it
- [ ] Add integration tests for:
  - adding a first starbase item
  - queuing an upgrade
  - rejecting duplicate unfinished starbase items
  - rejecting invalid target types
  - rejecting ship production on planets without shipbuilding-capable starbases
- [ ] Run `cd backend && uv run pytest tests/engine`

---

## Step 6: Expose starbases in player state and fog-of-war output

Make starbase state visible to the right players at the right detail level.

- [ ] Update fog/player-state derivation in [`backend/openstars/engine/fog.py`](/Users/tim/code/openstars/backend/openstars/engine/fog.py) to include starbase summaries on planets
- [ ] For owned planets, include full Phase 1 starbase state
- [ ] For non-owned planets, expose only the starbase fields allowed by current scan level
- [ ] Ensure planets with no starbase serialize cleanly as `starbase = null` or omission, whichever the current player-state contract expects
- [ ] Emit owner-visible `starbase.constructed` and `starbase.upgraded` events
- [ ] Add/update backend tests for own-planet visibility, scanned enemy visibility, hidden-planet behaviour, and event propagation
- [ ] Run `cd backend && uv run pytest tests/engine tests/server`

---

## Step 7: Add frontend starbase display in planet detail

Show starbase state in the existing planet detail flow without introducing a full editor.

- [ ] Review the current planet detail panel and choose where starbase information lives without disrupting existing layout
- [ ] Add/update TypeScript types for planet starbase data
- [ ] Render owned-planet starbase state, including:
  - starbase presence/absence
  - starbase type
  - whether it can build ships
- [ ] Render non-owned scanned starbase summaries according to available player-state fields
- [ ] Add basic UI for queueing supported starbase builds/upgrades if the current production panel is the right place for it; otherwise document the deferred UI follow-up in this task file
- [ ] Preserve the current yellow/blue semantic distinction for shipbuilding-capable vs non-shipbuilding starbases if represented in the UI
- [ ] Add frontend tests for starbase rendering and any new interactions
- [ ] Run `cd frontend && npm test`
- [ ] Run `cd frontend && npx tsc --noEmit`
- [ ] Run `cd frontend && npm run lint`

---

## Step 8: End-to-end verification and task record update

Finish the task with full verification and record the outcome here.

- [ ] Run `cd backend && uv run pytest`
- [ ] Run `cd backend && uv run ruff check .`
- [ ] Run `cd backend && uv run ruff format --check .`
- [ ] Run `cd frontend && npm test`
- [ ] Run `cd frontend && npx tsc --noEmit`
- [ ] Run `cd frontend && npm run lint`
- [ ] Update this task file with `[x]` for completed work and add notes about final starbase cost choices, any deferred UI gaps, and any follow-up work

---

## Notes

- Build this on top of the existing production queue rather than inventing a parallel starbase-construction workflow
- Keep starbase state authoritative in global state; the client edits intent only
- Avoid introducing fuel/refuelling fields or behaviour in this task
- Keep the supported-type surface narrow: `orbital_fort` and `space_station` only
- If ship-production gating touches code paths that do not yet support ship production end-to-end, capture the exact follow-up clearly rather than inventing speculative UI
