# Colonisation (PRD 16)

Implement the remaining colonisation work from `docs/prd/16-colonisation.md`: the `colonize` waypoint task, colony ship dismantling, colony establishment, failure handling, and player-facing events.

## Scope

- Starting turn 0 colony ships are already implemented in `tasks/2026-04-03-starting-colony-ship.md`; do not duplicate that work here
- Primary scope is backend simulation and API-visible behavior
- Frontend layout for creating colonise orders remains a separate follow-up under the UI PRD, but this task should include any lightweight type or event-message support needed so colonisation results display correctly

---

## Step 1: Align PRD 16 with the current event contract

PRD 16 still shows typed event payloads, but the codebase now uses the generic `GameEvent { owner, source_id, code, values }` envelope from PRD 03 / PRD 50. Update the colonisation PRD before backend work so implementation targets an agreed API shape.

- [x] Update `docs/prd/16-colonisation.md` event examples to the generic event envelope
- [ ] Define canonical event codes for colonisation:
  - [x] `colonisation.colonised`
  - [x] `colonisation.failed`
- [x] Define the ordered `values` payload for each event, including the failure `reason`
- [x] Note that turn 0 colony ship seeding is already implemented separately and is not part of this task

Validation:
- [x] Docs sanity pass: PRD 16 event examples match the generic event model used in `docs/prd/03-turn-lifecycle.md` and `docs/prd/50-api.md`

---

## Step 2: Extend colonise task schema and shared constants

Teach the engine models about the new waypoint task and centralise the colony ship dismantle numbers so movement logic can use them deterministically.

- [x] Update `backend/openstars/engine/models.py`:
  - [x] Extend `WaypointTask.type` to include `"colonize"`
- [x] Add shared colonisation constants for the predefined `colony_ship` hull:
  - [x] `DISMANTLE_RECOVERY = 0.333`
  - [x] construction cost / recovered mineral values used by the resolver
- [x] Decide the best home for those constants so they can be reused cleanly by tests and resolution code

Unit tests:
- [x] Add or update backend model tests to confirm `set_waypoints` accepts a `"colonize"` task with no extra fields
- [x] Add a regression test for colony ship dismantle recovery values (1 Fe / 1 Bo / 5 Ge per ship)

Validation:
- [x] `cd backend && uv run pytest tests/engine/test_setup.py tests/server/test_api.py`

---

## Step 3: Add a pure colonisation resolver module

Create a dedicated resolver for colonisation so the movement step stays readable and the core rules are unit-testable in isolation.

- [x] Add `backend/openstars/engine/resolve_steps/colonisation.py`
- [x] Implement helpers for:
  - [x] detecting whether a fleet has any `colony_ship` entries
  - [x] collecting all colony ship entries from fleet composition
  - [x] computing recovered minerals from dismantled colony ships
- [x] Implement `execute_colonize_task(...)` as a pure resolver that:
  - [x] validates the four PRD preconditions (`planet exists`, `planet unowned`, `fleet has colony ship`, `fleet has colonists`)
  - [x] sets `planet.owner`
  - [x] lands all colonists to `planet.population`
  - [x] dismantles all colony ships from the fleet composition
  - [x] deposits recovered minerals plus any carried mineral cargo onto the planet
  - [x] clears fleet cargo after landing
  - [x] reports whether the fleet should be dissolved if no ships remain
  - [x] returns any `GameEvent` objects needed for success or failure
- [x] Keep the resolver deterministic and side-effect free so movement can apply its result cleanly

Unit tests:
- [x] Success case: empty planet becomes owned, population is landed, recovered minerals are deposited, and fleet cargo is cleared
- [x] Success case: fleet with multiple colony ships recovers minerals per ship
- [x] Success case: mixed fleet dismantles only `colony_ship` entries and leaves escorts intact
- [x] Success case: carried mineral cargo is also deposited on the new colony
- [x] Failure case: `no_planet`
- [x] Failure case: `planet_already_owned`
- [x] Failure case: `no_colony_ship`
- [x] Failure case: `no_colonists`
- [x] Event assertions for both `colonisation.colonised` and `colonisation.failed`

Validation:
- [x] `cd backend && uv run pytest tests/engine/test_colonisation.py`

---

## Step 4: Wire colonisation into Step 2 fleet movement

Execute colonisation on waypoint arrival, preserve deterministic fleet order, and remove fleets that fully dismantle themselves.

- [x] Update `backend/openstars/engine/resolve_steps/movement.py`:
  - [x] import and call the new colonisation resolver when `wp.task.type == "colonize"`
  - [x] pass through the planet lookup at the waypoint coordinates
  - [x] update `planets_by_id` / `planets_by_coord` with the colonised planet state
  - [x] remove fleets from `fleets_by_id` when colonisation consumes every ship in the fleet
  - [x] keep surviving non-colony ships in place with remaining waypoints
- [x] Update `move_fleets(...)` so removing a fleet mid-step does not break lexicographic processing or return stale fleets
- [x] Thread any colonisation events into the turn event map from `resolve.py`
- [x] Preserve existing transport / transfer behavior and task execution order

Unit tests:
- [x] Add movement-step tests for a colonise waypoint that dissolves the fleet completely
- [x] Add movement-step tests for a colonise waypoint that leaves a surviving escort fleet
- [x] Add a regression test confirming colonisation runs after arriving at the waypoint, not before movement
- [x] Add a regression test confirming skipped colonise tasks leave fleet movement / waypoint consumption behavior consistent with other tasks

Validation:
- [x] `cd backend && uv run pytest tests/engine/test_movement.py tests/engine/test_colonisation.py`

---

## Step 5: Verify interaction with population and player-state visibility

Colonisation happens in Step 2 and population growth / death happens in Step 6, so newly landed colonists must participate in the same turn's population rules.

- [x] Add backend coverage showing a colony founded on a hostile planet can immediately suffer colonist deaths in the same resolved turn
- [x] Confirm the resulting planet ownership / population state is visible correctly in derived player state after colonisation
- [x] Confirm colonisation events are delivered only to the owning player

Unit tests:
- [x] Add an engine test covering Step 2 colonisation followed by Step 6 hostile-population loss
- [x] Add or update fog / API tests asserting the colonised planet appears as owned to the player after resolve

Validation:
- [x] `cd backend && uv run pytest tests/engine/test_population.py tests/server/test_api.py`

---

## Step 6: Frontend compatibility for colonisation results

This task does not build the full colonise-order UI, but the frontend should understand colonise tasks coming back from the API and render colonisation events cleanly.

- [x] Update `frontend/src/types/game.ts`:
  - [x] extend `WaypointTask.type` to include `"colonize"`
- [x] Add event message templates for:
  - [x] `colonisation.colonised`
  - [x] `colonisation.failed`
- [x] Ensure any existing waypoint/task rendering code handles a `"colonize"` task without crashing, even if editing UI remains deferred
- [x] Leave full colonise task authoring UI to the separate UI task

Unit tests:
- [x] Add or update frontend tests for colonisation event message formatting
- [x] Add a small regression test for rendering a fleet / waypoint payload that includes a `"colonize"` task

Validation:
- [x] `cd frontend && npm test`
- [x] `cd frontend && npm run lint`
- [x] `cd frontend && npx tsc --noEmit`

---

## Step 7: Integration tests over HTTP

Exercise colonisation end-to-end through the real API, following the established `backend/int_tests/` pattern.

- [x] Add `backend/int_tests/test_colonisation.py`
- [x] Cover a successful colonisation flow:
  - [x] create a game
  - [x] load colonists onto the starting colony ship
  - [x] submit a `set_waypoints` command with a `colonize` task
  - [x] resolve the turn
  - [x] assert planet ownership, landed population, mineral recovery, fleet removal or survival, and emitted event
- [x] Cover each failure reason over HTTP:
  - [x] `no_planet`
  - [x] `planet_already_owned`
  - [x] `no_colony_ship`
  - [x] `no_colonists`
- [ ] Add an end-to-end assertion that colonising a hostile world triggers same-turn population loss after resolution

Validation:
- [x] `./backend/int_tests/run.sh`

---

## Step 8: Final quality gate

- [x] `cd backend && uv run ruff check .`
- [x] `cd backend && uv run ruff format --check .`
- [x] `cd backend && uv run pytest`
- [x] `cd frontend && npm run lint`
- [x] `cd frontend && npx tsc --noEmit`
- [x] `cd frontend && npm test`

---

## Notes

- Keep colonisation logic server-authoritative and resolver-driven; the client should never infer colony outcomes locally
- Reuse the existing cargo model from PRD 15 rather than introducing colonisation-specific cargo handling
- Fleet dissolution needs extra care because Step 2 currently iterates fleets in sorted ID order; avoid mutating iteration state in a way that skips fleets or reintroduces removed fleets in the returned list
- Colonisation success and failure should use stable event codes and compact ordered `values`, consistent with the simplified event model
- Full colonise waypoint authoring UI should be tracked separately once the PRD 08 interaction details are agreed
