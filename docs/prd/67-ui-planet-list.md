# PRD 67 — UI Planet List

Part of the UI series — see [PRD 60 — UI Overview](60-ui-overview.md) for layout, design principles, and colour system.

## Overview

The Planet List is a reusable tabular view of the player's known planets. It is the modern equivalent of the original Stars! "Planet List" view (F3): a sortable, filterable table that surfaces the same information density the original gave players when managing many worlds at once.

This PRD defines the list primitive — its data sources, default columns, sort and filter behaviour, selection semantics, and the slots a consumer screen can use to swap in opinionated columns. It does not define any single screen that hosts the list; the first consumer is [PRD 68 — UI Production](68-ui-production.md).

## Design Goals

- **One implementation, many consumers.** Production today; fleet-list, summary view, and bombing/invasion screens later all reuse the same component.
- **Cheap to read.** The default columns answer the player's most common per-planet questions at a glance — owner, population, mines/factories, queue head, resources/turn — without opening the planet detail panel.
- **Cheap to filter.** Free-text search and a small number of toggle filters cover the common slicing tasks; full faceting is out of scope.
- **Single-select for now.** Multi-select / bulk operations are out of scope (see [PRD 13 — Production](13-production.md) for the rationale); the API leaves room for a future `selectedIds: string[]` without a redesign.
- **Data comes from `PlayerState`.** No new API endpoints. The list reads `PlayerState.planets`, optionally falling back to `galaxy.planets` for unscanned entries when the consumer asks for them.

## Entry Points

The list itself has no top-bar entry — each consumer screen mounts it. Initial consumer:

- [PRD 68 — UI Production](68-ui-production.md) — Production view's left pane.

Future consumers (not in scope here) may include a dedicated "Planets" top-bar tab and the bombing/invasion target picker.

## Component API

New component: `frontend/src/components/panels/PlanetList.tsx`.

### Props

```ts
interface PlanetListProps {
  planets: PlayerPlanet[];
  selectedPlanetId: string | null;
  onSelectPlanet: (planetId: string) => void;
  columns: PlanetListColumn[];
  filter?: PlanetListFilter;          // optional; consumers may pass their own
  emptyState?: ReactNode;             // shown when planets is non-empty but filtered set is empty
}
```

- `planets` — already-scoped input. Consumers filter upstream (e.g. Production passes only own planets).
- `selectedPlanetId` / `onSelectPlanet` — controlled selection; the list never owns selection state itself.
- `columns` — ordered list of column descriptors (see below). The consumer decides which columns to show.
- `filter` — optional filter state (search string + a small set of toggles). Omitting `filter` shows no filter controls.
- `emptyState` — custom empty-state node; falls back to a generic message if absent.

### Column descriptor

```ts
interface PlanetListColumn {
  id: string;                         // stable id, e.g. "name", "population", "queue_head"
  header: string;                     // column heading
  align?: "left" | "right";           // default "left"
  width?: string;                     // CSS width hint (e.g. "10rem"), optional
  sortable?: boolean;                 // default true
  sortValue?: (planet: PlayerPlanet) => number | string | null;
  render: (planet: PlayerPlanet) => ReactNode;
}
```

`sortValue` is required when `sortable` is true. Null-sorting: nulls sort *last* regardless of direction (so empty-queue planets don't pollute the top of the sort).

### Default column descriptors

Exported alongside the component as composable building blocks. Consumers import the ones they want:

| Column id        | Header           | Source                                                          | Sort                          |
|------------------|------------------|------------------------------------------------------------------|-------------------------------|
| `name`           | Name             | `planet.name`                                                    | by name (locale-aware)        |
| `owner`          | Owner            | `planet.owner` (or "You" for own)                                | own first, then by username   |
| `population`     | Pop              | `planet.population`                                              | numeric desc by default       |
| `resources`      | Res/turn         | `planet.resources`                                               | numeric desc                  |
| `mines`          | Mines            | `planet.mines`                                                   | numeric desc                  |
| `factories`      | Factories        | `planet.factories`                                               | numeric desc                  |
| `starbase`       | Starbase         | `planet.starbase` (short label: "None" / "Dock" / "+ships")      | by capability rank            |
| `queue_head`     | Building         | first item in `planet.productionQueue` ("—" when empty)          | by item-type label, nulls last|
| `queue_length`   | Q                | `planet.productionQueue.length`                                  | numeric desc                  |
| `scanner`        | Scanner          | `planet.scanner.installed` ("Yes" / "—")                         | installed first               |

Columns that depend on owner-only fields (`production_queue`, `resources`) render `—` for non-own planets; sorts treat them as null.

### Filter shape

```ts
interface PlanetListFilter {
  search: string;                                                  // matches name (case-insensitive)
  toggles: Array<{ id: string; label: string; active: boolean }>;  // consumer-defined toggles
  onChange: (next: PlanetListFilter) => void;
}
```

The list applies `search` against `planet.name`. Toggle predicates are not encoded in the filter state itself — the consumer applies its own toggle logic when computing the `planets` array passed in. The list renders the toggle pills using the array provided so the visuals live in one place.

This is intentional: it keeps the list dumb about what each toggle means while still owning the toggle UI.

## Visual Specification

### Layout

```
┌──────────────────────────────────────────────────────────────────────┐
│  Search [____________]   [□ Empty queue]  [□ Has starbase]  [✕]      │
├──────────────────────────────────────────────────────────────────────┤
│  Name           Pop      Res/turn  Mines  Factories  Building   Q   │
├──────────────────────────────────────────────────────────────────────┤
│ ▸ Earth         312,400     412      24        61    Factory    3   │
│   Mars           54,200     127      18        12    —          0   │
│   Procyon V     128,900     201      19        25    Scout      5   │
└──────────────────────────────────────────────────────────────────────┘
```

- Selected row gets a player-self accent border on the left and a slightly raised surface background.
- Sortable column headers show an arrow indicator on the active sort column.
- Hover shows a muted background to telegraph clickability.
- Rows are clickable across their full width — no per-cell click targets.

### Sorting

- Click a sortable header to set it as the active sort, ascending. Click again to flip to descending. Click a third time to clear the sort and fall back to the default sort.
- Default sort: `name` ascending.
- Sort state is local to the list instance (held in component state); not persisted to URL or `PlayerState`.

### Empty states

- `planets` is empty: render the consumer-provided `emptyState`, or `"No planets to show."` as fallback.
- `planets` is non-empty but the filter excludes everything: render `"No planets match the current filter."` plus a `Clear filter` button that calls `filter.onChange({ ...filter, search: "", toggles: toggles.map(t => ({ ...t, active: false })) })`.

### Keyboard

- `Tab` moves focus into the list; the first focusable element is the search input (when filter is present), otherwise the first row.
- `Up` / `Down` move between rows when focus is inside the list. `Enter` / `Space` selects the focused row.
- `Home` / `End` jump to the first / last row.
- Typing while a row is focused does not type-ahead in the first cut; this is a deferred polish item.

## Selection Semantics

- Single-select. The list never tracks selection state internally — it is fully controlled via `selectedPlanetId` and `onSelectPlanet`.
- Selecting a row never opens a planet panel or changes the galaxy map selection on its own. Cross-screen selection (e.g. selecting a planet here, opening it on the map) is a consumer concern.
- A `null` `selectedPlanetId` is valid — no row is highlighted.

## Data Source

Reads exclusively from `PlayerState.planets`. The list does not fetch.

Fields used by the default columns must be populated on the supplied `PlayerPlanet` records. Consumers that want columns based on data that's only present for own planets (production queue, mineral stockpile, etc.) are expected to filter the input to own planets upstream — this PRD does not gate columns by ownership at render time beyond rendering `—` for missing values.

The list does **not** read from `galaxy.planets`. If a consumer needs to render rows for planets the player has never seen (unlikely but possible), the consumer should synthesise stub `PlayerPlanet` records and pass them in.

## Performance Targets

Initial scale: up to ~200 planets per player. At that size:

- A single render of the list with default columns must stay under 16 ms on a typical desktop browser.
- Sorting and filtering operations are O(n log n) and O(n) respectively; no memoisation gymnastics are needed at this scale, but the component should accept a stable column array (the consumer is expected to define the columns outside render).

Virtualisation is **out of scope**. If we ever ship a galaxy with thousands of planets it becomes worth revisiting — until then, plain rendering is simpler to test and reason about.

## Accessibility

- Rows are real `<button>` elements (or `<tr>` with `role="row"` + `tabindex="0"` if a table semantics is preferred — implementation choice).
- Selected row exposes `aria-selected="true"`.
- Sort indicator on column headers uses `aria-sort` with `ascending` / `descending` / `none`.
- The search input has a visible label or an `aria-label="Search planets"`.

## Relationship to Other PRDs

- **PRD 60 — UI Overview** — overall layout, colour system.
- **PRD 68 — UI Production** — first consumer; uses this list in the left pane of the Production view.
- **PRD 11 — Scanners** — `scan_level` semantics, owner-only fields. The list is unaware of scanner rules; the consumer is expected to pass already-appropriate records.
- **PRD 13 — Production** — `production_queue` shape used by the `queue_head` and `queue_length` default columns.
- **PRD 62 — Planet Detail Panel** — neighbouring planet view. The Planet List can host a "Show on map" or "Open panel" affordance via a custom column if needed; this is a consumer concern.

## Deferred

- **Multi-select** (`selectedIds: string[]`, ctrl/shift-click) — held back per the production-view decision; the column descriptor API does not need to change to add it later.
- **Column reordering / show-hide controls** — consumers ship a fixed column set for now. A persistence layer for per-user column preferences is a future concern.
- **Type-ahead row navigation** — typing a name prefix jumps to the matching row.
- **Saved filter presets** — "Worlds blocked on minerals", "Worlds with no queue", etc.
- **Virtualisation** for very large galaxies.
- **URL-persistent sort and filter state** — keeps screen reload sticky; minor quality-of-life.
