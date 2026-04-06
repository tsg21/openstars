# Ship Production (PRD 13 extension)

Extends the existing production system to support ship production: player-owned ship designs with associated costs, ship queue items referencing those designs, production resolution that creates ships and places them into fleets at the producing planet, and frontend production UI for ships.

## Scope

This task covers the ship production additions to `docs/prd/13-production.md`, building on the existing production queue and the starbase shipbuilding gate from `docs/prd/17-starbases.md`.

Out of scope for this task:

- Ship design editor (hull selection and component fitting)
- Ship scrapping
- Tech-based cost reductions
- Race-trait-specific design availability

---

## Step 1: Extend engine models for ship designs and ship queue items

Add the ship design and cost models and extend the production queue schema to support ship items.

- [x] Add ship design cost data to [`backend/openstars/engine/models.py`](/Users/tim/code/openstars/backend/openstars/engine/models.py) and store it on the shared `Design` model
- [x] Keep ship designs in the existing `designs: list[Design]` global state collection rather than maintaining a second list
- [x] Extend `ProductionQueueItem.item_type` to include `"ship"`
- [x] Add `design_id: str | None = None` to `ProductionQueueItem`, required when `item_type == "ship"` and absent otherwise
- [x] Extend `PlayerProductionQueueItem` with the same `design_id` field
- [x] Add/update backend schema tests covering model defaults, serialization, and the `design_id` constraint
- [x] Run `cd backend && uv run pytest tests/engine tests/server`

---

## Step 2: Seed starting ship designs and add designs API endpoint

Give each player a minimal set of starting designs at turn 0, and expose designs through a dedicated endpoint outside the normal turn lifecycle.

- [x] Define the Phase 1 starting design set in code (at minimum a basic Scout with appropriate resource and mineral costs) and document the chosen cost values in this task's Notes section below
- [x] Update turn-0 generation to create starting designs for each player in global state
- [x] Add `GET /games/{game_id}/designs` endpoint returning all buildable designs owned by the authenticated player
- [x] Ensure the endpoint is not coupled to turn resolution — designs are read-only through this endpoint for now
- [x] Add backend tests for:
  - turn-0 design seeding
  - designs endpoint response shape
  - designs endpoint returns only the requesting player's designs
- [x] Run `cd backend && uv run pytest tests/engine tests/server`

---

## Step 3: Extend production command validation for ship items

Teach command application to accept and validate ship production items.

- [x] Update `add_production_item` handling to accept `item_type = "ship"` with a `design_id`
- [x] Validate that `design_id` references a design owned by the commanding player
- [x] Validate that the planet has a starbase with `can_build_ships = true` (gate already modelled in PRD 17)
- [x] Reject ship items without `design_id` and non-ship items with `design_id`
- [x] Add integration tests for:
  - valid ship item queued on a shipbuilding planet
  - rejected on a planet with no starbase
  - rejected on a planet with `can_build_ships = false`
  - rejected with a missing or foreign `design_id`
- [x] Run `cd backend && uv run pytest tests/engine`

---

## Step 4: Implement ship production resolution and fleet completion

Extend the production engine to resolve ship items and place completed ships into fleets.

- [x] Extend the production resolution step to look up the referenced design's cost when processing a `ship` queue item
- [x] Use the same proportional mineral spend algorithm as mines and factories
- [x] On unit completion, apply the fleet joining rule:
  1. Find all fleets at the planet owned by the same player that contain at least one ship of the completed design
  2. If any exist, add the new ship to the one with the lexicographically smallest fleet ID
  3. Otherwise create a new fleet at the planet containing the single new ship
- [x] Emit `production.ship_built` events per the PRD 13 event envelope: `values: [planet_name, design_name, quantity]`
- [x] Add focused unit tests covering:
  - ship cost lookup from design
  - proportional mineral spend for a multi-mineral ship cost
  - completion joining an existing fleet containing that design
  - completion creating a new fleet when none exists
  - completion joining the correct fleet when multiple fleets at the planet contain the design
- [x] Run `cd backend && uv run pytest tests/engine/test_production.py`

---

## Step 5: Expose ship designs and updated queue state in player state and API

Make designs and ship queue items visible to the client.

- [x] Include `design_id` on ship `PlayerProductionQueueItem` entries in the fog/player-state derivation
- [x] Ensure `production.ship_built` events appear in the owner's event list
- [x] Confirm the designs endpoint serialises cleanly through the existing snake_case to camelCase conversion
- [x] Add/update backend tests for own-planet ship queue visibility and event propagation
- [x] Run `cd backend && uv run pytest tests/engine tests/server`

---

## Step 6: Add frontend ship production UI

Extend the production panel to show and queue ship designs.

- [x] Add/update TypeScript types for `ShipDesign` and ship `PlayerProductionQueueItem`
- [x] Fetch available designs from `GET /games/{game_id}/designs` and display them in the production inventory alongside mines and factories
- [x] Allow adding ship items to the queue by selecting a design
- [x] Render queued ship items showing design name, quantity remaining, and partial progress
- [x] Ensure ship items respect the existing move, remove, and clear controls
- [x] Add frontend tests for design listing and ship queue item rendering
- [x] Run `cd frontend && npm test`
- [x] Run `cd frontend && npx tsc --noEmit`
- [x] Run `cd frontend && npm run lint`

---

## Step 7: End-to-end verification and task record update

- [x] Run `cd backend && uv run pytest`
- [x] Run `cd backend && uv run ruff check .`
- [x] Run `cd backend && uv run ruff format --check .`
- [x] Run `cd frontend && npm test`
- [x] Run `cd frontend && npx tsc --noEmit`
- [x] Run `cd frontend && npm run lint`
- [x] Update this task file with `[x]` for completed work and add notes about starting design costs, fleet creation behaviour observed in testing, and any follow-up work

---

## Notes

- Designs are immutable: the engine reads cost directly from the design at resolution time, no snapshot is stored on the queue item
- Ship production now uses the shared `designs` collection as the single source of truth; a design is buildable when it has a non-null `cost`
- Designs live outside the turn lifecycle — they are not submitted as turn commands and are not modified by resolution
- Keep all queue and fleet state authoritative in global state; the client edits intent only
- Starting design costs to be documented here once chosen in Step 2
- Implemented starting ship design set per player:
  - `Scout`: **15 resources**, **5 ironium**, **3 boranium**, **2 germanium**
  - `Small Freighter`: **20 resources**, **12 ironium**, **0 boranium**, **17 germanium**
  - `Colony Ship`: **30 resources**, **5 ironium**, **5 boranium**, **15 germanium**
- Fleet completion behaviour observed in tests:
  - Completed ships join the lexicographically smallest same-owner fleet at the producing planet that already contains that design
  - If no such fleet exists, a new single-ship fleet is created at the producing planet
- Follow-up work:
  - Decide production fleet naming scheme (currently a deterministic fallback name is assigned when creating a new fleet from ship production)
  - Add a dedicated design management flow (create/update/scrap) when design editing enters scope
