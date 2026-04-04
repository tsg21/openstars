# UI Fleet Names

Frontend implementation for fleet names and fleet renaming, following the backend support added in `tasks/2026-04-04-fleet-names.md` and the updated UI PRDs:

- `docs/prd/63-ui-fleet-detail.md`
- `docs/prd/64-ui-waypoint-orders.md`

Backend context: player-state payloads now include `name` for owned fleets, and the commands API accepts `rename_fleet`. Enemy fleet names remain hidden by fog of war.

---

## Step 1: Extend frontend types for fleet names and rename commands

Update the shared frontend types so fleet names and `rename_fleet` are first-class in the UI.

- [x] In `frontend/src/types/game.ts`, add `name?: string | null` to `PlayerFleet`
- [x] Add `RenameFleetCommand`:
  - `type: "rename_fleet"`
  - `fleetId: string`
  - `name: string`
- [x] Add `RenameFleetCommand` to the `PlayerCommand` union
- [x] Confirm existing `keysToCamel` response mapping already exposes backend `name` as `fleet.name` with no extra manual conversion

Unit tests:
- [x] Type-only changes: no dedicated Vitest needed; covered by `npx tsc --noEmit` in the final validation step

---

## Step 2: Support `rename_fleet` in staged command state

Make rename commands behave like other draft commands: replace per fleet, survive local editing, and appear in the working view before turn submission.

- [x] In `frontend/src/hooks/useGameState.ts`, update `setCommand` so `rename_fleet` replaces any existing staged rename for the same `fleetId` instead of appending duplicates
- [x] Keep the existing `set_waypoints` replacement behaviour unchanged
- [x] In `frontend/src/lib/applyCommands.ts`, apply `rename_fleet` to the matching owned fleet in the derived working player state
- [x] Silently ignore unknown fleets in `applyCommandsToPlayerState`, matching backend behaviour

Unit tests:
- [x] `frontend/src/hooks/useGameState.test.tsx` — staging two `rename_fleet` commands for the same fleet keeps only the latest one
- [x] `frontend/src/lib/applyCommands.test.ts` — `rename_fleet` updates `fleet.name` in the working state
- [x] `frontend/src/lib/applyCommands.test.ts` — renaming an unknown fleet is ignored without affecting other fleets

---

## Step 3: Serialize and reload rename commands through the API client

Ensure the UI can both submit rename commands and reload them from `GET /commands` for the current turn.

- [x] Confirm `frontend/src/api/client.ts` submits `rename_fleet` commands unchanged except for normal snake_case conversion
- [x] Confirm `getCommands()` already maps `rename_fleet` payloads back into camelCase via the shared request helper
- [x] Add or update fixtures where the frontend assumes only `set_waypoints` and production commands exist

Unit tests:
- [x] `frontend/src/api/client.test.ts` — submitting a `rename_fleet` command sends `{ type: "rename_fleet", fleet_id, name }`
- [x] `frontend/src/api/client.test.ts` — `getCommands()` returns `fleetId` in camelCase for `rename_fleet`

---

## Step 4: Add rename draft state in the fleet detail flow

Wire a local rename interaction into the existing detail-panel flow so players can rename owned fleets during the command phase.

- [x] In `frontend/src/App.tsx`, add fleet-rename draft state:
  - currently edited fleet name
  - whether the fleet header is in rename mode
- [x] Initialise rename state from the selected fleet's working-view name when entering rename mode
- [x] Add save/cancel handlers:
  - save stages `gameState.setCommand({ type: "rename_fleet", fleetId, name })`
  - cancel restores the non-editing header state without staging a command
- [x] Reset transient rename-edit UI state when selection changes or the turn advances
- [x] Continue to rely on `applyCommandsToPlayerState` so the renamed value appears immediately after staging

Unit tests:
- [x] `frontend/src/App.test.tsx` — saving a rename stages a `rename_fleet` command
- [x] `frontend/src/App.test.tsx` — cancelling rename does not stage a command
- [x] `frontend/src/App.test.tsx` — rename edit state resets when the selected fleet changes

---

## Step 5: Update `FleetDetail` to be name-first and editable

Implement the header and interaction specified in PRD 63.

- [x] In `frontend/src/components/FleetDetail.tsx`, render the fleet name as the primary heading for owned fleets
- [x] Add a `Rename` button to the right of the fleet name for owned fleets only
- [x] When rename mode is active, replace the title with an inline text input and save/cancel controls
- [x] Show fleet ID as secondary metadata only, in a lower-emphasis style
- [x] Keep enemy fleet detail name-free; do not fabricate or reveal a name when `fleet.name` is absent
- [x] Preserve existing waypoint/task UI below the header

Unit tests:
- [x] `frontend/src/components/FleetDetail.test.tsx` — owned fleets show the fleet name as the primary heading
- [x] `frontend/src/components/FleetDetail.test.tsx` — enemy fleets do not show a rename button
- [x] `frontend/src/components/FleetDetail.test.tsx` — rename mode shows an input prefilled with the current name
- [x] `frontend/src/components/FleetDetail.test.tsx` — fleet ID remains visible only as secondary metadata

---

## Step 6: Replace ID-first fleet labels in other visible UI surfaces

Sweep the current UI for places where we show fleet IDs to the player even when a fleet name is available, and switch them to name-first presentation.

- [x] In `frontend/src/components/PlanetDetail.tsx`, update the "Fleets in Orbit" section to show the fleet name as the primary row label for owned fleets
- [x] Where the row needs a stable secondary identifier, keep the fleet ID visually subordinate
- [x] In any own-fleet selectors inside the waypoint/task UI, prefer `fleet.name` and only fall back to `fleet.id` if `name` is absent
- [x] Update any test doubles or placeholder render text that still expose fleet IDs as the main label (for example `frontend/src/components/DetailPanel.test.tsx`)

Unit tests:
- [x] `frontend/src/components/PlanetDetail.test.tsx` — orbiting own fleets render their names
- [x] `frontend/src/components/WaypointTaskEditor.test.tsx` — own-fleet transfer selector uses fleet names
- [x] `frontend/src/components/DetailPanel.test.tsx` — fleet detail test stub expectations no longer assume ID-first rendering

---

## Step 7: Validation, polish, and command-error behaviour

Match the PRD details around rename UX and make sure failure states are reasonable.

- [x] Trim surrounding whitespace before staging the rename command
- [x] Block empty rename submission in the client UI
- [x] Support keyboard interaction:
  - `Enter` saves
  - `Escape` cancels
- [x] If `gameState.error` is set after submit, keep the working-view fleet name and allow the player to correct/resubmit rather than discarding local command state

Unit tests:
- [x] `frontend/src/components/FleetDetail.test.tsx` — empty rename cannot be saved
- [x] `frontend/src/components/FleetDetail.test.tsx` — `Enter` saves and `Escape` cancels

---

## Step 8: Frontend quality gate

- [x] `cd frontend && npm test`
- [x] `cd frontend && npm run lint`
- [x] `cd frontend && npx tsc --noEmit`

---

## Step 9: Update backlog/task references

- [x] Review `tasks/backlog.md` for fleet-name UI follow-up items superseded by this task (none found)
- [x] If implementation scope changes materially while working, update this task file before moving on

---

## Follow-up: Rename state ownership tidy-up

Small refactor after the main fleet-name work: move transient rename-edit UI state out of `App.tsx` and into `FleetDetail`, while still staging commands through the top-level command flow.

- [x] Replace rename-specific prop threading with a generic `onNewCommand` callback from `App.tsx` through `DetailPanel`
- [x] Move `fleetRenameMode` and `editedFleetName` local state into `frontend/src/components/FleetDetail.tsx`
- [x] Keep `rename_fleet` staging top-level by having `FleetDetail` emit a `PlayerCommand` on save
- [x] Reset local rename-edit state when the selected fleet changes

Unit tests:
- [x] `frontend/src/components/FleetDetail.test.tsx` — saving rename emits `rename_fleet` through `onNewCommand`
- [x] `frontend/src/components/FleetDetail.test.tsx` — local rename state resets when the fleet prop changes
- [x] `frontend/src/App.test.tsx` — `App` forwards a new fleet command from the detail panel into `gameState.setCommand`

---

## Follow-up: Waypoint editor state ownership tidy-up

Equivalent cleanup for fleet waypoint editing: move transient waypoint draft UI state out of `App.tsx` and into `FleetDetail`, while still letting the top level own command staging and map integration.

- [x] Replace waypoint-edit prop threading with a `FleetDetail`-owned waypoint editor state
- [x] Expose the active waypoint editor state back to `App.tsx` only as a small map/keyboard bridge
- [x] Keep `set_waypoints` staging top-level by having `FleetDetail` emit a `PlayerCommand` on save
- [x] Reset local waypoint-edit state when the selected fleet or turn changes

Unit tests:
- [x] `frontend/src/components/FleetDetail.test.tsx` — local waypoint editing enables/disables the expected controls
- [x] `frontend/src/components/FleetDetail.test.tsx` — saving waypoint changes emits `set_waypoints` through `onNewCommand`
- [x] `frontend/src/App.test.tsx` — `App` continues to react correctly to waypoint-editor state changes from the detail panel
