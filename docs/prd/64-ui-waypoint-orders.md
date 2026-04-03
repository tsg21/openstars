# PRD 64 — UI Waypoint Orders

Part of the UI series — see [PRD 60 — UI Overview](60-ui-overview.md) for layout, design principles, and colour system.

This PRD defines how players create, edit, and submit fleet waypoint orders in the frontend, aligned to backend mechanics in:
- [PRD 10 — Fleet Movement](10-fleet-movement.md)
- [PRD 15 — Freight Transport](15-freight-transport.md)
- [PRD 16 — Colonisation](16-colonisation.md)

The server remains authoritative for movement and task execution. The frontend is an order editor only.

## Goals

- Make waypoint authoring fast from the galaxy map (few clicks, clear feedback).
- Expose advanced waypoint tasking (`transport`, `transfer`, `colonize`) without requiring raw JSON.
- Keep client behaviour deterministic and schema-safe, so submitted commands always match backend expectations.
- Clearly separate **planned orders** (local draft) from **resolved outcomes** (next turn state).

## Non-Goals

- Client-side simulation of movement, cargo flow, or colonisation results.
- Predictive conflict/battle simulation.
- Multi-turn scripting beyond `repeat` route loops already supported by backend.

## Backend Contract (Authoritative)

Waypoint commands are sent through `set_waypoints` for a fleet. The UI must support:

- Full replacement of fleet waypoints on submit.
- Optional `repeat` flag per fleet.
- Waypoint task payloads from backend PRDs:
  - `transport`
  - `transfer`
  - `colonize`

The UI must preserve exact waypoint order because resolution consumes waypoints sequentially and order is gameplay-significant.

## User Stories

- As a player, I can click a fleet and queue multiple destinations.
- As a player, I can assign cargo tasks at the waypoint where the fleet should execute them.
- As a player, I can set a colonize task on a target planet and understand preconditions before submit.
- As a player, I can toggle repeat mode for supply routes.
- As a player, I can review all pending waypoint edits before submitting my turn.

## UX Flow

1. **Select fleet** from map (deep-space) or planet panel (in-orbit).
2. **Enter waypoint edit mode** in fleet detail panel.
3. **Add waypoint** by:
   - Clicking a planet (snaps to planet coordinates), or
   - Clicking deep space (exact coordinates).
4. **Edit waypoint row** in panel:
   - Reorder (future-ready; not required in first version if remove+readd is provided).
   - Remove.
   - Open task editor (`None`, `Transport`, `Transfer`, `Colonize`).
5. **Set fleet repeat toggle** (`on`/`off`).
6. **Review command preview** (human-readable list).
7. **Submit turn**; UI sends canonical command payload.

## Waypoint List Requirements

Each waypoint row shows:

- Index (`1`, `2`, `3`, …)
- Destination label (planet name if known, else coordinates)
- Task chip (`No task`, `Transport`, `Transfer`, `Colonize`)
- Row actions (edit task, delete)

If repeat is enabled, show a loop indicator on the route and in the fleet header.

## Task Editor Requirements

### Shared

- One task max per waypoint.
- Switching task type rewrites task payload for that waypoint.
- Validation is local and blocks invalid submit, but server errors remain source of truth.

### Transport Task

UI supports adding ordered cargo operations with:
- action (`load_all`, `load_amount`, `load_up_to`, `unload_all`, `unload_amount`)
- cargo type (`ironium`, `boranium`, `germanium`, `colonists`)
- optional amount when required

Display operations in execution order because order affects capacity-constrained outcomes.

### Transfer Task

UI supports:
- target fleet selector (same-owner fleets only in current known state)
- ordered transfer operations (`load`/`unload`, cargo type, amount)

If target fleet is not present at execution time, backend skips task; UI should label this as a runtime risk, not a validation error.

### Colonize Task

UI supports planet-target colonize intent at the waypoint.

Pre-submit hints (non-authoritative):
- Fleet has colony ship hull
- Fleet has at least 1 colonist cargo
- Waypoint is on a known planet

If hints fail, show warning state and allow player to decide whether to submit.

## Validation & Error Handling

Client-side validation before submit:

- waypoint coordinates in map bounds
- required numeric amounts are positive integers
- transfer task has target fleet id
- no malformed task payloads

Server-side command rejection (400/409 etc.) is rendered in a persistent error banner with fleet-scoped inline details where possible.

## Data Model (Frontend)

Use camelCase frontend types mapped to API snake_case in the API client layer.

```ts
type FleetWaypointDraft = {
  x: number;
  y: number;
  task: WaypointTaskDraft | null;
};

type WaypointTaskDraft =
  | { type: "transport"; orders: CargoOrderDraft[] }
  | { type: "transfer"; fleetId: string; orders: TransferOrderDraft[] }
  | { type: "colonize" };
```

Fleet draft state includes:
- `fleetId`
- `waypoints: FleetWaypointDraft[]`
- `repeat?: boolean`
- `dirty: boolean` (unsaved local edits)

## Command Payload Examples

### Movement-only route

```json
{
  "type": "set_waypoints",
  "fleet_id": "FL9qb7w1",
  "waypoints": [
    { "x": 550148141952, "y": 549755867136 },
    { "x": 549311406080, "y": 549956141056 }
  ]
}
```

### Repeating transport route

```json
{
  "type": "set_waypoints",
  "fleet_id": "FL9qb7w1",
  "repeat": true,
  "waypoints": [
    {
      "x": 550148141952,
      "y": 549755867136,
      "task": {
        "type": "transport",
        "orders": [
          { "action": "load_all", "cargo_type": "germanium" }
        ]
      }
    },
    {
      "x": 549311406080,
      "y": 549956141056,
      "task": {
        "type": "transport",
        "orders": [
          { "action": "unload_all", "cargo_type": "germanium" }
        ]
      }
    }
  ]
}
```

### Colonize destination

```json
{
  "type": "set_waypoints",
  "fleet_id": "FLp4h8e2",
  "waypoints": [
    {
      "x": 550001000000,
      "y": 549900000000,
      "task": { "type": "colonize" }
    }
  ]
}
```

## Interaction States

- **Clean:** no local edits.
- **Dirty:** local edits present, not submitted.
- **Submitted:** server accepted commands for current turn.
- **Outdated:** turn advanced; local draft discarded or migrated via explicit UX.

## Accessibility

- Full keyboard navigation in waypoint list and task editor.
- Visible focus states on map-interaction controls.
- Icon + text labels for task types (not colour-only).
- Error messages announced via ARIA live region.

## Acceptance Criteria

1. Player can create, remove, and clear waypoints for any owned fleet.
2. Player can attach `transport`, `transfer`, and `colonize` tasks to waypoints.
3. Player can toggle `repeat` and see route-loop indication.
4. Submit serializes to valid `set_waypoints` payload using snake_case fields in transport.
5. Reload restores submitted commands from `GET /commands` into editable UI state.
6. Invalid drafts are blocked client-side with actionable inline feedback.
7. Backend errors are surfaced without losing local edits.

## Dependencies

- PRD 10 movement semantics (waypoint ordering and consumption)
- PRD 15 task schema (`transport`, `transfer`) and `repeat`
- PRD 16 task schema (`colonize`)
- PRD 50 commands API (`POST/GET /commands`)

## Future Extensions

- Drag-to-reorder waypoints directly on map and in list.
- Waypoint templates (patrol loop, shuttle loop, colonize run).
- Conflict/risk overlays (enemy scanner coverage, known minefields) while plotting.
