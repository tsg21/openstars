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

- [x] Add `PlanetStarbaseState` to [`backend/openstars/engine/models.py`](/Users/tim/code/openstars/backend/openstars/engine/models.py)
- [x] Extend `PlanetState` with `starbase: PlanetStarbaseState | None = None`
- [x] Constrain starbase `type` to the PRD 17 Phase 1 values: `orbital_fort` and `space_station`
- [x] Add `can_build_ships: bool` to the starbase state
- [x] Extend owner-visible player planet models with `starbase` data
- [x] Extend scanned non-owner planet models with the starbase summary fields allowed by current scan level
- [x] Add/update backend schema tests covering defaults, serialization, and validation for starbase state
- [x] Run `cd backend && uv run pytest tests/engine tests/server`

---

## Step 2: Seed home-world starbases at turn 0

Make home-world shipbuilding capability explicit in authoritative game state.

- [x] Update turn-0 generation so each player home world starts with `starbase.type = "space_station"`
- [x] Set `can_build_ships = true` on seeded home-world starbases
- [x] Ensure non-home planets still start with `starbase = None`
- [x] Update any turn-0 fixture builders and test factories that currently assume implicit home-world shipbuilding
- [x] Add/update backend tests covering home-world starbase seeding and non-home absence
- [x] Run `cd backend && uv run pytest tests/engine tests/server`

---

## Step 3: Add starbases to the production queue model

Teach the queue and command schema about starbase production items.

- [x] Extend `ProductionQueueItem` to support `item_type = "starbase"`
- [x] Add `target_type: Literal["orbital_fort", "space_station"] | None` to queue items, required for `starbase` items and absent for others
- [x] Extend production command validation so `add_production_item` accepts `starbase` items with a valid `target_type`
- [x] Reject invalid combinations such as:
  - `starbase` without `target_type`
  - non-`starbase` queue items with `target_type`
  - unsupported starbase target types
- [x] Keep queue item IDs server-generated and stable once created
- [x] Add/update backend schema and command-validation tests for the new queue item shape
- [x] Run `cd backend && uv run pytest tests/engine tests/server`

---

## Step 4: Implement starbase production costs and completion rules

Extend production resolution so planets can build and upgrade starbases deterministically.

- [x] Define Phase 1 starbase cost tables for `orbital_fort` and `space_station`, documented in code and aligned with PRD 17
- [x] Implement completion handling for:
  - constructing a first starbase on a planet with `starbase = None`
  - upgrading from one supported starbase type to the other
- [x] Implement the PRD 17 upgrade credit rule:
  - reject upgrade to the same type
  - pay `target_cost - source_credit`
  - `source_credit = 50%` of the existing starbase's total value
- [x] Keep all production resolution integer-only and deterministic
- [x] Add focused unit tests covering:
  - starbase cost lookup
  - first-build completion
  - upgrade cost calculation
  - invalid same-type upgrade rejection
  - queue blocking/progress persistence for starbase builds
- [x] Run `cd backend && uv run pytest tests/engine/test_production.py`

---

## Step 5: Apply starbase queue commands and shipbuilding gating

Wire starbase production into authoritative command application and enforce the new build gate for ships.

- [x] Update production command application to accept and store valid starbase queue items
- [x] Reject more than one unfinished `starbase` queue item on the same planet
- [x] Reject starbase production commands on unowned planets
- [x] Enforce PRD 17 shipbuilding gating:
  - planets without a starbase cannot queue ship production items
  - planets with `can_build_ships = false` cannot queue ship production items
  - planets with `can_build_ships = true` may queue ship production items once ship production exists or in any current validation surface that references it
- [x] Add integration tests for:
  - adding a first starbase item
  - queuing an upgrade
  - rejecting duplicate unfinished starbase items
  - rejecting invalid target types
  - rejecting ship production on planets without shipbuilding-capable starbases
- [x] Run `cd backend && uv run pytest tests/engine`

---

## Step 6: Expose starbases in player state and fog-of-war output

Make starbase state visible to the right players at the right detail level.

- [x] Update fog/player-state derivation in [`backend/openstars/engine/fog.py`](/Users/tim/code/openstars/backend/openstars/engine/fog.py) to include starbase summaries on planets
- [x] For owned planets, include full Phase 1 starbase state
- [x] For non-owned planets, expose only the starbase fields allowed by current scan level
- [x] Ensure planets with no starbase serialize cleanly as `starbase = null` or omission, whichever the current player-state contract expects
- [x] Emit owner-visible `starbase.constructed` and `starbase.upgraded` events
- [x] Add/update backend tests for own-planet visibility, scanned enemy visibility, hidden-planet behaviour, and event propagation
- [x] Run `cd backend && uv run pytest tests/engine tests/server`

---

## Step 7: Add frontend starbase display in planet detail

Show starbase state in the existing planet detail flow without introducing a full editor.

- [x] Review the current planet detail panel and choose where starbase information lives without disrupting existing layout
- [x] Add/update TypeScript types for planet starbase data
- [x] Render owned-planet starbase state, including:
  - starbase presence/absence
  - starbase type
  - whether it can build ships
- [x] Render non-owned scanned starbase summaries according to available player-state fields
- [x] Add basic UI for queueing supported starbase builds/upgrades if the current production panel is the right place for it; otherwise document the deferred UI follow-up in this task file
- [x] Preserve the current yellow/blue semantic distinction for shipbuilding-capable vs non-shipbuilding starbases if represented in the UI
- [x] Add frontend tests for starbase rendering and any new interactions
- [x] Run `cd frontend && npm test`
- [x] Run `cd frontend && npx tsc --noEmit`
- [x] Run `cd frontend && npm run lint`

---

## Step 8: End-to-end verification and task record update

Finish the task with full verification and record the outcome here.

- [x] Run `cd backend && uv run pytest`
- [x] Run `cd backend && uv run ruff check .`
- [x] Run `cd backend && uv run ruff format --check .`
- [x] Run `cd frontend && npm test`
- [x] Run `cd frontend && npx tsc --noEmit`
- [x] Run `cd frontend && npm run lint`
- [x] Update this task file with `[x]` for completed work and add notes about final starbase cost choices, any deferred UI gaps, and any follow-up work

---

## Notes

- Build this on top of the existing production queue rather than inventing a parallel starbase-construction workflow
- Keep starbase state authoritative in global state; the client edits intent only
- Avoid introducing fuel/refuelling fields or behaviour in this task
- Keep the supported-type surface narrow: `orbital_fort` and `space_station` only
- If ship-production gating touches code paths that do not yet support ship production end-to-end, capture the exact follow-up clearly rather than inventing speculative UI


### Implementation notes (2026-04-04)

- Final Phase 1 starbase costs implemented in backend:
  - `orbital_fort`: 80 resources, 40 ironium, 20 boranium, 10 germanium
  - `space_station`: 160 resources, 80 ironium, 40 boranium, 20 germanium
- Upgrade costing uses `target_cost - 50% source_credit` per PRD 17, integer-only and deterministic.
- Frontend queue UI now supports adding `orbital_fort` and `space_station` starbase items from planet detail production controls.
- Galaxy map planets with visible starbases now render a small yellow marker at the top right of the planet dot, positioned to sit inside the orbit-fleet ring when present.
- No separate starbase design editor was added; this remains intentionally out of scope for Phase 1.
