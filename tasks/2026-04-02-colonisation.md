# Colonisation (PRD 16)

Implements the `colonize` waypoint task, colony ship turn-0 generation, colony establishment, colony ship dismantling, and colonisation events.

## Scope

Backend engine only. No frontend UI changes. UI notes in PRD 16 are deferred.

---

## Step 1: Extend models (`models.py`)

Add the new waypoint task type and colonisation event fields.

- [ ] Extend `WaypointTask.type` to allow `"colonize"` alongside `"transport"` and `"transfer"`
- [ ] Extend `GameEvent` for colonisation events:
  - `colonists_landed: int | None = None`
  - `minerals_recovered: Minerals | None = None`
  - `reason: str | None = None` — `"no_planet"` | `"planet_already_owned"` | `"no_colony_ship"` | `"no_colonists"`
- [ ] Update the file-level comment/docstring to include the new colonisation event types

---

## Step 2: Colonisation helpers (`resolve_steps/colonisation.py`)

Create a pure colonisation module for precondition checks, dismantling recovery, and state updates.

- [ ] Add colony ship constants:
  - `COLONY_SHIP_HULL = "colony_ship"`
  - `DISMANTLE_RECOVERY_NUMERATOR = 1`
  - `DISMANTLE_RECOVERY_DENOMINATOR = 3`
  - `COLONY_SHIP_COST = Minerals(ironium=5, boranium=5, germanium=15)`
- [ ] Add `fleet_has_colony_ship(fleet: Fleet, designs_by_id: dict[str, Design]) -> bool`
- [ ] Add `count_colony_ships(fleet: Fleet, designs_by_id: dict[str, Design]) -> int`
- [ ] Add `recovered_minerals_for_colony_ships(count: int) -> Minerals`
- [ ] Add `resolve_colonize_task(fleet: Fleet, planet: PlanetState | None, designs_by_id: dict[str, Design]) -> tuple[Fleet | None, PlanetState | None, GameEvent]`
  - On failure: return unchanged fleet/planet and a `colonize_failed` event with the appropriate `reason`
  - On success:
    - Set `planet.owner` to `fleet.owner`
    - Set `planet.population` to `fleet.cargo.colonists`
    - Set `fleet.cargo.colonists` to `0`
    - Dismantle all `colony_ship` entries from `fleet.composition`
    - Add dismantle recovery minerals to `planet.minerals`
    - Deposit any remaining fleet mineral cargo onto the planet and zero those fleet cargo fields
    - Return `None` for the fleet if no ships remain after dismantling
    - Emit a `colonised` event containing `colonists_landed` and `minerals_recovered`
- [ ] Unit tests in `backend/tests/engine/test_colonisation.py`:
  - `fleet_has_colony_ship` and `count_colony_ships`
  - Recovery amounts per colony ship and multiplied across multiple colony ships
  - Failure reasons: `no_planet`, `planet_already_owned`, `no_colony_ship`, `no_colonists`
  - Successful colonisation transfers ownership and population
  - Successful colonisation deposits dismantle recovery and remaining fleet minerals on the planet
  - Mixed fleet colonisation removes only the `colony_ship` entries and preserves other ship types
  - Fleet dissolves when all ships in the fleet are colony ships

---

## Step 3: Turn 0 generation (`create_game.py`)

Add a colony ship design and starting fleet for each player.

- [ ] Define `COLONY_SHIP_SPEED = 6` and `COLONY_SHIP_CAPACITY = 25` alongside the existing scout and freighter constants
- [ ] For each player, create a `colony_ship` design:
  - `name="Colony Ship"`
  - `hull="colony_ship"`
  - `speed=COLONY_SHIP_SPEED`
  - `cargo_capacity=COLONY_SHIP_CAPACITY`
  - `scanner=Scanner(normal=0, penetrating=0)`
- [ ] For each player, create one colony ship fleet parked at the home planet with empty cargo, no waypoints, and `repeat=False`
- [ ] Update comments/docstrings noting that Turn 0 now creates three default designs/fleets per player: scout, small freighter, and colony ship
- [ ] Unit tests in `backend/tests/engine/test_create_game.py`:
  - Turn 0 state includes one colony ship design per player
  - Turn 0 state includes one colony ship fleet per player at the homeworld
  - Colony ship design uses `speed=6`, `cargo_capacity=25`, and `hull="colony_ship"`

---

## Step 4: Movement and resolution pipeline (`resolve_steps/movement.py`, `resolve.py`)

Execute `colonize` tasks on waypoint arrival and allow fleets to dissolve cleanly.

- [ ] Extend `_execute_waypoint_task(...)` to handle `wp.task.type == "colonize"` after the existing `transport` and `transfer` branches
  - Look up the planet at `(wp.x, wp.y)` from `planets_by_coord`
  - Call `resolve_colonize_task(...)`
  - Write back any updated planet into `planets_by_id` / `planets_by_coord`
  - If the fleet survives, return the updated fleet
  - If the fleet dissolves, return `None` and record the event
- [ ] Thread colonisation events through movement and back into `resolve_turn`
- [ ] Update `move_fleet` / `move_fleets` signatures and return values as needed so dissolved fleets are removed from global state instead of being recreated as empty fleets
- [ ] In `resolve_turn`, merge colonisation events into `owner_events` before mining
- [ ] Unit tests in `backend/tests/engine/test_movement.py` or `backend/tests/engine/test_colonisation.py`:
  - Colonize task executes on arrival at an unowned planet
  - Colonize task failure still consumes the waypoint and leaves the fleet moving on to subsequent waypoints
  - Colonize task can dissolve the fleet and the dissolved fleet is omitted from the returned fleet list
  - Colonize task does not affect non-target planets or unrelated fleets

---

## Step 5: Integration tests (`int_tests/test_colonisation.py`)

Tests go through the HTTP API against a running backend. Follow `int_tests/test_game_lifecycle.py`: create a game, submit commands, resolve turns, assert on response bodies.

- [ ] Turn 0 owner state includes a colony ship fleet and colony ship design
- [ ] Load colonists onto the colony ship with a `transport` waypoint task, then submit a `colonize` waypoint to an unowned planet; after resolving:
  - The planet owner is set to the player
  - The planet population equals the landed colonists
  - The fleet is removed if it contained only colony ships
  - A `colonised` event is present with `colonists_landed` and `minerals_recovered`
- [ ] Colonising with a mixed fleet leaves non-colony ships in orbit after the colony ship is dismantled
- [ ] Colonising an already owned planet emits `colonize_failed` with `reason="planet_already_owned"`
- [ ] Colonising with no colonists emits `colonize_failed` with `reason="no_colonists"`
- [ ] Colonising empty space emits `colonize_failed` with `reason="no_planet"`
- [ ] Successful colonisation deposits dismantle recovery minerals and any remaining fleet mineral cargo onto the new colony
- [ ] A newly colonised hostile planet is still claimable and is then subject to normal population death on later turns (PRD 14 behaviour)

---

## Step 6: Lint and format

- [ ] `cd backend && uv run ruff check .` — clean
- [ ] `cd backend && uv run ruff format --check .` — clean

---

## Step 7: Run all tests

- [ ] `cd backend && uv run pytest` — all passing

---

## Notes

- The `colonize` task has no extra payload beyond `{"type": "colonize"}` — all colonists currently aboard are landed
- Colonisation runs during Step 2 (movement) on waypoint arrival, alongside other waypoint task execution
- Dismantle recovery is fixed for the pre-defined `colony_ship` hull until the ship designer introduces explicit components and design costs
- A fleet can fail colonisation and still continue along later waypoints in the same turn if it has remaining movement budget
