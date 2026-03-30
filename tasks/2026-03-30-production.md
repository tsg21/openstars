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

- [ ] Add `ProductionProgress` and `ProductionQueueItem` to [`backend/openstars/engine/models.py`](/Users/tim/code/openstars/backend/openstars/engine/models.py)
- [ ] Extend `PlanetState` with `production_queue: list[ProductionQueueItem] = Field(default_factory=list)`
- [ ] Extend `PlayerPlanet` with `production_queue: list[PlayerProductionQueueItem] | None = None`
- [ ] Extend the command model(s) with `add_production_item`, `move_production_item`, `remove_production_item`, and `clear_production_queue`
- [ ] Keep queue item IDs server-generated and stable once created
- [ ] Add/update backend schema tests covering model defaults, serialization, and command validation surface
- [ ] Run `cd backend && uv run pytest tests/engine tests/server` for the touched schema coverage

---

## Step 2: Add production engine helpers

Create pure production helpers so queue spending and completion behaviour is isolated and easy to test.

- [ ] Add `backend/openstars/engine/resolve_steps/production.py`
- [ ] Keep production resolution helpers in `backend/openstars/engine/resolve_steps/` alongside other turn pipeline step modules
- [ ] Define Phase 1 unit costs for `mine` and `factory`, sourced from PRD 12 values
- [ ] Implement pure helpers for:
  - largest payable resource increment selection
  - proportional mineral spend calculation from total post-increment progress
  - per-unit completion handling
  - queue item removal/decrement semantics when quantity changes
- [ ] Keep the algorithm integer-only and deterministic
- [ ] Add focused unit tests covering:
  - mine/factory cost tables
  - proportional mineral thresholds
  - blocked factory progress from mineral shortage
  - completion resetting progress and decrementing quantity
  - removal semantics that discard partial progress without refunds
- [ ] Run `cd backend && uv run pytest tests/engine/test_production.py`

---

## Step 3: Apply production queue commands during resolution

Wire validated queue-edit commands into the authoritative command-application step.

- [ ] Update the command application path in [`backend/openstars/engine/resolve.py`](/Users/tim/code/openstars/backend/openstars/engine/resolve.py) or supporting modules to mutate `production_queue`
- [ ] Validate that `planet_id` belongs to the commanding player
- [ ] Validate `item_id` / `insert_after_item_id` references against that same planet queue
- [ ] Reject unsupported `item_type` values and non-positive `quantity`
- [ ] Preserve progress when moving items
- [ ] Drop progress without refunds when removing the partially completed unit or clearing the queue
- [ ] Add integration tests for add, move, partial remove, full remove, clear, and invalid cross-planet/cross-owner references
- [ ] Run `cd backend && uv run pytest tests/engine`

---

## Step 4: Insert Step 5 production into turn resolution

Resolve production after mining/resources and before the turn counter advances.

- [ ] Update the turn pipeline so production runs after Step 4 resource calculation
- [ ] Process owned planets in lexicographic planet ID order
- [ ] For each planet, spend from that turn's available resources only
- [ ] Process queue items top-to-bottom, letting the current item consume as many payable increments and completed units as possible before moving on
- [ ] Stop the rest of that planet's queue when the current item blocks on resources or minerals
- [ ] Apply completion effects:
  - `mine` adds one mine
  - `factory` adds one factory
- [ ] Remove queue entries automatically when `quantity` reaches zero
- [ ] Emit consistent owner-only `production_completed` events, choosing either per-unit or aggregated form and documenting the choice in code/tests
- [ ] Add integration tests covering:
  - single-turn mine completion
  - multi-turn factory progress persistence
  - blocking queue behaviour
  - multiple completed units from one queue entry in one turn
  - deterministic ordering across planets
- [ ] Run `cd backend && uv run pytest tests/engine/test_production.py tests/engine/test_resolve.py`

---

## Step 5: Expose production queues in player state and API responses

Make queue state visible only to the owning player, alongside production events and existing economy data.

- [ ] Update fog/player-state derivation in [`backend/openstars/engine/fog.py`](/Users/tim/code/openstars/backend/openstars/engine/fog.py) to include `production_queue` for own planets only
- [ ] Keep `production_queue = None` for non-owned planets, regardless of scan level
- [ ] Include `production_completed` events in the owner's event list
- [ ] Ensure API responses serialize production queue data cleanly through the existing snake_case to camelCase client conversion
- [ ] Add/update backend tests for own-planet visibility, non-owner redaction, and event propagation
- [ ] Run `cd backend && uv run pytest tests/engine tests/server`

---

## Step 6: Add frontend production queue UI for owned planets

Add the initial production panel in the planet detail flow, limited to mines and factories.

- [ ] Review the current planet detail panel and choose where the production queue lives without disrupting existing layout
- [ ] Add TypeScript types for owner-visible production queue items if needed
- [ ] Render the selected owned planet's queue with item type, quantity remaining, and partial progress for the current unit
- [ ] Add controls to:
  - add `Mine` and `Factory` items
  - remove queue items
  - move items up/down or otherwise reorder them
  - clear the queue
- [ ] Show blocked-state messaging when the current queue item cannot progress because of resource or mineral shortage if that information is available from current state; otherwise document the backend/frontend gap as a follow-up note
- [ ] Ensure non-owned planets do not show editable production controls
- [ ] Add frontend tests for queue rendering and edit interactions
- [ ] Run `cd frontend && npm test`
- [ ] Run `cd frontend && npx tsc --noEmit`
- [ ] Run `cd frontend && npm run lint`

---

## Step 7: End-to-end verification and task record update

Finish the task with full verification and record the outcome here.

- [ ] Run `cd backend && uv run pytest`
- [ ] Run `cd backend && uv run ruff check .`
- [ ] Run `cd backend && uv run ruff format --check .`
- [ ] Run `cd frontend && npm test`
- [ ] Run `cd frontend && npx tsc --noEmit`
- [ ] Run `cd frontend && npm run lint`
- [ ] Update this task file with `[x]` for completed work and add notes about event aggregation choice, any deferred UI gaps, and follow-up tasks

---

## Notes

- Build this on top of the existing PRD 12 resource calculation rather than introducing resource stockpiling
- Keep all queue/progress state in authoritative global state; the client edits intent only
- If blocked-state UX needs extra backend state beyond the PRD's current player model, capture that as an explicit follow-up instead of inferring unreliably on the client
