# PRD 65 — Fleet Merge / Split UI

Part of the UI series — see [PRD 60 — UI Overview](60-ui-overview.md) for layout, design principles, and colour system.

## Overview

Fleet merge/split lets a player redistribute ships between colocated own fleets in any combination — merging multiple fleets into one, splitting a fleet into several, or doing arbitrary multi-way reshuffles. New fleets can be created and existing fleets can be dissolved, all in a single operation. The same UI applies whether the fleets are at a planet or in deep space.

## When It Appears

The "Manage Fleets" button appears in the fleet detail panel (PRD 63) when there are **two or more own fleets at the same position**. A single fleet at a location has no merge/split affordance.

The button label is **"Manage Fleets at [location]"** (e.g. "Manage Fleets at Sol" or "Manage Fleets at (120, 340)").

Clicking it opens the Fleet Composer.

## Fleet Composer

The Fleet Composer is a modal dialog. It operates on all own fleets currently at the position — the player can make any changes within a single composer session.

### Layout

The composer shows a **matrix** of ship designs (rows) × fleets (columns). Each cell is an editable integer field representing how many ships of that design belong to that fleet after the operation.

```
┌────────────────────────────────────────────────────────────────┐
│  Manage Fleets at Sol                                    [✕]   │
│                                                                │
│  Design          Fleet 1    Fleet 2    [+ New Fleet]          │
│  ─────────────────────────────────────────────────────        │
│  Scout            [ 3 ]      [ 0 ]       [   ]                │
│  Freighter        [ 1 ]      [ 2 ]       [   ]                │
│  Colony Ship      [ 0 ]      [ 1 ]       [   ]                │
│  ─────────────────────────────────────────────────────        │
│  Total              4          3           0                   │
│                                                                │
│  Row totals must equal: Scout 3, Freighter 3, Colony Ship 1   │
│                                                                │
│                                     [Cancel]  [Apply Changes] │
└────────────────────────────────────────────────────────────────┘
```

The row constraint (shown at the bottom) is the total count of each design across all fleets at the location — the sum of each row cannot change. Cells are highlighted in red if a row is over- or under-subscribed, and **Apply Changes** is disabled until all rows are valid.

### Columns

- **One column per existing own fleet.** Fleet names appear as column headers and are inline-editable (same rename mechanic as PRD 63).
- **One "New Fleet" column** — always present, initially empty. Adding any ships to it creates a new fleet. If the player wants more than one new fleet, they click **"+ New Fleet"** to add another column.
- Columns whose total ships reach **zero** are dimmed and labelled "Will be dissolved". The player may re-add ships to prevent dissolution.
- There is no explicit "delete fleet" action — a fleet with zero ships is implicitly dissolved.

### Rows

Only ship designs that have at least one ship somewhere in the current fleets at the location appear as rows. Designs with zero total ships are not shown.

### Interaction Flow

1. Player opens the Fleet Composer from the fleet detail panel.
2. The initial state reflects the current fleet compositions (no changes yet).
3. Player edits cells directly — click or tab into a cell, type a new number.
4. Row totals validate in real-time. Over/under-subscribed rows show a red highlight on the offending cells and the row total.
5. When all rows are valid, **Apply Changes** is enabled.
6. Pressing **Apply Changes** closes the composer and queues the changes as a `merge_split_fleets` command. The local UI reflects the new fleet compositions immediately (optimistic update, same pattern as waypoints).
7. **Cancel** discards all edits and closes.

### Keyboard

- **Tab / Shift-Tab** — move between cells left-to-right, top-to-bottom.
- **Enter** — move to the next cell in the column.
- **Escape** — cancel and close.

### Fast-path actions

Two common operations get dedicated shortcuts above the matrix:

- **Merge All** — moves all ships into the first (leftmost) fleet, zeroing all others. Useful shorthand when the player just wants to consolidate.
- **Split Evenly** — distributes each design as evenly as possible across all existing columns (no new fleet created). Fractional remainders go to the leftmost fleet.

These are convenience buttons; they set cell values as if typed — the player can adjust afterward before applying.

### Empty Location

If a player makes changes that leave *all* fleet columns at zero, the Apply button remains disabled. At least one fleet must survive the operation.

## Command Model

Applying the Fleet Composer produces a single `merge_split_fleets` command.

```json
{
  "type": "merge_split_fleets",
  "position": { "x": 123, "y": 456 },
  "fleets": [
    {
      "fleet_id": "FL9qb7w1",
      "name": "Fleet 1",
      "ships": [
        { "design_id": "DS3abc", "count": 3 },
        { "design_id": "DS7xyz", "count": 1 }
      ]
    },
    {
      "fleet_id": "tmp_new-1",
      "name": "Fleet 3",
      "ships": [
        { "design_id": "DS7xyz", "count": 2 }
      ]
    }
  ]
}
```

- A `fleet_id` beginning with `tmp_` identifies a new fleet being created. The client generates these IDs; they are not real fleet IDs.
- Existing fleets with a real `fleet_id` and zero total ships are dissolved by the server.
- Existing fleets not listed in the command are left unchanged (no ships moved to/from them).
- The server validates that the total ships per design across all listed fleets equals the current totals; it rejects the command if this does not hold.

## Temporary Fleet IDs for New Fleets

New fleets created by a split have no server-assigned ID until the turn resolves. The player may want to set waypoints on these fleets immediately — within the same turn's command set.

### How it works

When the client creates a new fleet column in the Fleet Composer, it generates a **temporary fleet ID** with a `tmp_` prefix (e.g. `tmp_1`, `tmp_2`). IDs are produced by a monotonic integer counter held in memory for the current turn. The counter starts at 1 when a new turn loads and increments each time a new fleet is created. It resets when the next turn arrives — temporary IDs do not survive turn resolution and need not be globally unique.

This ID is used in the `fleet_id` field of the `merge_split_fleets` entry for that fleet, and in any subsequent commands that reference it — exactly like a real fleet ID:

```json
{
  "type": "set_waypoints",
  "fleet_id": "tmp_new-1",
  "waypoints": [
    { "x": 200, "y": 300, "warp": 7 }
  ]
}
```

No other command needs to know whether a fleet ID is temporary or real. The server resolves this transparently: when processing commands it builds a `tmp_id → real_id` mapping from any `merge_split_fleets` commands in the turn, and substitutes real IDs whenever it encounters a `tmp_` fleet ID elsewhere in the command list.

Temporary IDs are scoped to a single turn's command list. They are not persisted and have no meaning after the turn resolves.

### UI behaviour

After the player applies the Fleet Composer, new fleets appear immediately in the local UI (optimistic update) under their temporary ID. The fleet detail panel and waypoint editor treat them identically to real fleets — the player can select them, set waypoints, and rename them without any round-trip to the server.

When the next turn loads, the server-assigned fleet IDs replace the temporary ones. If the server rejects the `merge_split_fleets` command (e.g. ship count mismatch), the placeholder fleets and any commands that referenced their temporary IDs are rolled back together.

## Colocated Fleet Indicator

When multiple own fleets are at the same position, the fleet detail panel shows a small note below the composition section:

> *2 other own fleets here — [Manage Fleets at Sol]*

This is the primary entry point into the Fleet Composer.

The planet detail panel's "Fleets in Orbit" section (PRD 62) also shows a **"Manage Fleets"** button when two or more own fleets are present, as a secondary entry point.

## Constraints and Validation

| Constraint | Behaviour |
|---|---|
| Fleets must be colocated | Button only appears when ≥ 2 own fleets share the exact same position |
| Enemy/neutral fleets excluded | Composer only shows own fleets; other players' fleets at the same location are not listed |
| Row totals must be preserved | Real-time validation; Apply disabled if any row is off |
| At least one surviving fleet | Apply disabled if all columns would be dissolved |
| New fleet name | Auto-generated server-side (e.g. "Fleet #12"); player can rename inline before or after applying |

## Relationship to Other PRDs

- **PRD 60** — UI layout, design principles, colour system
- **PRD 62** — Planet detail panel (Fleets in Orbit secondary entry point)
- **PRD 63** — Fleet detail panel (primary entry point, rename mechanic)
- **PRD 05** — Fleet schema (composition, position)
- **PRD 07** — Turn command schema (where `merge_split_fleets` is registered)
