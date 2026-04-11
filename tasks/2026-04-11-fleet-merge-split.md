# Fleet Merge / Split

**PRD:** [65 — Fleet Merge/Split UI](../docs/prd/65-ui-fleet-merge-split.md), [07 — Turn Mechanics](../docs/prd/07-turn-mechanics.md), [05 — Global State](../docs/prd/05-global-state.md)

Implement the fleet merge/split feature end-to-end. Players can redistribute ships between colocated own fleets in any combination, creating and dissolving fleets as needed. New fleets use client-generated `tmp_` IDs so they can receive waypoint orders in the same turn.

---

## Step 1 — Backend: `MergeSplitFleetsCommand` model

**Files:** `backend/openstars/engine/models.py`

Add the new command model. New fleet entries use a `tmp_`-prefixed `fleet_id`; existing fleet entries use a real `FL…` ID.

```python
class MergeSplitFleetEntry(BaseModel):
    fleet_id: str           # real FL… ID or tmp_… for new fleets
    name: str | None = None # optional rename; None = keep current / auto-generate
    ships: list[FleetComposition]

class MergeSplitFleetsCommand(BaseModel):
    type: Literal["merge_split_fleets"] = "merge_split_fleets"
    fleets: list[MergeSplitFleetEntry]
```

Add `MergeSplitFleetsCommand` to the `PlayerCommand` union (the `Annotated` discriminated union in models.py).

- [x] Add `MergeSplitFleetEntry` and `MergeSplitFleetsCommand` models
- [x] Add `MergeSplitFleetsCommand` to `PlayerCommand` union
- [x] Unit tests in `test_models.py`:
  - valid command round-trips through JSON
  - command with `tmp_` fleet IDs is accepted
  - command with `name: null` is accepted

---

## Step 2 — Backend: apply `merge_split_fleets` command

**Files:** `backend/openstars/engine/resolve_steps/commands/merge_split_fleets.py` (new), `backend/openstars/engine/resolve_steps/apply_commands.py`

Implement the resolution logic per PRD 07 Step 1:

1. For each entry with a `tmp_` fleet ID: allocate a real ID via `ids.next_fleet_id(ctx)`, create the fleet at the given position, record `tmp_id → real_id` in a local map.
2. For each entry with a real fleet ID: update composition and (if provided) name.
3. Dissolve fleets with zero total ships (remove from `ctx.fleets_by_id`).
4. Distribute fuel and cargo proportionally across resulting fleets (see below).
5. After processing this player's `merge_split_fleets` command, substitute any `tmp_` IDs in subsequent commands in that player's list before they are dispatched.

**Fuel and cargo distribution** (per PRD 07):
- For fuel: `share = floor(total_fuel * fleet_fuel_capacity / sum_capacities)`. Remainder goes to the fleet with the largest capacity (tie-break: lexicographic fleet ID, `tmp_` IDs sort after real IDs).
- For cargo: same formula, but applied per cargo type independently (ironium, boranium, germanium, colonists), using `cargo_capacity` as the denominator.
- Fleet with zero capacity receives nothing. If total capacity is zero, resource is lost.

Fuel capacity is derived at runtime: `sum(design.fuel_capacity * entry.count for ...)`. Cargo capacity similarly.

Wire up in `apply_commands.py`: handle `MergeSplitFleetsCommand`. After allocating real IDs for any `tmp_` entries, do a find-and-replace pass over the remaining commands in that player's list — substituting each `tmp_` ID string with the real ID everywhere it appears — before continuing dispatch.

- [x] `merge_split_fleets.py`: new fleet creation with `next_fleet_id`
- [x] `merge_split_fleets.py`: existing fleet composition + name update
- [x] `merge_split_fleets.py`: fleet dissolution (zero-ship columns)
- [x] `merge_split_fleets.py`: proportional fuel distribution
- [x] `merge_split_fleets.py`: proportional cargo distribution (per type)
- [x] `apply_commands.py`: dispatch `MergeSplitFleetsCommand`; find-and-replace `tmp_` IDs in the remaining command list before continuing
- [x] Unit tests in `test_merge_split_fleets.py`:
  - merge two fleets into one: correct composition, dissolved fleet removed
  - split one fleet into two: both created with correct compositions
  - new fleet gets a real ID; `tmp_` references in subsequent `set_waypoints` resolve correctly
  - fuel distributed proportionally; remainder goes to largest-capacity fleet
  - cargo distributed proportionally per type
  - fleet with zero ships is dissolved
  - command rejected if ship totals don't match current state (server-side validation)
  - command rejected if any listed fleet is not owned by the commanding player

---

## Step 3 — Backend: command validation

**Files:** `backend/openstars/engine/resolve_steps/apply_commands.py` (or a dedicated validator)

Validate `merge_split_fleets` before applying:

- All listed real fleet IDs must be owned by the commanding player and exist at the given position
- Total ships per design across all listed fleets must equal the totals currently held by those fleets
- At least one resulting fleet must have ships (can't dissolve all fleets)
- `tmp_` IDs must not clash with existing fleet IDs or with each other within the command

Raise a descriptive error (consistent with existing command validation errors) on failure — the whole turn command list is rejected.

- [x] Validation logic for `merge_split_fleets`
- [x] Unit tests covering each invalid case above

---

## Step 4 — Frontend: types and `applyCommandsToPlayerState`

**Files:** `frontend/src/types/game.ts`, `frontend/src/lib/applyCommands.ts`

Add the TypeScript types for the new command:

```typescript
export interface MergeSplitFleetEntry {
  fleetId: string;       // real FL… ID or tmp_… for new fleets
  name?: string;
  ships: FleetComposition[];
}

export interface MergeSplitFleetsCommand {
  type: "merge_split_fleets";
  fleets: MergeSplitFleetEntry[];
}
```

Add to `PlayerCommand` union.

In `applyCommandsToPlayerState`, handle `merge_split_fleets`:
- Create new `PlayerFleet` objects for `tmp_` entries (use `tmp_` ID as `id`; composition from the command; no waypoints, no cargo initially — the optimistic view doesn't try to predict fuel/cargo distribution)
- Update composition of existing fleets
- Remove zero-ship fleets from the fleets array
- Apply any `rename_fleet` implied by the `name` field

Also: add a **turn-scoped `tmp_` counter** to the game commands context. Expose `nextTmpFleetId(): string` from `useGameCommands` — returns `tmp_1`, `tmp_2`, etc., resetting when the turn changes.

- [x] `MergeSplitFleetEntry`, `MergeSplitFleetsCommand` types in `game.ts`
- [x] Add to `PlayerCommand` union
- [x] `applyCommandsToPlayerState` handles `merge_split_fleets`
- [x] `tmp_` counter in the commands context (reset on turn change)
- [x] Unit tests in `applyCommands.test.ts`:
  - merge two fleets: one remains, one removed
  - split: new `tmp_` fleet appears in working state
  - existing fleet composition updated correctly

---

## Step 5 — Frontend: Fleet Composer component

**Files:** `frontend/src/components/FleetComposer.tsx` (new), `frontend/src/components/FleetComposer.test.tsx` (new)

Implement the modal Fleet Composer per PRD 65.

**Layout:** matrix of ship designs (rows) × fleets (columns). Each cell is an integer input.

**Column headers:** fleet name, inline-editable. Dimmed + "Will be dissolved" label when column total = 0.

**"+ New Fleet" button:** appends a new blank column using `nextTmpFleetId()`.

**Row validation:** sum of each row must equal the total for that design across all fleets at the location. Highlight cells red when a row is over/under-subscribed. Disable **Apply Changes** until all rows are valid and at least one column has ships.

**Fast-path buttons:**
- **Merge All** — moves all ships to the leftmost fleet column
- **Split Evenly** — distributes each design as evenly as possible across existing columns (no new column); remainder to leftmost

**Keyboard:** Tab/Shift-Tab between cells; Enter advances down the column; Escape cancels.

On **Apply Changes**: build a `MergeSplitFleetsCommand` from current cell state, call `addCommand`, close the modal. The command includes only fleets with ships > 0 (or existing fleets now at zero, so the server dissolves them).

- [x] `FleetComposer.tsx`: matrix layout, column headers, cell inputs
- [x] Inline fleet name editing in column headers
- [x] Row total validation + red highlight
- [x] Apply Changes / Cancel buttons; Apply disabled when invalid
- [x] "Will be dissolved" column label
- [x] "+ New Fleet" button using `nextTmpFleetId()`
- [x] Merge All fast-path
- [x] Split Evenly fast-path
- [x] Keyboard navigation (Tab, Enter, Escape)
- [x] Unit tests in `FleetComposer.test.tsx`:
  - renders correct rows from fleet compositions
  - editing a cell updates totals and triggers validation
  - Apply Changes emits the correct command
  - Apply disabled when row totals invalid
  - Apply disabled when all columns would be dissolved
  - Merge All sets correct cell values
  - Split Evenly distributes correctly (and handles remainder)
  - "+ New Fleet" adds a column

---

## Step 6 — Frontend: entry points

**Files:** `frontend/src/components/FleetDetail.tsx`, `frontend/src/components/PlanetDetail.tsx`

**Fleet detail panel:** when 2+ own fleets share the same position as the selected fleet, show a note below the composition section:

> *N other own fleet(s) here — [Manage Fleets at Sol]*

Clicking opens the Fleet Composer modal, pre-populated with all own fleets at that position.

**Planet detail panel:** in the "Fleets in Orbit" section, when 2+ own fleets are orbiting, show a **"Manage Fleets"** button alongside the fleet list.

Both entry points need the full list of fleets at the position from the working player state — pass them as a prop to `FleetComposer`.

- [x] `FleetDetail.tsx`: colocated fleet note + "Manage Fleets" button
- [x] `PlanetDetail.tsx`: "Manage Fleets" button in Fleets in Orbit section
- [x] Unit tests: button appears only when ≥ 2 own fleets colocated

---

## Step 7 — Integration test

**Files:** `backend/int_tests/test_merge_split.py` (new)

Follow the pattern in `int_tests/test_freight.py`: a `GameClient`-based test class that creates a real game, submits commands over HTTP, resolves turns, and asserts on the resulting player state.

The game starts with two own fleets at the same planet (the scout and freighter that Turn 0 generates for each player — they are already colocated at the home planet).

**Test cases:**

- **Merge:** submit `merge_split_fleets` that moves all ships from the freighter fleet into the scout fleet (giving the scout fleet a mixed composition). Resolve. Assert: only one fleet remains at that position for the player; it has the combined composition; the freighter fleet ID no longer exists in state.

- **Split + waypoints on new fleet:** submit `merge_split_fleets` splitting the scout into two fleets — one keeping the scout, one `tmp_1` getting the freighter ship — followed immediately by a `set_waypoints` command targeting `tmp_1`. Resolve. Assert: two own fleets exist at the home position; the new (non-scout) fleet has a non-`tmp_` ID; that fleet's waypoints match what was submitted.

- **Fuel distribution:** after a merge, assert that the resulting fleet's fuel equals the sum of the two original fleets' fuel (both start full, so total fuel = total capacity).

- **Invalid command rejected:** submit a `merge_split_fleets` where the ship totals don't add up; assert the turn command submission returns an error (or the turn resolves but the command is skipped with an error event — whichever the implementation chooses).

- [x] Setup: create game, identify scout and freighter fleet IDs from Turn 0 state
- [x] Test: merge two fleets; verify one fleet with combined composition remains
- [x] Test: split + `set_waypoints` on `tmp_` fleet; verify new fleet has correct ID and waypoints after resolution
- [x] Test: fuel is summed correctly after merge
- [x] Test: invalid ship totals are rejected
