# Freight Transport (PRD 15)

Implements cargo holds, load/unload waypoint tasks, fleet-to-fleet transfer, jettison, and repeat routes. Gives each player a starting small freighter.

## Scope

Backend engine only. No frontend UI changes. UI notes in PRD 15 are deferred.

---

## Step 1: Extend models (`models.py`)

Add cargo types and extend `Design`, `Fleet`, waypoints, and player commands.

- [x] Add `Cargo` model with `ironium: int = 0`, `boranium: int = 0`, `germanium: int = 0`, `colonists: int = 0`
- [x] Add `CargoOrder` model:
  - `cargo_type: str` — `"ironium"` | `"boranium"` | `"germanium"` | `"colonists"`
  - `action: str` — `"load_all"` | `"load_amount"` | `"load_up_to"` | `"unload_all"` | `"unload_amount"` | `"unload_but"`
  - `amount: int | None = None`
- [x] Add `WaypointTask` model:
  - `type: str` — `"transport"` | `"transfer"`
  - `orders: list[CargoOrder] = []`
  - `fleet_id: str | None = None` — transfer tasks only
- [x] Add `Waypoint` model with `x: int`, `y: int`, `task: WaypointTask | None = None`
- [x] Extend `Design` with `cargo_capacity: int = 0`
- [x] Extend `Fleet` with:
  - `cargo: Cargo = Field(default_factory=Cargo)`
  - `repeat: bool = False`
  - Change `waypoints: list[Position]` → `list[Waypoint]`
- [x] Add `JettisonCargoCommand` model:
  - `type: Literal["jettison_cargo"] = "jettison_cargo"`
  - `fleet_id: str`
  - `cargo: Cargo`
- [x] Update `SetWaypointsCommand`:
  - Change `waypoints: list[Position]` → `list[Waypoint]`
  - Add `repeat: bool | None = None`
- [x] Add `JettisonCargoCommand` to the `PlayerCommand` union
- [x] Extend `PlayerFleet` with:
  - `cargo: Cargo | None = None` — owner only
  - `cargo_capacity: int | None = None` — owner only

---

## Step 2: New freight module (`resolve_steps/freight.py`)

Create `backend/openstars/engine/resolve_steps/freight.py` with pure cargo resolution functions.

- [x] `fleet_cargo_capacity(fleet: Fleet, designs_by_id: dict[str, Design]) -> int` — sum of `design.cargo_capacity * count` across composition
- [x] `used_capacity(cargo: Cargo) -> int` — `ironium + boranium + germanium + ceil(colonists / 100)`
- [x] `remaining_capacity(fleet: Fleet, designs_by_id: dict[str, Design]) -> int`
- [x] `resolve_load(action: str, amount: int | None, available: int, held: int, remaining_cap: int) -> int` — returns amount to load (clamped to available and remaining capacity); handles all three load action types
- [x] `resolve_unload(action: str, amount: int | None, held: int) -> int` — returns amount to unload; handles all three unload action types
- [x] `execute_transport_task(fleet: Fleet, planet: PlanetState, task: WaypointTask, designs_by_id: dict[str, Design]) -> tuple[Fleet, PlanetState]` — apply all orders in the task, return updated fleet and planet
- [x] `execute_transfer_task(fleet: Fleet, target_fleet: Fleet, task: WaypointTask, designs_by_id: dict[str, Design]) -> tuple[Fleet, Fleet]` — apply all orders between two co-located fleets
- [x] Colonist capacity: 1 kT holds 100 colonists; use `ceil(colonists / 100)` for capacity usage (199 colonists = 2 kT)
- [x] Unit tests for `resolve_load`:
  - `load_all`: takes all available, capped at remaining capacity
  - `load_amount`: takes exact amount; partial if unavailable
  - `load_up_to`: loads to fill to target; no-op if already at or above target
- [x] Unit tests for `resolve_unload`:
  - `unload_all`: unloads everything held
  - `unload_amount`: unloads exact amount; partial if less held
  - `unload_but`: leaves specified amount behind
- [x] Unit tests for `fleet_cargo_capacity` and `used_capacity`
- [x] Unit tests for colonist capacity rounding — 100 = 1 kT, 101 = 2 kT, 200 = 2 kT

---

## Step 3: Turn 0 generation (`create_game.py`)

Add a small freighter design and fleet for each player.

- [x] Define `SMALL_FREIGHTER_SPEED = 6` and `SMALL_FREIGHTER_CAPACITY = 70` constants alongside existing scout constants
- [x] For each player, after creating the scout design, create a `small_freighter` design:
  - `name="Small Freighter"`, `hull="small_freighter"`, `speed=SMALL_FREIGHTER_SPEED`, `cargo_capacity=SMALL_FREIGHTER_CAPACITY`
  - `scanner=Scanner(normal=0, penetrating=0)` (no scanner)
- [x] For each player, after creating the scout fleet, create a small freighter fleet:
  - Parked at the home planet with empty cargo
  - No waypoints, `repeat=False`
- [x] Update docstring/comment noting two designs and two fleets per player at Turn 0

---

## Step 4: Commands (`resolve_steps/commands.py`)

Handle `jettison_cargo` and the extended `set_waypoints`.

- [x] In `_apply_set_waypoints_command`: change valid waypoint construction from `Position(x=wp.x, y=wp.y)` to `Waypoint(x=wp.x, y=wp.y, task=wp.task)` (preserving task); update fleet reconstruction to include `repeat` (set from `cmd.repeat` if not `None`, else preserve existing `fleet.repeat`)
- [x] Add `_apply_jettison_cargo_command(fleets_by_id, planets_by_id, username, cmd)`:
  - Look up fleet; reject if not owned by `username`
  - Reject if fleet position matches any planet's coordinates (fleet is in orbit)
  - For each non-zero field in `cmd.cargo`, subtract from `fleet.cargo` (clamp at 0, no error on overage)
  - Reconstruct fleet with updated cargo
- [x] Wire `JettisonCargoCommand` into `apply_commands` dispatch

---

## Step 5: Movement with waypoint task execution (`resolve_steps/movement.py`)

Extend `move_fleet` to execute waypoint tasks on arrival and handle `repeat`.

- [x] Add parameters to `move_fleet`: `planets_by_coord: dict[tuple[int,int], PlanetState]`, `fleets_by_id: dict[str, Fleet]`, `designs_by_id: dict[str, Design]`; also accept `planets_by_id: dict[str, PlanetState]` to write back updated planets
- [x] On waypoint arrival (the `dist <= budget` branch), before consuming the waypoint:
  - If `wp.task` is not `None` and `wp.task.type == "transport"`: look up planet at `(wp.x, wp.y)` in `planets_by_coord`; if found, call `execute_transport_task`; update `planets_by_id` and local fleet cargo
  - If `wp.task` is not `None` and `wp.task.type == "transfer"`: look up target fleet by `wp.task.fleet_id` in `fleets_by_id`; if present at same coordinates and same owner, call `execute_transfer_task`; update both fleets in `fleets_by_id`
- [x] Waypoint consumption: if `fleet.repeat` is `True`, append the consumed waypoint to the **end** of the waypoints list instead of discarding it
- [x] Propagate `cargo` and `repeat` fields through to the returned `Fleet` object
- [x] Update `move_fleets` signature to pass the new parameters through; build `planets_by_coord` lookup from `planets_by_id` at the call site in `resolve.py`

---

## Step 6: Fog of war (`fog.py`)

Expose cargo fields to fleet owners.

- [x] In `derive_player_state`, for each `PlayerFleet`: if the fleet is owned by this player, set `cargo` and `cargo_capacity` (compute capacity from fleet composition and designs)
- [x] `cargo` and `cargo_capacity` remain `None` for fleets owned by other players

---

## Step 7: Integration tests (`int_tests/test_freight.py`)

Tests go through the HTTP API against a running backend. Follow the pattern in `int_tests/test_game_lifecycle.py`: create a game, submit commands, resolve a turn, assert on response bodies.

- [x] Turn 0 state includes a small freighter fleet for each player; fleet has `cargo` and `cargo_capacity` fields visible to its owner
- [x] Submit a `set_waypoints` command with a transport task; after resolving, the fleet's cargo matches what was loaded from the planet, and the planet's surface minerals decreased accordingly
- [x] Submit an unload transport task; after resolving, the planet's minerals increased and the fleet's cargo decreased
- [x] Load capped at fleet capacity: request to load more than capacity allows; after resolving, fleet is full and surplus remains on planet
- [x] Fleet with `repeat: true`: after two turns, the fleet has cycled back through its waypoints and executed the task again
- [x] Submit a `jettison_cargo` command; after resolving, the fleet's cargo is reduced by the jettisoned amounts
- [x] Transfer task: two fleets at the same location; after resolving, cargo has moved from one fleet to the other

---

## Step 8: Lint and format

- [x] `cd backend && uv run ruff check .` — clean
- [x] `cd backend && uv run ruff format --check .` — clean

---

## Step 9: Run all tests

- [ ] `cd backend && uv run pytest` — all passing

---

## Notes

- Waypoints in `Fleet` change type from `list[Position]` to `list[Waypoint]`. `Waypoint` has the same `x`/`y` fields so movement arithmetic is unchanged — only the pop/append logic and task dispatch are new
- `resolve_load` and `resolve_unload` are pure functions taking scalars; `execute_transport_task` composes them across a full `WaypointTask`
- Colonist capacity uses ceiling division (199 colonists = 2 kT) to match Stars! behaviour — partial kT is always rounded up when loading
- Transfer tasks are owner-only for now; cross-player transfers are deferred to the diplomacy PRD
- The `planets_by_coord` lookup in the movement step is built once per turn at the `resolve.py` call site — it maps `(planet.position.x, planet.position.y)` to `PlanetState`
- Jettison is applied in Step 1 (commands), before movement, so a fleet can jettison and then move in the same turn
