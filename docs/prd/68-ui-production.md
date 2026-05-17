# PRD 68 — UI Production

Part of the UI series — see [PRD 60 — UI Overview](60-ui-overview.md) for layout, design principles, and colour system.

## Overview

The Production view is a top-level workspace for managing per-planet production queues across all of a player's owned planets. It is the editing surface for [PRD 13 — Production](13-production.md).

Production previously lived inside the right-hand planet detail panel — a compact picker plus a vertical queue. That layout is fine for a single planet but cramped when surveying many worlds and unclear about what is buildable. This PRD moves the full editor into its own workspace, modelled on the existing [PRD 66 — Research UI](66-ui-research.md) flow: a top-bar `Production` tab opens a dedicated, in-flow workspace.

This PRD does not change any production simulation defined in PRD 13. Queue commands, costs, and resolution rules are unchanged.

## Design Goals

- **Sweep across many planets.** The left pane is a planet list (per [PRD 67 — UI Planet List](67-ui-planet-list.md)) so the player can move between worlds without returning to the galaxy map.
- **Production-focused planet context.** The middle pane renders only the planet state that matters for production (resources/turn, minerals, mines/factories, starbase capability) — not a copy of the planet detail panel.
- **Discoverable build options.** The right pane is a build palette listing every queueable item with cost, grouped by category. Replaces the dropdown-style picker.
- **One canonical editor.** The per-planet queue editor in the planet detail panel goes away. The detail panel keeps a read-only queue summary plus a `Manage production →` button that opens this workspace pre-selected to that planet.

## Entry Points

### Top-bar Production tab

The top bar's left-side view selector (PRD 60) gains a `Production` tab alongside Command, Designer, and Research:

```
[Command]   [Production]   [Designer]   [Research]
```

The tab is always visible (unlike Research, which is gated on `PlayerState.research`). It is enabled whenever the player has at least one owned planet; otherwise it is rendered disabled with a tooltip ("No owned planets yet").

### Keyboard shortcut

`P` switches to the Production workspace from anywhere in Command view (provided no text input is focused). Pressing `P` while already in Production returns to Command view. Mirrors the `R` shortcut for Research.

### Planet Detail link

The planet detail panel, on an own detailed-scan planet, shows a `Manage production →` button. Clicking it switches the app to Production mode and selects that planet in the list.

## Workspace Layout

Three panes, left to right, filling the area below the top bar:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  TopBar:  [Command] [Production*] [Designer] [Research]                      │
├────────────────────┬──────────────────────────────────┬──────────────────────┤
│ Planet List        │ Selected planet                  │ Build palette        │
│ (PRD 67)           │                                  │                      │
│                    │  ── summary ────────────────     │  ── categories ──    │
│ Search [______]    │  Earth (you)                     │  Infrastructure      │
│ [□ Empty queue]    │  Res/turn:    412                │   • Mine          5  │
│                    │  Mines / Fac: 24 / 61            │   • Factory      10g │
│ ▸ Earth     Q3     │  Starbase:    Dock (+ships)      │   • Scanner    100r  │
│   Mars      —      │  Minerals:    642 / 213 / 416    │                      │
│   Procyon V Q5     │  Status:      Building (3 left)  │  Ships               │
│   ...              │                                  │   • Scout            │
│                    │  ── queue ──────────────────     │   • Colony Ship      │
│                    │  ≡ Factory ×3   res 6/10   [-+×] │   • Freighter        │
│                    │  ≡ Mine    ×5               [-+×]│   ...                │
│                    │  ≡ Scout   ×2               [-+×]│                      │
│                    │                                  │  (drag or click to   │
│                    │  [ Clear queue ]                 │   add to queue)      │
└────────────────────┴──────────────────────────────────┴──────────────────────┘
```

Default pane widths: left 22%, centre 48%, right 30%. Panes are not user-resizable in the first cut.

### Pane 1 — Planet list

- Uses the `PlanetList` component from PRD 67.
- Source: all planets in `PlayerState.planets` where `planet.owner === currentPlayer`. The list is unconditionally populated with own planets, including brand-new colonies with no factories yet (see "Inclusion rule" below).
- Default columns: `name`, `population`, `resources`, `mines`, `factories`, `queue_head`, `queue_length`.
- Filter:
  - Search by name.
  - Toggle: `Empty queue` — only planets with `productionQueue.length === 0`.
  - Toggle: `Has starbase` — only planets with `planet.starbase != null`.
  - Toggle: `Can build ships` — only planets with `planet.starbase?.canBuildShips === true`.
- Default sort: `name` ascending.
- Selection drives the centre and right panes. A selection is always present once the workspace mounts; on first mount, the list pre-selects (in order of preference): the planet passed in via the `Manage production →` entry point, otherwise the first row.

#### Inclusion rule

All owned planets appear in the list, regardless of `mines + factories` count or starbase presence. This was chosen over a "has production capacity" filter so that brand-new colonies are visible immediately and the player can queue their first mines. The `Empty queue` and `Has starbase` toggles handle the slicing cases the alternative was trying to solve.

### Pane 2 — Selected planet

Renders a production-focused subset of the planet detail panel. The full planet detail panel (PRD 62) is **not** re-mounted here.

Sections, top to bottom:

1. **Header**: planet name, scan-level chip (always "detailed" for own planets per PRD 11), and a small `Show on map` link that returns to Command view with this planet selected. No close affordance — the workspace owns the whole content area.
2. **Production summary**:
   - `Res/turn: <N>` — `planet.resources`. When the planet is set to leftover-only, append ` (leftover only)`.
   - `Mines / Factories: <M> / <F>` — `planet.mines` and `planet.factories`.
   - `Starbase: <label>` — concise capability label (`None`, `Dock`, `Dock (+ships)`, etc.).
   - `Minerals: I / B / G` — surface stockpile per mineral type.
   - `Status: <state>` — derived locally:
     - `Idle` when queue is empty.
     - `Building (<N> remaining)` when queue is non-empty and the first item has `quantity` units left.
     - `Blocked` when the most recent turn's resolution emitted an event indicating the planet's queue blocked (a follow-up; until that hookup lands, render `Building (<N> remaining)`).
3. **Queue editor** — see "Queue editor" below.

The middle pane never shows the full mineral bar chart or habitability chart from PRD 62 — those are not production decisions. Players who want them switch to Command view.

### Pane 3 — Build palette

Categorised list of every queueable item the player can build today. Mirrors the visual treatment of the Designer's component palette (categorised, scrollable, items show cost) without borrowing its drag-onto-grid mechanics.

Categories and items:

| Category        | Items                                                                                          |
|-----------------|------------------------------------------------------------------------------------------------|
| Infrastructure  | Mine, Factory, Planetary Scanner                                                               |
| Ships           | One entry per owned ship design (from `playerState.designs`)                                   |
| Starbases       | Available starbase upgrades for the selected planet (from PRD 17 starbase reference)            |

Each palette row shows:

- Label (item name).
- Cost: resources and per-mineral costs as a compact line (e.g. `10r 4g`).
- A short availability note when the item is not currently queueable on the selected planet (e.g. `Needs starbase`, `Already installed`, `Already queued`). Unavailable rows are visually muted and not clickable.

Click-to-append adds the item to the end of the selected planet's queue. Holding `Shift` while clicking adds with `quantity = 5` (a small ergonomic boost — single click is `quantity = 1`). The palette never reorders existing queue items; reordering is a queue-pane gesture (see below).

### Queue editor

Inside the centre pane. Renders the selected planet's `productionQueue` as an ordered list of rows:

| Element                          | Behaviour                                                              |
|----------------------------------|------------------------------------------------------------------------|
| Drag handle (`≡`)                | Drag a row to reorder within the queue. Uses dnd-kit (already in repo). |
| Item label                       | Item type name, or design name for ships.                              |
| Quantity                         | `× N`. Editable inline via the +/- buttons.                            |
| Progress                         | `res a/b` for the unit currently under construction. Hidden when `a == 0`. |
| `+ / −` quantity controls       | Increment / decrement quantity. Decrementing to 0 removes the row.    |
| `↑ / ↓` arrow controls          | Move the row up / down one position. Keyboard-accessible alternative to drag. |
| Remove button (`×`)              | Removes the row entirely (regardless of quantity).                     |

Below the queue rows:

- `Clear queue` button — disabled when the queue is empty. Confirms via inline danger styling (no separate confirm dialog).

Drag-to-reorder and arrow controls produce the same `move_production_item` command stream as the existing per-planet editor — the queue diff helpers in [frontend/src/lib/productionQueueCommands.ts](../../frontend/src/lib/productionQueueCommands.ts) are reused unchanged.

`planetary_scanner` rows remain a special case from PRD 13:

- Quantity is always 1.
- The `+` quantity control is disabled.
- The palette entry for `Planetary Scanner` is hidden / disabled when the planet already has a scanner installed or already has a queued scanner.

### Empty states

- **No owned planets** — the workspace renders the empty pane structure with a centred message ("Colonise a planet to start producing.") and the top-bar tab is rendered disabled.
- **Selected planet, empty queue** — middle pane queue area shows `Queue empty. Add items from the palette →`. Palette remains active.
- **Selected planet, no matching palette items** — should not happen for own planets, but if it does, palette renders a fallback message ("Nothing available to build right now.").

## Planet Detail Panel Changes

The full per-planet queue editor in [frontend/src/components/panels/PlanetDetail.tsx](../../frontend/src/components/panels/PlanetDetail.tsx) is replaced by:

- A `Production` section with a one-line read-only summary: e.g. `Queue: 3× Factory, 5× Mine, +1 more` or `Queue: empty`.
- A `Manage production →` button that switches mode to Production and selects this planet.

This change is reflected in [PRD 62 — Planet Detail Panel](62-ui-planet-detail.md). The summary is owner-only — gated on ownership alone, since an own planet is always `scan_level: "detailed"` with `scan_age: 0` by construction (PRD 11).

## Command Model

Production view edits use the existing PRD 13 commands — no new command shapes:

- `add_production_item` — palette click.
- `move_production_item` — drag-reorder or arrow buttons.
- `remove_production_item` — `−` quantity (partial) or `×` remove (full).
- `clear_production_queue` — `Clear queue` button.

All edits queue commands through the existing `planet`-scoped dirty buffer (see [frontend/src/hooks/useGameCommands.ts](../../frontend/src/hooks/useGameCommands.ts)). The workspace never calls the server between turn submissions. Switching planets in the planet list does not flush anything — pending edits for any planet persist until the player submits the turn (or returns the controls to the committed state, in which case the queue-command diff resolves to empty).

The set of queue-diff helpers in `productionQueueCommands.ts` is reused unchanged.

## Interaction Flow

1. Player clicks the top-bar `Production` tab (or presses `P`, or clicks `Manage production →` on a planet panel).
2. Workspace mounts; planet list selects the entry planet (or the first row).
3. Player edits the queue via palette clicks, drag-to-reorder, arrow buttons, quantity controls, or `Clear queue`.
4. Each edit immediately produces zero or more PRD 13 commands appended to the `planet`-scoped buffer; the centre pane re-renders against the working queue (the same merging applied today in the planet detail panel).
5. Player switches planets in the list and continues. Pending commands across planets coexist.
6. Player returns to Command view (top-bar tab, `P`, or `Esc`) and submits the turn.

## Keyboard

- `P` — toggle Production / Command view (suppressed when a text input is focused).
- `Esc` — return to Command view from Production.
- `↑` / `↓` — move selection within the planet list when the list has focus.
- Within the queue editor, `Tab` cycles through queue rows; on each row, `↑` / `↓` move the row, `+` / `−` adjust quantity, `Delete` / `Backspace` removes.

## Visual Tokens

Reuse existing tokens:

- `panel-surface`, `--color-panel-border` for pane backgrounds and dividers.
- `--color-player-self` accent for the selected planet row.
- Designer-style palette row hover (`hover:bg-white/8`) for the build palette.

No new colour or spacing tokens are introduced.

## Relationship to Other PRDs

- **PRD 13 — Production** — queue model, commands, costs. Unchanged by this PRD.
- **PRD 17 — Starbases** — gating for ship and starbase production rows in the palette.
- **PRD 18 — Ship Design** — source of design entries for the `Ships` palette category.
- **PRD 60 — UI Overview** — top-bar layout (Production tab placement), colour system.
- **PRD 62 — Planet Detail Panel** — gains the production summary + `Manage production →` link; loses the full queue editor.
- **PRD 67 — UI Planet List** — reusable list primitive used in the left pane.

## Deferred

- **Multi-planet selection / bulk operations.** The architectural pieces (controlled selection in PRD 67, planet-scoped commands in PRD 13) leave room for it. Held back to keep the first cut single-planet.
- **Production templates and apply-to-all.** A follow-up that builds on bulk operations.
- **Turns-to-complete estimate in palette rows and queue rows.** Tracked in [tasks/backlog.md](../../tasks/backlog.md) under Production. Needs a small client-side estimator that takes the planet's `resources` and mineral stockpile and walks the queue.
- **"Blocked by minerals/resources" badge** on planets and queue items, driven by the previous turn's resolution events. Useful but requires an event-source lookup that we don't yet expose to the client cleanly.
- **Pane resizing**.
- **Drag from the palette directly into a queue position** (insert at a specific index). The first cut only supports drag *within* the queue; palette adds always append.
- **Cost preview for the whole queue** (total resources, total minerals) in the centre pane footer.
- **Keyboard type-ahead** in the planet list.
