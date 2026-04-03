# UI Waypoint Orders (PRD 64)

Frontend implementation for fleet waypoint editing with waypoint tasks (`transport`, `transfer`) and repeat routes. Colonize task UI is deferred until the PRD 16 colonisation backend is implemented.

Backend context: the backend already supports `Waypoint` (with optional `task`), `WaypointTask` (`transport`/`transfer`), `CargoOrder`, and the `repeat` flag on `SetWaypointsCommand` — all merged in the freight transport task (2026-04-02). The frontend types and UI have not yet been updated to match.

---

## Step 1: Extend frontend types (`frontend/src/types/game.ts`)

Add the cargo and waypoint task models, and update all types that reference waypoints.

- [x] Add `Cargo` type: `ironium: number; boranium: number; germanium: number; colonists: number`
- [x] Add `CargoOrder` type:
  - `action: "load_all" | "load_amount" | "load_up_to" | "unload_all" | "unload_amount" | "unload_but"`
  - `cargoType: "ironium" | "boranium" | "germanium" | "colonists"`
  - `amount?: number | null`
- [x] Add `WaypointTask` type:
  - `type: "transport" | "transfer"` (colonize added later with PRD 16)
  - `orders: CargoOrder[]`
  - `fleetId?: string | null` — transfer tasks only
- [x] Add `Waypoint` type: `x: number; y: number; task?: WaypointTask | null`
- [x] Update `PlayerFleet`:
  - Change `waypoints?: Position[]` → `waypoints?: Waypoint[]`
  - Add `repeat?: boolean | null` — own fleets only
  - Add `cargo?: Cargo | null` — own fleets only
  - Add `cargoCapacity?: number | null` — own fleets only
- [x] Update `SetWaypointsCommand`:
  - Change `waypoints: Position[]` → `waypoints: Waypoint[]`
  - Add `repeat?: boolean | null`
- [x] Add `WaypointDraftState` type (used by App.tsx draft state, defined here for clarity):
  ```ts
  type WaypointDraftState = {
    command: SetWaypointsCommand; // same shape used for submit
    dirty: boolean;
    validationErrors: Record<string, string>;
  };
  ```
- [x] Unit tests (Vitest) — none needed for type-only changes; type correctness is verified by tsc in step 9

---

## Step 2: Fix coordinate truncation in API client (`frontend/src/api/client.ts`)

The existing `submitCommands` function truncates waypoint coordinates but currently strips the `task` field in doing so (lines ~214–217: `{x: Math.trunc(wp.x), y: Math.trunc(wp.y)}`). Fix this to spread the full waypoint.

- [x] In `submitCommands`, change the waypoint mapping to preserve task:
  ```ts
  waypoints: command.waypoints.map((wp) => ({
    ...wp,
    x: Math.trunc(wp.x),
    y: Math.trunc(wp.y),
  })),
  ```
- [x] Unit test: when a `set_waypoints` command with a transport task is submitted, the task is preserved in the serialized payload (check the `integerCommands` mapping result)
- [x] Unit test: the final serialized JSON for a transport task has snake_case keys throughout — `cargo_type` (not `cargoType`), `fleet_id` (not `fleetId`) for transfer tasks — verifying that `keysToSnake` recurses correctly into nested task and order objects

---

## Step 3: Update `applyCommands.ts` to apply `repeat`

The `set_waypoints` handler currently only applies `waypoints` to the fleet. Extend it to also apply `repeat`.

- [x] In the `set_waypoints` branch of `applyCommandsToPlayerState`, update the fleet merge to include `repeat`:
  ```ts
  merged.fleets[fleetIndex] = {
    ...merged.fleets[fleetIndex],
    waypoints: cmd.waypoints,
    ...(cmd.repeat != null && { repeat: cmd.repeat }),
  };
  ```
- [x] Unit test: `applyCommandsToPlayerState` with a `set_waypoints` command that has `repeat: true` sets the fleet's `repeat` field to `true`
- [x] Unit test: `applyCommandsToPlayerState` with a `set_waypoints` command that omits `repeat` (undefined) leaves the fleet's existing `repeat` value unchanged
- [x] Unit test: waypoints with tasks are preserved through `applyCommandsToPlayerState` — the task field is not lost

---

## Step 4: Update App.tsx draft state

Upgrade the waypoint edit state from `Position[]` to `Waypoint[]`, add repeat editing, and expose a task-update callback.

- [x] Change `editedWaypoints` state type from `Position[] | null` to `Waypoint[] | null`
- [x] Add `editRepeat` state: `boolean`, initialized to `false`
- [x] Update `handleEnterWaypointMode` to initialize `editedWaypoints` from `workingFleet.waypoints ?? []` (already `Waypoint[]` after step 1) and `editRepeat` from `workingFleet.repeat ?? false`
- [x] Update `handleAddWaypoint(pos: Position)` to push a full `Waypoint` object: `{ x: pos.x, y: pos.y, task: null }`
- [x] Update `handleSaveWaypoints` to include `repeat: editRepeat` in the `set_waypoints` command:
  ```ts
  gameState.setCommand({
    type: "set_waypoints",
    fleetId: selectedFleet.id,
    waypoints: editedWaypoints,
    repeat: editRepeat,
  });
  ```
- [x] Update `handleRemoveWaypoint(index)` — no change needed (filters by index, works for `Waypoint[]`)
- [x] Update `handleClearAllWaypoints` — sets to `[]`, no change needed
- [x] Add `handleToggleRepeat` callback: `setEditRepeat((r) => !r)`
- [x] Add `handleUpdateWaypointTask(index: number, task: WaypointTask | null)` callback:
  ```ts
  setEditedWaypoints((prev) =>
    prev ? prev.map((wp, i) => (i === index ? { ...wp, task } : wp)) : null
  );
  ```
- [x] Pass `editRepeat`, `onToggleRepeat`, and `onUpdateWaypointTask` through to `DetailPanel`

---

## Step 5: Clear draft on turn advance (App.tsx)

When the turn resolves while the player has the waypoint editor open, `editedWaypoints` and `editRepeat` become stale — they reference last-turn fleet positions and tasks. Add a `useEffect` to exit edit mode cleanly when the turn number changes.

- [x] In App.tsx, add a `useEffect` that watches `gameState.playerState?.turn`:
  ```ts
  useEffect(() => {
    if (waypointEditMode) {
      setWaypointEditMode(false);
      setEditedWaypoints(null);
      setEditRepeat(false);
    }
  }, [gameState.playerState?.turn]);
  ```
- [x] Unit test: when `playerState.turn` increments (simulated by re-rendering with a new turn value), `waypointEditMode` is reset to false and `editedWaypoints` is cleared

---

## Step 6: Update GalaxyMap.tsx (type only)

`GalaxyMap` renders waypoints for route lines and markers — it accesses `.x` and `.y` which exist on both `Position` and `Waypoint`, so no logic changes are needed, only the prop type.

- [x] Change `editedWaypoints` prop type from `Position[] | null` to `Waypoint[] | null`
- [x] Verify the `GalaxyMap.test.tsx` still compiles (no value changes, just types)

---

## Step 7: Fleet detail panel — repeat toggle and task chips (`frontend/src/components/DetailPanel.tsx`)

Update `FleetDetail` to display repeat state and per-waypoint task chips.

- [x] Add props to `FleetDetail`: `editRepeat: boolean`, `onToggleRepeat: () => void`, `onUpdateWaypointTask: (index: number, task: WaypointTask | null) => void`
- [x] Update `editedWaypoints` prop type from `Position[] | null` to `Waypoint[] | null`
- [x] Update `DetailPanelProps` interface to match
- [x] In `FleetDetail`, update the `waypoints` variable (line ~692) to use `Waypoint[]` — the `waypointInfo` entries now carry the full `Waypoint` (including task) not just a `pos: Position`
- [x] Add repeat indicator in the fleet header card (show only for own fleets):
  - When `waypointEditMode`: show a toggle button/checkbox labelled "Repeat route" that calls `onToggleRepeat`, checked when `editRepeat`
  - When not editing: if `fleet.repeat` is true, show a small cycle icon with text "Repeating route"
- [x] In each waypoint row, add a task chip after the destination label:
  - `fleet.waypoints[i].task?.type` or `editedWaypoints[i].task?.type` (depending on edit mode)
  - Chip labels: `None` (no task), `Transport`, `Transfer`
  - Chip styling: subtle badge, different colour per task type (e.g. blue for transport, amber for transfer)
- [x] In edit mode, add an "Edit task" button per waypoint row — clicking sets a local `activeTaskEdit: number | null` state to that index, showing the task editor inline below that row
- [x] Unit tests (`DetailPanel.test.tsx`):
  - Renders task chips for waypoints with tasks
  - Repeat toggle is visible in edit mode
  - "Repeating route" indicator shown when `fleet.repeat` is true and not in edit mode

---

## Step 8: Transport task editor component

Add `WaypointTaskEditor.tsx` in `frontend/src/components/` with a `TransportTaskEditor` component.

The editor allows building an ordered list of cargo operations. It renders inline below the waypoint row when active.

- [x] Create `frontend/src/components/WaypointTaskEditor.tsx`
- [x] `TransportTaskEditor` props: `orders: CargoOrder[]`, `onChange: (orders: CargoOrder[]) => void`
- [x] Render one row per order:
  - Action `<select>`: all six `action` values with human-readable labels (`Load all`, `Load amount`, `Load up to`, `Unload all`, `Unload amount`, `Unload, keep`)
  - Cargo type `<select>`: `ironium`, `boranium`, `germanium`, `colonists`
  - Amount `<input type="number">`: only shown when action is one of `load_amount`, `load_up_to`, `unload_amount`, `unload_but`; min=1
  - Remove button per row
- [x] "Add order" button appends a default order (`load_all`, `ironium`)
- [x] Validation: if amount is required and missing or ≤ 0, show inline error for that row — used in step 10
- [x] Expose a `validateTransportOrders(orders: CargoOrder[]): Record<string, string>` helper function (pure, exported)
- [x] Unit tests:
  - Renders each action type; amount input only shown for amount-requiring actions
  - `validateTransportOrders`: error when amount required and missing; no error when not required; no error when valid amount provided
  - Add order appends default; remove order removes at index

---

## Step 9: Transfer task editor component

Add `TransferTaskEditor` in `WaypointTaskEditor.tsx`.

- [x] `TransferTaskEditor` props: `fleetId: string | null`, `orders: CargoOrder[]`, `ownFleets: PlayerFleet[]`, `onChange: (fleetId: string | null, orders: CargoOrder[]) => void`
- [x] Fleet selector `<select>`: lists `ownFleets` (by name/id); empty option "Select fleet..." when `fleetId` is null
- [x] Below the selector: note "Target fleet must be at this location at resolution time — if absent, task is skipped"
- [x] Same cargo orders list UI as `TransportTaskEditor`
- [x] Expose `validateTransferTask(fleetId: string | null, orders: CargoOrder[]): Record<string, string>` (exported pure function)
- [x] Unit tests:
  - Shows fleet dropdown populated with own fleets
  - `validateTransferTask`: error when `fleetId` is null; no error when set

---

## Step 10: Wire task editor into `DetailPanel.tsx`

Connect `WaypointTaskEditor` to the waypoint row "Edit task" button.

- [x] Import `TransportTaskEditor`, `TransferTaskEditor` from `WaypointTaskEditor.tsx`
- [x] Add local state `activeTaskEdit: number | null` in `FleetDetail` — the waypoint index being edited
- [x] When "Edit task" is clicked for row `i`, set `activeTaskEdit = i`
- [x] Inline below row `i` when `activeTaskEdit === i`:
  - Task type selector: `None`, `Transport`, `Transfer` — switching type replaces the task payload
  - If `Transport` selected: render `<TransportTaskEditor orders={...} onChange={...} />`
  - If `Transfer` selected: render `<TransferTaskEditor fleetId={...} orders={...} ownFleets={...} onChange={...} />`
  - `onChange` calls `onUpdateWaypointTask(i, newTask)`
  - "Close" button sets `activeTaskEdit = null`
- [x] Pass `ownFleets` (own fleets from player state) down to `FleetDetail` via props so `TransferTaskEditor` can populate the fleet dropdown
- [x] Unit tests:
  - Clicking "Edit task" opens the editor for that row
  - Switching from Transport to Transfer resets the task payload
  - Switching to None clears the task (calls `onUpdateWaypointTask(i, null)`)

---

## Step 11: Validation and submit blocking

- [x] In `handleSaveWaypoints` (App.tsx), compute validation errors before saving:
  - For each waypoint with a `transport` task: call `validateTransportOrders(task.orders)`
  - For each waypoint with a `transfer` task: call `validateTransferTask(task.fleetId, task.orders)`
  - Collect errors into a `Record<string, string>` keyed by `"waypoint-{i}-{field}"`
  - If any errors exist, do not call `gameState.setCommand` and do not exit edit mode; display errors inline
- [x] In `FleetDetail`, pass validation errors down and show them per row/per operation field
- [x] The "Done" button in edit mode is disabled (or shows errors) when validation errors are present
- [x] Server-side errors from `gameState.submit` (already surfaced via `gameState.error`) should also show fleet-scoped detail when available; no changes to the submission error flow are needed for this task — the existing `error` state is sufficient

---

## Step 12: Frontend tests (Vitest)

Run all existing tests and ensure they pass with the type changes:

- [x] `cd frontend && npm test` — all tests pass (includes existing `DetailPanel.test.tsx` and `GalaxyMap.test.tsx`)

---

## Step 13: Update backlog (`tasks/backlog.md`)

Mark items completed by this task:

- [x] Mark `[ ] Repeat waypoint routes` → `[x]` — backend support was added in the freight transport task; this task adds the UI toggle and loop indicator
- [x] Mark `[ ] Population transport — load/unload colonists as cargo` → `[x]` — backend treats colonists as a cargo type (PRD 15); this task adds the UI to author transport tasks with `colonists` as a cargo type
- [x] Leave `[ ] Waypoint tasks — load, unload, colonise, remote mine, patrol, transfer, lay mines, scrap` open — transport and transfer are done after this task, but colonize (pending PRD 16), remote mine, patrol, and others remain

---

## Step 14: Lint and type-check

- [x] `cd frontend && npm run lint` — clean
- [x] `cd frontend && npx tsc --noEmit` — no type errors

---

## Notes

- **Colonize task deferred**: PRD 16 colonisation backend has not yet been implemented. `WaypointTask.type` in `models.py` is `Literal["transport", "transfer"]`. Once the PRD 16 backend task is complete, a follow-up task will: extend `WaypointTask.type` to include `"colonize"` in both backend and frontend types, and add the `ColonizeTaskEditor` component (hints: fleet has colony ship, fleet has colonists, waypoint is on a known planet).
- **`Waypoint` vs `Position`**: `Waypoint` has the same `x`, `y` fields as `Position` plus an optional `task` — it's a structural superset. GalaxyMap coordinate calculations work unchanged; only type annotations need updating.
- **Reload restores draft from server**: when the page loads, `useGameState` fetches submitted commands via `GET /commands` and applies them via `applyCommandsToPlayerState`. Since the working player state already reflects submitted commands (including waypoint tasks), the fleet detail panel will show the correct task chips without extra work. The draft edit state (`editedWaypoints`) is always initialized from the current working fleet waypoints when entering edit mode.
- **`keysToSnake` coverage**: the API client's `keysToSnake` recursively converts object keys — it handles nested `WaypointTask` (camelCase → snake_case) automatically. The only manual conversion needed is the coordinate integer truncation fixed in step 2.
- **Transfer `ownFleets` prop**: `TransferTaskEditor` needs to show a dropdown of the player's own fleets. Pass the `workingPlayerState.fleets.filter(f => f.owner === currentPlayer)` list from App.tsx down through `DetailPanel` → `FleetDetail` → task editor.
