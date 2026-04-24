# PRD 66 — Research UI

Part of the UI series — see [PRD 60 — UI Overview](60-ui-overview.md) for layout, design principles, and colour system.

## Overview

The Research UI lets a player see where their six tech fields stand, how much of their planetary output is flowing to research each turn, and change what they are studying. It is the frontend for the research simulation defined in [PRD 21 — Research & Technology](21-research-and-technology.md).

The per-planet "leftover only" production mode toggle lives in the planet detail panel and is specified in [PRD 62 — Planet Detail Panel](62-ui-planet-detail.md); this PRD only cross-references it.

## Design Goals

- **Always-visible at a glance**: the current field, its progress, and a rough ETA are in the top bar so the player doesn't have to open a dialog to see "am I close?".
- **Editing in one place**: all research decisions (current field, next field, allocation) are set in a single modal, not scattered through menus.
- **Information density matches the original**: the dialog surfaces all six fields at once with costs, progress, and unlock hints — not one field at a time.
- **Command-and-resolve faithful**: every edit queues a `set_research` command; the dialog never calls the server between opens, and pending edits coexist with other unsubmitted commands.

## Entry Points

### Top-bar Research Indicator

A compact indicator sits in the top bar (PRD 60) between the turn indicator and the Submit button:

```
[Turn 12]   Research: Propulsion · lvl 3 · 42% → lvl 4   [Waiting: 1/3]   [Submit]
```

Contents:

- Field label — current field name
- Current level
- Progress towards next level, as a percentage of `cost_to_next_level`
- Arrow plus the target level when next level is reached (cosmetic; purely "you are heading here")

When the current field is capped at `26`, the indicator reads `Propulsion · lvl 26 · MAX`. When `allocation_percent` is `0` and there are no leftover-only planets contributing, the indicator is dimmed and reads `Research paused`.

The indicator is a clickable button. Clicking it opens the Research dialog.

### Keyboard Shortcut

`R` opens the Research dialog from anywhere in Command View (provided no text input is focused).

## Research Dialog

A modal dialog — the primary editing surface.

### Layout

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  Research                                                              [✕]   │
│                                                                              │
│  Allocation: [──────●────────────]  42%   (≈ 412 resources this turn)       │
│                                                                              │
│  Current field: ( Propulsion ▾ )        Next field: ( Electronics ▾ )       │
│                                                                              │
│  ────────────────────────────────────────────────────────────────────────    │
│                                                                              │
│  Energy          [██░░░░░░░░]  lvl 2    40 / 130       ▷                    │
│  Weapons         [░░░░░░░░░░]  lvl 0     0 / 50        ▷                    │
│  Propulsion      [█████░░░░░]  lvl 4  2050 / 3790    ● current              │
│  Construction    [█░░░░░░░░░]  lvl 1     0 / 80        ▷                    │
│  Electronics     [████░░░░░░]  lvl 3    95 / 210     ○ queued next          │
│  Biotechnology   [░░░░░░░░░░]  lvl 0     0 / 50        ▷                    │
│                                                                              │
│  ────────────────────────────────────────────────────────────────────────    │
│                                                                              │
│  Cost to next level (Propulsion):  3,790 resources                          │
│  Estimated completion:             ≈ 5 turns at current allocation          │
│                                                                              │
│                                                     [Cancel]  [Apply]       │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Allocation slider

- A range input bound to `allocation_percent`, `0..100`, step `1`.
- Live display of the percent and a derived "≈ N resources this turn" figure from `PlayerState.research.estimated_resources_this_turn`.
- Snaps are unnecessary — the original Stars! used a draggable slider with a numeric field beside it, and a plain range + number pair is sufficient here.
- Setting the value to `0` dims the per-field rows (no progress will accrue from reserved allocation; leftover-only planets will still contribute).

### Current / Next field selectors

- Two dropdowns above the field list — `current_field` and `next_field`.
- `next_field` includes an explicit `(none)` option for `null`.
- If `current_field` and `next_field` are set to the same value, the UI inlines a note under the selector: *"Same as current — next field will reset to none on apply."* (mirrors the engine behaviour in [PRD 21 command validation](21-research-and-technology.md#set_research).)
- Capped fields (level `26`) are shown but disabled in the `current_field` dropdown; they remain selectable in the `next_field` dropdown only because the user is allowed to queue one (it just won't fire).

### Per-field rows

One row per field, six rows always. Each row shows:

- Field name (label colour keyed to the field — see "Field Colours" below)
- Progress bar filled to `progress[f] / cost_to_next_level_for_f`
- Level integer
- `progress / cost` numeric pair
- Status marker:
  - `● current` on the active field
  - `○ queued next` on the queued field
  - `▷` click-to-switch affordance on every other field — clicking sets `current_field` to that row

Capped fields (`levels[f] == 26`) show `MAX` instead of the numeric pair and hide the progress bar; the row greys out.

`cost_to_next_level_for_f` for fields other than `current_field` is computed client-side via the same formula as the projection (`base_cost(level_f) + 10 * total_levels`). The cost formula table is shipped to the client as static data and does not need to be fetched per-open.

### Cost / ETA summary

Below the per-field rows:

- **Cost to next level** — the server-provided `PlayerState.research.cost_to_next_level`.
- **Estimated completion** — `ceil((cost_to_next_level - progress[current_field]) / estimated_resources_this_turn)` turns. If `estimated_resources_this_turn == 0`, show `— (no research income)`.

Both figures recompute as the user drags the allocation slider, using the same formulae the server uses — the slider is the only control on the dialog that changes `estimated_resources_this_turn` live.

### Interaction Flow

1. Player opens the dialog.
2. Dialog initialises from `PlayerState.research` plus any `set_research` command already queued in the local unsubmitted-commands buffer (so re-opening shows pending edits, not the server's pre-edit state).
3. Player adjusts allocation, current field, and/or next field.
4. **Apply** queues a `set_research` command with only the fields that changed relative to the committed server state. If nothing has changed, Apply is disabled.
5. **Cancel** discards edits and closes.

Only one pending `set_research` command per turn — a new Apply overwrites the previous one in the buffer (consistent with the "last command wins" semantics in PRD 21).

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

- **Tab** — move through allocation slider, dropdowns, then the click-to-switch affordance on each row.
- **Enter** in the allocation number input — apply and close (equivalent to clicking Apply).
- **Escape** — cancel and close.
- **R** — toggle the dialog (same shortcut that opens it also closes it).

## Event Feedback

Level-up events (`research.level_up` — PRD 51) surface through the existing event log in the bottom strip (PRD 60). No dedicated toast or top-bar highlight in the MVP — the event log is the single source of turn-resolution feedback.

## Planet Production Mode

The per-planet `contribute_only_leftover_to_research` toggle is **not** in the Research dialog. It lives on the planet detail panel — see [PRD 62 — Planet Detail Panel](62-ui-planet-detail.md), "Research Contribution" section.

The Research dialog may include a read-only summary line below the per-field rows — *"3 of 7 planets set to leftover-only"* — to let the player know the allocation slider is not governing every planet. The count is derivable client-side from the `PlayerPlanet.contribute_only_leftover_to_research` flags in player state. This summary is cosmetic and may be deferred to a follow-up.

## Command Model

Applying the Research dialog produces a single `set_research` command, containing only the fields the player changed:

```json
{
  "type": "set_research",
  "current_field": "propulsion",
  "next_field": "electronics",
  "allocation_percent": 42
}
```

Unchanged fields are omitted. An explicit clear of `next_field` sends `"next_field": null`.

Multiple dialog applies within a single turn replace the previous pending command in the local buffer — the client never submits two `set_research` commands for the same turn (the backend allows it but last-wins, so the client deduplicates upfront).

## Constraints and Validation

| Constraint | Behaviour |
|---|---|
| `allocation_percent` in `0..100` | Range input enforces bounds; number input clamps on blur |
| `current_field` in canonical six | Dropdown only lists valid ids |
| Capped field cannot be `current_field` | Capped fields are disabled in the current-field dropdown |
| Apply disabled when unchanged | Apply only enables when at least one field differs from the committed state + pending buffer |
| Simultaneous edits across tabs | Not supported in MVP; last-open dialog wins on Apply. A warning banner is deferred. |

## Relationship to Other PRDs

- **PRD 21** — Research simulation, state shape, commands, event codes
- **PRD 60** — Top bar layout (research indicator placement), colour system
- **PRD 62** — Planet detail panel (per-planet leftover toggle)
- **PRD 51** — Event codes (`research.level_up` toast source)
- **PRD 20** — Component catalogue (source of tech prerequisites for any Technology Browser follow-up)

## Deferred

- **Technology Browser** — a separate screen listing every component/hull by unlock field and level, with tech prerequisites highlighted relative to the player's current levels. PRD 21 lists this as deferred; it deserves its own sub-PRD in the 60s once the research core lands.
- **Miniaturisation preview** — showing "what will the cost of this component drop to next level?" in either the browser or the designer. Hooks into the build-time miniaturisation in PRD 21.
- **Cross-planet allocation overview** — a compact table showing reserved vs. leftover contribution per planet this turn. Could slot into the Research dialog or the planet detail panel.
- **Allocation presets** — quick buttons (`0%`, `15%`, `50%`, `100%`) above the slider. Low value for MVP; defer until the slider usage pattern is observed.
- **Multi-level-up animation on the progress bar** — when a turn resolves with multiple level-ups in the current field, animate the bar filling, resetting, and advancing. Purely cosmetic.
- **Per-field ETA column** — showing "turns to next level" for every field, not just the current one. Useful but adds dialog complexity; defer until player feedback suggests it.
