# UI Fleet Names

Frontend implementation for fleet names and fleet renaming, following the backend support added in `tasks/2026-04-04-fleet-names.md` and the updated UI PRDs:

- `docs/prd/63-ui-fleet-detail.md`
- `docs/prd/64-ui-waypoint-orders.md`

Backend context: player-state payloads now include `name` for owned fleets, and the commands API accepts `rename_fleet`. Enemy fleet names remain hidden by fog of war.

---

## Step 1: Extend frontend types for fleet names and rename commands

Update the shared frontend types so fleet names and `rename_fleet` are first-class in the UI.

- [ ] In `frontend/src/types/game.ts`, add `name?: string | null` to `PlayerFleet`
- [ ] Add `RenameFleetCommand`:
  - `type: "rename_fleet"`
  - `fleetId: string`
  - `name: string`
- [ ] Add `RenameFleetCommand` to the `PlayerCommand` union
- [ ] Confirm existing `keysToCamel` response mapping already exposes backend `name` as `fleet.name` with no extra manual conversion

Unit tests:
- [ ] Type-only changes: no dedicated Vitest needed; covered by `npx tsc --noEmit` in the final validation step

---

## Step 2: Support `rename_fleet` in staged command state

Make rename commands behave like other draft commands: replace per fleet, survive local editing, and appear in the working view before turn submission.

- [ ] In `frontend/src/hooks/useGameState.ts`, update `setCommand` so `rename_fleet` replaces any existing staged rename for the same `fleetId` instead of appending duplicates
- [ ] Keep the existing `set_waypoints` replacement behaviour unchanged
- [ ] In `frontend/src/lib/applyCommands.ts`, apply `rename_fleet` to the matching owned fleet in the derived working player state
- [ ] Silently ignore unknown fleets in `applyCommandsToPlayerState`, matching backend behaviour

Unit tests:
- [ ] `frontend/src/hooks/useGameState.test.tsx` — staging two `rename_fleet` commands for the same fleet keeps only the latest one
- [ ] `frontend/src/lib/applyCommands.test.ts` — `rename_fleet` updates `fleet.name` in the working state
- [ ] `frontend/src/lib/applyCommands.test.ts` — renaming an unknown fleet is ignored without affecting other fleets

---

## Step 3: Serialize and reload rename commands through the API client

Ensure the UI can both submit rename commands and reload them from `GET /commands` for the current turn.

- [ ] Confirm `frontend/src/api/client.ts` submits `rename_fleet` commands unchanged except for normal snake_case conversion
- [ ] Confirm `getCommands()` already maps `rename_fleet` payloads back into camelCase via the shared request helper
- [ ] Add or update fixtures where the frontend assumes only `set_waypoints` and production commands exist

Unit tests:
- [ ] `frontend/src/api/client.test.ts` — submitting a `rename_fleet` command sends `{ type: "rename_fleet", fleet_id, name }`
- [ ] `frontend/src/api/client.test.ts` — `getCommands()` returns `fleetId` in camelCase for `rename_fleet`

---

## Step 4: Add rename draft state in the fleet detail flow

Wire a local rename interaction into the existing detail-panel flow so players can rename owned fleets during the command phase.

- [ ] In `frontend/src/App.tsx`, add fleet-rename draft state:
  - currently edited fleet name
  - whether the fleet header is in rename mode
- [ ] Initialise rename state from the selected fleet's working-view name when entering rename mode
- [ ] Add save/cancel handlers:
  - save stages `gameState.setCommand({ type: "rename_fleet", fleetId, name })`
  - cancel restores the non-editing header state without staging a command
- [ ] Reset transient rename-edit UI state when selection changes or the turn advances
- [ ] Continue to rely on `applyCommandsToPlayerState` so the renamed value appears immediately after staging

Unit tests:
- [ ] `frontend/src/App.test.tsx` — saving a rename stages a `rename_fleet` command
- [ ] `frontend/src/App.test.tsx` — cancelling rename does not stage a command
- [ ] `frontend/src/App.test.tsx` — rename edit state resets when the selected fleet changes

---

## Step 5: Update `FleetDetail` to be name-first and editable

Implement the header and interaction specified in PRD 63.

- [ ] In `frontend/src/components/FleetDetail.tsx`, render the fleet name as the primary heading for owned fleets
- [ ] Add a `Rename` button to the right of the fleet name for owned fleets only
- [ ] When rename mode is active, replace the title with an inline text input and save/cancel controls
- [ ] Show fleet ID as secondary metadata only, in a lower-emphasis style
- [ ] Keep enemy fleet detail name-free; do not fabricate or reveal a name when `fleet.name` is absent
- [ ] Preserve existing waypoint/task UI below the header

Unit tests:
- [ ] `frontend/src/components/FleetDetail.test.tsx` — owned fleets show the fleet name as the primary heading
- [ ] `frontend/src/components/FleetDetail.test.tsx` — enemy fleets do not show a rename button
- [ ] `frontend/src/components/FleetDetail.test.tsx` — rename mode shows an input prefilled with the current name
- [ ] `frontend/src/components/FleetDetail.test.tsx` — fleet ID remains visible only as secondary metadata

---

## Step 6: Replace ID-first fleet labels in other visible UI surfaces

Sweep the current UI for places where we show fleet IDs to the player even when a fleet name is available, and switch them to name-first presentation.

- [ ] In `frontend/src/components/PlanetDetail.tsx`, update the "Fleets in Orbit" section to show the fleet name as the primary row label for owned fleets
- [ ] Where the row needs a stable secondary identifier, keep the fleet ID visually subordinate
- [ ] In any own-fleet selectors inside the waypoint/task UI, prefer `fleet.name` and only fall back to `fleet.id` if `name` is absent
- [ ] Update any test doubles or placeholder render text that still expose fleet IDs as the main label (for example `frontend/src/components/DetailPanel.test.tsx`)

Unit tests:
- [ ] `frontend/src/components/PlanetDetail.test.tsx` — orbiting own fleets render their names
- [ ] `frontend/src/components/WaypointTaskEditor.test.tsx` — own-fleet transfer selector uses fleet names
- [ ] `frontend/src/components/DetailPanel.test.tsx` — fleet detail test stub expectations no longer assume ID-first rendering

---

## Step 7: Validation, polish, and command-error behaviour

Match the PRD details around rename UX and make sure failure states are reasonable.

- [ ] Trim surrounding whitespace before staging the rename command
- [ ] Block empty rename submission in the client UI
- [ ] Support keyboard interaction:
  - `Enter` saves
  - `Escape` cancels
- [ ] If `gameState.error` is set after submit, keep the working-view fleet name and allow the player to correct/resubmit rather than discarding local command state

Unit tests:
- [ ] `frontend/src/components/FleetDetail.test.tsx` — empty rename cannot be saved
- [ ] `frontend/src/components/FleetDetail.test.tsx` — `Enter` saves and `Escape` cancels

---

## Step 8: Frontend quality gate

- [ ] `cd frontend && npm test`
- [ ] `cd frontend && npm run lint`
- [ ] `cd frontend && npx tsc --noEmit`

---

## Step 9: Update backlog/task references

- [ ] Update `tasks/backlog.md` if it contains any fleet-name UI follow-up items superseded by this task
- [ ] If implementation scope changes materially while working, update this task file before moving on
