# Production (PRD 13)

Implements the first per-planet production system: authoritative production queues, queue-edit commands, deterministic production resolution, owner-only queue visibility, and a basic planet production UI for mines and factories.

## Scope

This task covers the initial production queue described in `docs/prd/13-production.md`, building on PRD 12 economy/resource output. It includes backend engine work, player-state/API wiring, and the first frontend queue editor for owned planets.

Out of scope for this task:

- Ships, starbases, defences, terraforming, templates, or research spending
- Tech-based cost modifiers
- Multi-planet production workflows or bulk editing

---

## Step 1: Extend engine models and command schema

Add the production queue models and new command variants to the backend schema layer.

- [x] Add `ProductionProgress` and `ProductionQueueItem` to [`backend/openstars/engine/models.py`](/Users/tim/code/openstars/backend/openstars/engine/models.py)
- [x] Extend `PlanetState` with `production_queue: list[ProductionQueueItem] = Field(default_factory=list)`
- [x] Extend `PlayerPlanet` with `production_queue: list[PlayerProductionQueueItem] | None = None`
- [x] Extend the command model(s) with `add_production_item`, `move_production_item`, `remove_production_item`, and `clear_production_queue`
- [x] Keep queue item IDs server-generated and stable once created
- [x] Add/update backend schema tests covering model defaults, serialization, and command validation surface
- [x] Run `cd backend && uv run pytest tests/engine tests/server` for the touched schema coverage

---

## Step 2: Add production engine helpers

Create pure production helpers so queue spending and completion behaviour is isolated and easy to test.

- [x] Add `backend/openstars/engine/resolve_steps/production.py`
- [x] Keep production resolution helpers in `backend/openstars/engine/resolve_steps/` alongside other turn pipeline step modules
- [x] Define Phase 1 unit costs for `mine` and `factory`, sourced from PRD 12 values
- [x] Implement pure helpers for:
  - largest payable resource increment selection
  - proportional mineral spend calculation from total post-increment progress
  - per-unit completion handling
  - queue item removal/decrement semantics when quantity changes
- [x] Keep the algorithm integer-only and deterministic
- [x] Add focused unit tests covering:
  - mine/factory cost tables
  - proportional mineral thresholds
  - blocked factory progress from mineral shortage
  - completion resetting progress and decrementing quantity
  - removal semantics that discard partial progress without refunds
- [x] Run `cd backend && uv run pytest tests/engine/test_production.py`

---

## Step 3: Apply production queue commands during resolution

Wire validated queue-edit commands into the authoritative command-application step.

- [x] Update the command application path in [`backend/openstars/engine/resolve.py`](/Users/tim/code/openstars/backend/openstars/engine/resolve.py) or supporting modules to mutate `production_queue`
- [x] Validate that `planet_id` belongs to the commanding player
- [x] Validate `item_id` / `insert_after_item_id` references against that same planet queue
- [x] Reject unsupported `item_type` values and non-positive `quantity`
- [x] Preserve progress when moving items
- [x] Drop progress without refunds when removing the partially completed unit or clearing the queue
- [x] Add integration tests for add, move, partial remove, full remove, clear, and invalid cross-planet/cross-owner references
- [x] Run `cd backend && uv run pytest tests/engine`

---

## Step 4: Insert Step 5 production into turn resolution

Resolve production after mining/resources and before the turn counter advances.

- [x] Update the turn pipeline so production runs after Step 4 resource calculation
- [x] Process owned planets in lexicographic planet ID order
- [x] For each planet, spend from that turn's available resources only
- [x] Process queue items top-to-bottom, letting the current item consume as many payable increments and completed units as possible before moving on
- [x] Stop the rest of that planet's queue when the current item blocks on resources or minerals
- [x] Apply completion effects:
  - `mine` adds one mine
  - `factory` adds one factory
- [x] Remove queue entries automatically when `quantity` reaches zero
- [x] Emit consistent owner-only `production_completed` events, choosing either per-unit or aggregated form and documenting the choice in code/tests
- [x] Add integration tests covering:
  - single-turn mine completion
  - multi-turn factory progress persistence
  - blocking queue behaviour
  - multiple completed units from one queue entry in one turn
  - deterministic ordering across planets
- [x] Run `cd backend && uv run pytest tests/engine/test_production.py tests/engine/test_resolve.py`

---

## Step 5: Expose production queues in player state and API responses

Make queue state visible only to the owning player, alongside production events and existing economy data.

- [x] Update fog/player-state derivation in [`backend/openstars/engine/fog.py`](/Users/tim/code/openstars/backend/openstars/engine/fog.py) to include `production_queue` for own planets only
- [x] Keep `production_queue = None` for non-owned planets, regardless of scan level
- [x] Include `production_completed` events in the owner's event list
- [x] Ensure API responses serialize production queue data cleanly through the existing snake_case to camelCase client conversion
- [x] Add/update backend tests for own-planet visibility, non-owner redaction, and event propagation
- [x] Run `cd backend && uv run pytest tests/engine tests/server`

---

## Step 6: Add frontend production queue UI for owned planets

Add the initial production panel in the planet detail flow, limited to mines and factories.

- [x] Review the current planet detail panel and choose where the production queue lives without disrupting existing layout
- [x] Add TypeScript types for owner-visible production queue items if needed
- [x] Render the selected owned planet's queue with item type, quantity remaining, and partial progress for the current unit
- [x] Add controls to:
  - add `Mine` and `Factory` items
  - remove queue items
  - move items up/down or otherwise reorder them
  - clear the queue
- [x] Show blocked-state messaging when the current queue item cannot progress because of resource or mineral shortage if that information is available from current state; otherwise document the backend/frontend gap as a follow-up note
- [x] Ensure non-owned planets do not show editable production controls
- [x] Add frontend tests for queue rendering and edit interactions
- [x] Run `cd frontend && npm test`
- [x] Run `cd frontend && npx tsc --noEmit`
- [x] Run `cd frontend && npm run lint`

---

## Step 7: End-to-end verification and task record update

Finish the task with full verification and record the outcome here.

- [x] Run `cd backend && uv run pytest`
- [x] Run `cd backend && uv run ruff check .`
- [x] Run `cd backend && uv run ruff format --check .`
- [x] Run `cd frontend && npm test`
- [x] Run `cd frontend && npx tsc --noEmit`
- [x] Run `cd frontend && npm run lint`
- [x] Update this task file with `[x]` for completed work and add notes about event aggregation choice, any deferred UI gaps, and follow-up tasks

---

## Notes

- Build this on top of the existing PRD 12 resource calculation rather than introducing resource stockpiling
- Keep all queue/progress state in authoritative global state; the client edits intent only
- If blocked-state UX needs extra backend state beyond the PRD's current player model, capture that as an explicit follow-up instead of inferring unreliably on the client
- Event aggregation choice: aggregate `production_completed` events per planet and item type for the turn, rather than emitting one event per completed unit
- Deferred UI gap: the frontend currently renders an explicit follow-up note for blocked production state because player state does not yet expose whether the active queue item is blocked by resources or minerals
- Follow-up task: add explicit player-visible production blockage metadata so the detail panel can distinguish resource shortage from mineral shortage without guessing
