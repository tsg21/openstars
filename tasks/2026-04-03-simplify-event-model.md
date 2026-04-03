# Simplify Event Model to Code + Values Envelope

Refactor turn events so backend emits a generic event envelope and frontend owns message rendering.

## Goal

Replace typed, attribute-heavy events with a reusable structure:

- `owner` — player who should see the event
- `source_id` — entity reference (typically planet/fleet id)
- `code` — stable message code
- `values` — ordered inserts used by frontend templates

This removes the need to extend backend/frontend types for every new event shape.

---

## Step 1: Update PRD + API contract

Document and agree the new event contract before implementation.

- [x] Update `docs/prd/03-turn-lifecycle.md` events section to define the generic envelope and migration notes from typed events
- [x] Update `docs/prd/50-api.md` player-state schema and examples to use:
  - `owner: string`
  - `source_id: string | null`
  - `code: string`
  - `values: (string | number)[]`
- [x] Define initial canonical event codes used in Phase 1 mechanics (movement/scanning/economy/population)
- [x] Add guidance that `code` values are stable API surface; message text is UI-owned and localisable

Validation:
- [x] Docs sanity pass: examples in PRD 03 and API 50 match exactly (field names, casing, semantics)

---

## Step 2: Backend model and emitters

Replace `GameEvent` shape and update all resolution steps that emit events.

- [x] Update `backend/openstars/engine/models.py`:
  - Replace typed optional fields with generic event model (`owner`, `source_id`, `code`, `values`)
- [x] Update event producers to emit generic events:
  - `resolve_steps/mining.py`
  - `resolve_steps/production.py`
  - `resolve_steps/population.py`
  - any movement/scanner/colonisation modules currently emitting typed payloads
- [x] Ensure event ordering remains deterministic and unchanged relative to resolution order
- [x] Keep fog-of-war behavior unchanged (players only receive their own events)

Unit tests (backend):
- [x] Update/add tests under `backend/tests/engine/` to assert `code` + `values` payloads for mining/production/population
- [x] Add a regression test that unknown/new `code` strings pass through unchanged (no backend schema extension needed)

Validation commands:
- [x] `cd backend && uv run pytest backend/tests/engine/test_economy.py`
- [x] `cd backend && uv run pytest backend/tests/engine/test_population.py`

---

## Step 3: Frontend event dictionary and rendering

Move human-readable message construction to the frontend via code templates.

- [x] Replace discriminated union `GameEvent` types in `frontend/src/types/game.ts` with a generic event interface aligned to API client camelCase conversion:
  - `owner`, `sourceId`, `code`, `values`
- [x] Add event message dictionary (e.g. `frontend/src/components/eventMessages.ts` or similar):
  - map `code -> template`
  - support positional inserts from `values`
- [x] Update `EventLog.tsx` to:
  - render message text via code template formatter
  - gracefully handle unknown `code` (fallback generic string)
  - derive click target from `sourceId` using lookup logic (planet/fleet where applicable)
- [x] Keep icon/tone mapping code-based (default style for unknown codes)

Unit tests (frontend):
- [x] Add formatter tests for insert replacement and unknown code fallback
- [x] Update `EventLog` tests to assert rendered message text from `code` + `values`

Validation commands:
- [x] `cd frontend && npm test`
- [x] `cd frontend && npm run lint`
- [x] `cd frontend && npx tsc --noEmit`

---

## Step 4: Integration and migration verification

Confirm end-to-end behavior over HTTP and avoid compatibility surprises.

- [x] Update integration tests that currently assert typed event fields to assert generic envelope fields
- [ ] Add at least one integration assertion per major code family:
  - mining
  - production completed
  - population loss / abandonment
- [x] Verify frontend still displays turn events and map-centre click behavior using `sourceId`

Integration command:
- [x] `./backend/int_tests/run.sh`

---

## Step 5: Final quality gate

- [x] Backend lint: `cd backend && uv run ruff check .`
- [x] Backend format check: `cd backend && uv run ruff format --check .`
- [x] Frontend lint: `cd frontend && npm run lint`
- [x] Frontend typecheck: `cd frontend && npx tsc --noEmit`
- [x] Frontend tests: `cd frontend && npm test`

---

## Implementation notes

- Preserve API snake_case on the wire (`source_id`); frontend consumes camelCase (`sourceId`) via client conversion.
- `values` should remain positional, not keyed, to keep payload small and backend-agnostic.
- If localisation is added later, only frontend dictionaries should change.
- If needed, a short-lived compatibility layer can map legacy backend events to new UI format during rollout, then be removed in the same task.
