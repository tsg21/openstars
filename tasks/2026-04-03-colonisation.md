# Colonisation (PRD 16)

Implement the remaining colonisation work from `docs/prd/16-colonisation.md`: the `colonize` waypoint task, colony ship dismantling, colony establishment, failure handling, and player-facing events.

## Scope

- Starting turn 0 colony ships are already implemented in `tasks/2026-04-03-starting-colony-ship.md`; do not duplicate that work here
- Primary scope is backend simulation and API-visible behavior
- Frontend layout for creating colonise orders remains a separate follow-up under the UI PRD, but this task should include any lightweight type or event-message support needed so colonisation results display correctly

---

## Step 1: Align PRD 16 with the current event contract

PRD 16 still shows typed event payloads, but the codebase now uses the generic `GameEvent { owner, source_id, code, values }` envelope from PRD 03 / PRD 50. Update the colonisation PRD before backend work so implementation targets an agreed API shape.

- [ ] Update `docs/prd/16-colonisation.md` event examples to the generic event envelope
- [ ] Define canonical event codes for colonisation:
  - [ ] `colonisation.colonised`
  - [ ] `colonisation.failed`
- [ ] Define the ordered `values` payload for each event, including the failure `reason`
- [ ] Note that turn 0 colony ship seeding is already implemented separately and is not part of this task

Validation:
- [ ] Docs sanity pass: PRD 16 event examples match the generic event model used in `docs/prd/03-turn-lifecycle.md` and `docs/prd/50-api.md`

---

## Step 2: Extend colonise task schema and shared constants

Teach the engine models about the new waypoint task and centralise the colony ship dismantle numbers so movement logic can use them deterministically.

- [ ] Update `backend/openstars/engine/models.py`:
  - [ ] Extend `WaypointTask.type` to include `"colonize"`
- [ ] Add shared colonisation constants for the predefined `colony_ship` hull:
  - [ ] `DISMANTLE_RECOVERY = 0.333`
  - [ ] construction cost / recovered mineral values used by the resolver
- [ ] Decide the best home for those constants so they can be reused cleanly by tests and resolution code

Unit tests:
- [ ] Add or update backend model tests to confirm `set_waypoints` accepts a `"colonize"` task with no extra fields
- [ ] Add a regression test for colony ship dismantle recovery values (1 Fe / 1 Bo / 5 Ge per ship)

Validation:
- [ ] `cd backend && uv run pytest tests/engine/test_setup.py tests/server/test_api.py`

---

## Step 3: Add a pure colonisation resolver module

Create a dedicated resolver for colonisation so the movement step stays readable and the core rules are unit-testable in isolation.

- [ ] Add `backend/openstars/engine/resolve_steps/colonisation.py`
- [ ] Implement helpers for:
  - [ ] detecting whether a fleet has any `colony_ship` entries
  - [ ] collecting all colony ship entries from fleet composition
  - [ ] computing recovered minerals from dismantled colony ships
- [ ] Implement `execute_colonize_task(...)` as a pure resolver that:
  - [ ] validates the four PRD preconditions (`planet exists`, `planet unowned`, `fleet has colony ship`, `fleet has colonists`)
  - [ ] sets `planet.owner`
  - [ ] lands all colonists to `planet.population`
  - [ ] dismantles all colony ships from the fleet composition
  - [ ] deposits recovered minerals plus any carried mineral cargo onto the planet
  - [ ] clears fleet cargo after landing
  - [ ] reports whether the fleet should be dissolved if no ships remain
  - [ ] returns any `GameEvent` objects needed for success or failure
- [ ] Keep the resolver deterministic and side-effect free so movement can apply its result cleanly

Unit tests:
- [ ] Success case: empty planet becomes owned, population is landed, recovered minerals are deposited, and fleet cargo is cleared
- [ ] Success case: fleet with multiple colony ships recovers minerals per ship
- [ ] Success case: mixed fleet dismantles only `colony_ship` entries and leaves escorts intact
- [ ] Success case: carried mineral cargo is also deposited on the new colony
- [ ] Failure case: `no_planet`
- [ ] Failure case: `planet_already_owned`
- [ ] Failure case: `no_colony_ship`
- [ ] Failure case: `no_colonists`
- [ ] Event assertions for both `colonisation.colonised` and `colonisation.failed`

Validation:
- [ ] `cd backend && uv run pytest tests/engine/test_colonisation.py`

---

## Step 4: Wire colonisation into Step 2 fleet movement

Execute colonisation on waypoint arrival, preserve deterministic fleet order, and remove fleets that fully dismantle themselves.

- [ ] Update `backend/openstars/engine/resolve_steps/movement.py`:
  - [ ] import and call the new colonisation resolver when `wp.task.type == "colonize"`
  - [ ] pass through the planet lookup at the waypoint coordinates
  - [ ] update `planets_by_id` / `planets_by_coord` with the colonised planet state
  - [ ] remove fleets from `fleets_by_id` when colonisation consumes every ship in the fleet
  - [ ] keep surviving non-colony ships in place with remaining waypoints
- [ ] Update `move_fleets(...)` so removing a fleet mid-step does not break lexicographic processing or return stale fleets
- [ ] Thread any colonisation events into the turn event map from `resolve.py`
- [ ] Preserve existing transport / transfer behavior and task execution order

Unit tests:
- [ ] Add movement-step tests for a colonise waypoint that dissolves the fleet completely
- [ ] Add movement-step tests for a colonise waypoint that leaves a surviving escort fleet
- [ ] Add a regression test confirming colonisation runs after arriving at the waypoint, not before movement
- [ ] Add a regression test confirming skipped colonise tasks leave fleet movement / waypoint consumption behavior consistent with other tasks

Validation:
- [ ] `cd backend && uv run pytest tests/engine/test_movement.py tests/engine/test_colonisation.py`

---

## Step 5: Verify interaction with population and player-state visibility

Colonisation happens in Step 2 and population growth / death happens in Step 6, so newly landed colonists must participate in the same turn's population rules.

- [ ] Add backend coverage showing a colony founded on a hostile planet can immediately suffer colonist deaths in the same resolved turn
- [ ] Confirm the resulting planet ownership / population state is visible correctly in derived player state after colonisation
- [ ] Confirm colonisation events are delivered only to the owning player

Unit tests:
- [ ] Add an engine test covering Step 2 colonisation followed by Step 6 hostile-population loss
- [ ] Add or update fog / API tests asserting the colonised planet appears as owned to the player after resolve

Validation:
- [ ] `cd backend && uv run pytest tests/engine/test_population.py tests/server/test_api.py`

---

## Step 6: Frontend compatibility for colonisation results

This task does not build the full colonise-order UI, but the frontend should understand colonise tasks coming back from the API and render colonisation events cleanly.

- [ ] Update `frontend/src/types/game.ts`:
  - [ ] extend `WaypointTask.type` to include `"colonize"`
- [ ] Add event message templates for:
  - [ ] `colonisation.colonised`
  - [ ] `colonisation.failed`
- [ ] Ensure any existing waypoint/task rendering code handles a `"colonize"` task without crashing, even if editing UI remains deferred
- [ ] Leave full colonise task authoring UI to the separate UI task

Unit tests:
- [ ] Add or update frontend tests for colonisation event message formatting
- [ ] Add a small regression test for rendering a fleet / waypoint payload that includes a `"colonize"` task

Validation:
- [ ] `cd frontend && npm test`
- [ ] `cd frontend && npm run lint`
- [ ] `cd frontend && npx tsc --noEmit`

---

## Step 7: Integration tests over HTTP

Exercise colonisation end-to-end through the real API, following the established `backend/int_tests/` pattern.

- [ ] Add `backend/int_tests/test_colonisation.py`
- [ ] Cover a successful colonisation flow:
  - [ ] create a game
  - [ ] load colonists onto the starting colony ship
  - [ ] submit a `set_waypoints` command with a `colonize` task
  - [ ] resolve the turn
  - [ ] assert planet ownership, landed population, mineral recovery, fleet removal or survival, and emitted event
- [ ] Cover each failure reason over HTTP:
  - [ ] `no_planet`
  - [ ] `planet_already_owned`
  - [ ] `no_colony_ship`
  - [ ] `no_colonists`
- [ ] Add an end-to-end assertion that colonising a hostile world triggers same-turn population loss after resolution

Validation:
- [ ] `./backend/int_tests/run.sh`

---

## Step 8: Final quality gate

- [ ] `cd backend && uv run ruff check .`
- [ ] `cd backend && uv run ruff format --check .`
- [ ] `cd backend && uv run pytest`
- [ ] `cd frontend && npm run lint`
- [ ] `cd frontend && npx tsc --noEmit`
- [ ] `cd frontend && npm test`

---

## Notes

- Keep colonisation logic server-authoritative and resolver-driven; the client should never infer colony outcomes locally
- Reuse the existing cargo model from PRD 15 rather than introducing colonisation-specific cargo handling
- Fleet dissolution needs extra care because Step 2 currently iterates fleets in sorted ID order; avoid mutating iteration state in a way that skips fleets or reintroduces removed fleets in the returned list
- Colonisation success and failure should use stable event codes and compact ordered `values`, consistent with the simplified event model
- Full colonise waypoint authoring UI should be tracked separately once the PRD 08 interaction details are agreed
