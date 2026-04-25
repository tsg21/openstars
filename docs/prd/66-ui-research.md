# PRD 66 — Research UI

Part of the UI series — see [PRD 60 — UI Overview](60-ui-overview.md) for layout, design principles, and colour system.

## Overview

The Research UI lets a player see where their six tech fields stand, how much of their planetary output is flowing to research each turn, and change what they are studying. It is the frontend for the research simulation defined in [PRD 21 — Research & Technology](21-research-and-technology.md).

The per-planet "leftover only" production mode toggle lives in the planet detail panel and is specified in [PRD 62 — Planet Detail Panel](62-ui-planet-detail.md); this PRD only cross-references it.

## Design Goals

- **Easy to reach**: Research is a first-class top-bar tab alongside Command and Designer, so the player can reach the editing surface without hunting through secondary controls.
- **Editing in one place**: all research decisions (current field, next field, allocation) are set in a single workspace tab, not scattered through menus.
- **Information density matches the original**: the workspace surfaces all six fields at once with costs, progress, and unlock hints — not one field at a time.
- **Command-and-resolve faithful**: every edit queues a `set_research` command; the workspace never calls the server between opens, and pending edits coexist with other unsubmitted commands.

## Entry Points

### Top-bar Research Tab

The top bar's left-side view selector (PRD 60) includes a `Research` tab when `PlayerState.research` is present:

```
[Command]   [Designer]   [Research]
```

The tab is a clickable button. Clicking it switches the main area to the Research workspace. It does not duplicate the current field, progress, paused state, or ETA in the top bar; those details live inside the workspace.

### Keyboard Shortcut

`R` switches to the Research workspace from anywhere in Command View (provided no text input is focused). Pressing `R` while already in Research returns to Command View.

## Research Workspace

An in-flow workspace tab — the primary editing surface.

### Layout

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  Research                                                              [✕]   │
│                                                                              │
│  Resource Allocation     Current field                 Next field           │
│  [-] 42% [+]             ( Propulsion ▾ )              ( Electronics ▾ )    │
│                                                                              │
│  Current field: ( Propulsion ▾ )        Next field: ( Electronics ▾ )       │
│                                                                              │
│  ────────────────────────────────────────────────────────────────────────    │
│                                                                              │
│  Energy          [██░░░░░░░░]  lvl 2    40 / 130       ▷                    │
│  Weapons         [░░░░░░░░░░]  lvl 0     0 / 50        ▷                    │
│  Propulsion      [█████░░░░░]  lvl 4  2050 / 3790    ● current              │
│  Construction    [█░░░░░░░░░]  lvl 1     0 / 80        ▷                    │
│  Electronics     [████░░░░░░]  lvl 3    95 / 210     ○ next                 │
│  Biotechnology   [░░░░░░░░░░]  lvl 0     0 / 50        ▷                    │
│                                                                              │
│  ────────────────────────────────────────────────────────────────────────    │
│                                                                              │
│  Reserved this turn:               ≈ 412 resources                          │
│  Cost to next level (Propulsion):  3,790 resources                          │
│  Estimated completion:             ≈ 5 turns at current allocation          │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Allocation control

- A numeric input labelled `Resource Allocation`, bound to `allocation_percent`, `0..100`, step `1`, with a visible `%` suffix.
- Visible `-` and `+` buttons decrement/increment the percent by one point for small adjustments.
- The derived "≈ N resources this turn" figure is shown in the bottom summary, computed as `floor(reservable_resources_this_turn * allocation_percent / 100)`. It updates as the number changes.
- Setting the value to `0` dims the per-field rows (no progress will accrue from reserved allocation; leftover-only planets will still contribute).

### Current / Next field selectors

- Two dropdowns above the field list — `current_field` and `next_field`.
- `next_field` includes an explicit `(none)` option for `null`.
- If `current_field` and `next_field` are set to the same value, the UI inlines a note under the selector: *"Same as current — next field will reset to none on apply."* (mirrors the engine behaviour in [PRD 21 command validation](21-research-and-technology.md#set_research).)
- Capped fields (level `26`) are shown but disabled in the `current_field` dropdown; they remain selectable in the `next_field` dropdown only because the user is allowed to queue one (it just won't fire).

### Per-field rows

One row per field, six rows always. Each row shows:

- Field name (label colour keyed to the field — see "Field Colours" below)
- Current level shown as bold text in a small pill immediately to the right of the field name, using the field accent colour and no `lvl` prefix
- Progress bar filled to `progress[f] / (progress[f] + remaining_cost[f])`
- `progress / cost` numeric pair
- Status marker:
  - `● current` on the active field
  - `○ next` on the queued field
  - `▷` click-to-switch affordance on every other field — clicking sets `current_field` to that row

Capped fields (`levels[f] == 26`) show `MAX` instead of the numeric pair and hide the progress bar; the row greys out.

### Cost / ETA summary

Below the per-field rows:

- **Cost to next level** — `progress[current_field] + remaining_cost[current_field]` (recovers the absolute level cost from the projection).
- **Estimated completion** — `ceil(remaining_cost[current_field] / reservable_resources_this_turn_scaled)` turns, where `reservable_resources_this_turn_scaled = floor(reservable_resources_this_turn * allocation_percent / 100)`. If the scaled figure is `0`, show `— (no research income)`.

Both figures recompute as the user changes the allocation percent, using the same formulae the server uses — the allocation control is the only control in the workspace that changes the scaled reservable-resources figure live.

### Interaction Flow

1. Player switches to the Research workspace.
2. The workspace initialises from `PlayerState.research` plus any `set_research` command already queued in the local unsubmitted-commands buffer (so returning to the tab shows pending edits, not the server's pre-edit state).
3. Player adjusts allocation, current field, and/or next field.
4. Each change immediately replaces the pending `set_research` command with only the fields that differ from the committed server state.
5. If the player returns every control to the committed server value, the pending research command is cleared.

Only one pending `set_research` command per turn — each new edit overwrites the previous one in the buffer (consistent with the "last command wins" semantics in PRD 21).

### Field Colours

Each field gets a consistent accent colour used on the label and the progress bar fill. These match the field palette that frontend code shares with the technology browser (see "Deferred"). Initial palette:

| Field          | Accent        |
|----------------|---------------|
| Energy         | `#fbbf24` (amber) |
| Weapons        | `#ef4444` (red) |
| Propulsion     | `#3b82f6` (blue) |
| Construction   | `#a3a3a3` (grey) |
| Electronics    | `#22d3ee` (cyan) |
| Biotechnology  | `#22c55e` (green) |

These are UI-only; they are not game state and will not appear in the backend.

### Keyboard

- **Tab** — move through allocation controls, dropdowns, then the click-to-switch affordance on each row.
- **R** — switch to Research from Command View; return to Command View when already in Research.

## Event Feedback

Level-up events (`research.level_up` — PRD 51) surface through the existing event log in the bottom strip (PRD 60). No dedicated toast or top-bar highlight in the MVP — the event log is the single source of turn-resolution feedback.

## Planet Production Mode

The per-planet `contribute_only_leftover_to_research` toggle is **not** in the Research workspace. It lives on the planet detail panel — see [PRD 62 — Planet Detail Panel](62-ui-planet-detail.md), "Research Contribution" section.

The Research workspace may include a read-only summary line below the per-field rows — *"3 of 7 planets set to leftover-only"* — to let the player know the allocation percent is not governing every planet. The count is derivable client-side from the `PlayerPlanet.contribute_only_leftover_to_research` flags in player state. This summary is cosmetic and may be deferred to a follow-up.

## Command Model

Editing in the Research workspace produces a single `set_research` command, containing only the fields the player changed:

```json
{
  "type": "set_research",
  "current_field": "propulsion",
  "next_field": "electronics",
  "allocation_percent": 42
}
```

Unchanged fields are omitted. An explicit clear of `next_field` sends `"next_field": null`.

Multiple edits within a single turn replace the previous pending command in the local buffer — the client never submits two `set_research` commands for the same turn (the backend allows it but last-wins, so the client deduplicates upfront).

## Constraints and Validation

| Constraint | Behaviour |
|---|---|
| `allocation_percent` in `0..100` | Number input clamps on blur; stepper buttons clamp at the bounds |
| `current_field` in canonical six | Dropdown only lists valid ids |
| Capped field cannot be `current_field` | Capped fields are disabled in the current-field dropdown |
| Reverted controls | Pending research command is cleared when all controls match committed server state |
| Simultaneous edits across tabs | Not supported in MVP; the last applied workspace state wins. A warning banner is deferred. |

## Relationship to Other PRDs

- **PRD 21** — Research simulation, state shape, commands, event codes
- **PRD 60** — Top bar layout (research tab placement), colour system
- **PRD 62** — Planet detail panel (per-planet leftover toggle)
- **PRD 51** — Event codes (`research.level_up` toast source)
- **PRD 20** — Component catalogue (source of tech prerequisites for any Technology Browser follow-up)

## Deferred

- **Technology Browser** — a separate screen listing every component/hull by unlock field and level, with tech prerequisites highlighted relative to the player's current levels. PRD 21 lists this as deferred; it deserves its own sub-PRD in the 60s once the research core lands.
- **Miniaturisation preview** — showing "what will the cost of this component drop to next level?" in either the browser or the designer. Hooks into the build-time miniaturisation in PRD 21.
- **Cross-planet allocation overview** — a compact table showing reserved vs. leftover contribution per planet this turn. Could slot into the Research workspace or the planet detail panel.
- **Allocation presets** — quick buttons (`0%`, `15%`, `50%`, `100%`) near the allocation control. Low value for MVP; defer until the usage pattern is observed.
- **Multi-level-up animation on the progress bar** — when a turn resolves with multiple level-ups in the current field, animate the bar filling, resetting, and advancing. Purely cosmetic.
- **Per-field ETA column** — showing "turns to next level" for every field, not just the current one. Useful but adds workspace complexity; defer until player feedback suggests it.
