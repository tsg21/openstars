# Production view — frontend implementation

**Date:** 2026-05-17
**Goal:** Implement the Production workspace described in [PRD 68 — UI Production](docs/prd/68-ui-production.md), backed by the reusable planet-list primitive in [PRD 67 — UI Planet List](docs/prd/67-ui-planet-list.md). Players get a top-bar `Production` tab that opens a three-pane workspace (planet list / selected planet + queue / build palette). The full per-planet queue editor in [PlanetDetail](frontend/src/components/panels/PlanetDetail.tsx) is replaced with a read-only summary and a `Manage production →` button that opens the workspace pre-selected to that planet. All edits queue existing PRD 13 commands through the existing `planet`-scoped dirty buffer — no backend changes.
**Relevant PRDs:** [68 — UI Production](docs/prd/68-ui-production.md), [67 — UI Planet List](docs/prd/67-ui-planet-list.md), [13 — Production](docs/prd/13-production.md), [62 — Planet Detail Panel](docs/prd/62-ui-planet-detail.md), [60 — UI Overview](docs/prd/60-ui-overview.md), [17 — Starbases](docs/prd/17-starbases.md), [18 — Ship Design](docs/prd/18-ship-design.md)

Single-planet only — multi-select / bulk operations and turns-to-complete estimates are deferred (tracked in [tasks/backlog.md](tasks/backlog.md) under Production).

---

## Step 1 — Reusable `PlanetList` component

New module: `frontend/src/components/panels/PlanetList.tsx`.

Implement the component API from [PRD 67](docs/prd/67-ui-planet-list.md):

- [ ] Define and export `PlanetListColumn`, `PlanetListFilter`, and `PlanetListProps` types matching the PRD.
- [ ] Implement controlled selection via `selectedPlanetId` + `onSelectPlanet`. The component never owns selection state.
- [ ] Implement local sort state (active column id + direction). Default sort `name` ascending. Three-click cycle: asc → desc → cleared (returns to default).
- [ ] Null-sort rule: nulls sort last regardless of direction.
- [ ] Render the filter row when `filter` is provided: a search input bound to `filter.search` plus a toggle pill per `filter.toggles[]` entry. All changes call `filter.onChange(next)`. The component does **not** apply toggle predicates — it only renders the controls; the consumer supplies an already-filtered `planets` array. Search-by-name *is* applied inside the component (case-insensitive substring on `planet.name`).
- [ ] Empty states:
  - `planets` empty → render the consumer-provided `emptyState`, or fall back to `"No planets to show."`.
  - Filtered set empty (search excludes all rows) → render `"No planets match the current filter."` + a `Clear filter` button that calls `filter.onChange` with `search: ""` and all toggles `active: false`.
- [ ] Selected row gets a left accent border using `--color-player-self` and a raised surface background.
- [ ] Sortable column headers show an arrow indicator on the active sort column and expose `aria-sort`.

Unit tests in this step (`frontend/src/components/panels/PlanetList.test.tsx`):

- [ ] Renders one row per supplied planet, in default-sorted order (by name).
- [ ] Clicking a row calls `onSelectPlanet(row.id)`.
- [ ] Selected row carries `aria-selected="true"` and the accent class.
- [ ] Clicking a sortable header sorts ascending; clicking again sorts descending; clicking a third time returns to default sort.
- [ ] Null `sortValue`s appear last regardless of direction.
- [ ] Search input filters case-insensitively against `planet.name`.
- [ ] Clearing the filter via the empty-state button calls `filter.onChange` with reset values.
- [ ] Non-sortable columns do not respond to header clicks.

---

## Step 2 — Default column descriptors

New module: `frontend/src/components/panels/planetListColumns.ts`.

Export pre-built `PlanetListColumn` descriptors for the default columns enumerated in [PRD 67](docs/prd/67-ui-planet-list.md):

- [ ] `nameColumn` — `planet.name`, locale-aware sort.
- [ ] `ownerColumn` — display `"You"` for own planets, otherwise `planet.owner` or `"Uncolonised"` for `null`; sort: own first, then by username.
- [ ] `populationColumn` — `planet.population` (or `null`); numeric desc by default.
- [ ] `resourcesColumn` — `planet.resources` (or `null`); numeric desc by default. Renders `—` when null.
- [ ] `minesColumn` — `planet.mines` (or `null`); numeric desc by default.
- [ ] `factoriesColumn` — `planet.factories` (or `null`); numeric desc by default.
- [ ] `starbaseColumn` — short capability label (`None`, `Dock`, `Dock (+ships)`); sort: rank by capability (`canBuildShips` > present > absent).
- [ ] `queueHeadColumn` — first queue item's label (ship design name for `ship`, friendly label otherwise) or `—`; sort by label, nulls last.
- [ ] `queueLengthColumn` — `planet.productionQueue.length`; numeric desc by default.
- [ ] `scannerColumn` — `Yes` / `—`; sort: installed first.

Friendly labels for queue items reuse the existing `PRODUCTION_ITEM_LABELS` constant from [frontend/src/components/panels/PlanetDetail.tsx](frontend/src/components/panels/PlanetDetail.tsx); move that constant into a shared module if it isn't already exported.

Unit tests in this step (`frontend/src/components/panels/planetListColumns.test.ts`):

- [ ] `queueHeadColumn.sortValue` returns `null` for an empty queue and the friendly label otherwise.
- [ ] `starbaseColumn` produces the three expected labels for the three states.
- [ ] `ownerColumn.sortValue` for the current player ranks ahead of any other username.
- [ ] `resourcesColumn.render` returns `—` for a planet missing `resources`.
- [ ] Ship-design names flow through `queueHeadColumn.render` for `ship` queue heads.

---

## Step 3 — Top-bar Production tab

Extend [frontend/src/components/panels/TopBar.tsx](frontend/src/components/panels/TopBar.tsx) to add a `Production` tab.

- [ ] Widen the `mode` prop's discriminated union to include `"production"`. Update `onModeChange` accordingly and propagate the type into [frontend/src/App.tsx](frontend/src/App.tsx).
- [ ] Render the `Production` button immediately after `Command` (before `Designer`). Active styling matches the existing Command/Designer pattern.
- [ ] Add a `productionEnabled: boolean` prop. When `false`, render the button visually muted, disabled, and with a `title="No owned planets yet"` tooltip.
- [ ] No new copy / status badges in the top bar from this tab — workspace details stay inside the workspace.

Unit tests in this step (`frontend/src/components/panels/TopBar.test.tsx`):

- [ ] Production tab renders between Command and Designer.
- [ ] Clicking the tab calls `onModeChange("production")`.
- [ ] `productionEnabled={false}` renders the tab disabled and clicking does not call `onModeChange`.
- [ ] Active mode `"production"` applies the primary variant; other modes apply the ghost variant.
- [ ] Race-selection mode hides the Production tab (matches existing Command/Designer/Research handling).

---

## Step 4 — `ProductionWorkspace` shell

New component: `frontend/src/components/panels/ProductionWorkspace.tsx`. In-flow workspace mounted from `App.tsx` when `mode === "production"`. Follows the layout shape established by [DesignsWorkspace](frontend/src/components/panels/DesignsWorkspace.tsx) and [ResearchWorkspace](frontend/src/components/panels/ResearchWorkspace.tsx).

- [ ] Three-pane CSS grid: left 22% / centre 48% / right 30%, full available height, dividers using `--color-panel-border`.
- [ ] Props:
  - `ownedPlanets: PlayerPlanet[]`
  - `currentPlayer: string`
  - `shipDesigns: ShipDesign[]`
  - `commands: PlayerCommand[]` — committed-state-relative pending commands for use when computing the working queue.
  - `replaceCommands: ReplaceCommands` — the existing planet-scoped helper from `useGameCommands`.
  - `basePlayerState: PlayerState` — used as the diff baseline for `buildPlanetScopeCommands`.
  - `initialPlanetId: string | null` — preselected planet (set by the `Manage production →` entry point); falls back to the first row.
- [ ] Local state:
  - `selectedPlanetId: string | null` — initialised from `initialPlanetId ?? ownedPlanets[0]?.id ?? null`.
  - `filter: PlanetListFilter` — `search: ""`, three toggles (`Empty queue`, `Has starbase`, `Can build ships`), all inactive.
- [ ] Empty-workspace state when `ownedPlanets.length === 0`: render the three-pane chrome with a centred message ("Colonise a planet to start producing.").
- [ ] No manual Save/Cancel controls — every edit auto-buffers (consistent with the existing planet-scoped command flow).

Unit tests in this step (`frontend/src/components/panels/ProductionWorkspace.test.tsx`):

- [ ] Workspace renders three panes when at least one owned planet is supplied.
- [ ] On mount, the planet list and centre pane reflect `initialPlanetId` when provided.
- [ ] When `initialPlanetId` is not provided, the first owned planet (by name) is selected.
- [ ] When `ownedPlanets` is empty, the empty-workspace message renders and no panes are populated.
- [ ] Switching planets in the list updates the centre pane without flushing commands.

---

## Step 5 — Planet list pane (workspace integration)

Inside `ProductionWorkspace`:

- [ ] Mount `<PlanetList>` with the columns from Step 2: `nameColumn`, `populationColumn`, `resourcesColumn`, `minesColumn`, `factoriesColumn`, `queueHeadColumn`, `queueLengthColumn`.
- [ ] Pass the workspace-local `filter` state and a corresponding `onChange` handler.
- [ ] Apply the three toggle predicates upstream (i.e. compute `filteredPlanets` in the workspace and pass that to `PlanetList`):
  - `Empty queue` → `planet.productionQueue.length === 0`.
  - `Has starbase` → `planet.starbase != null`.
  - `Can build ships` → `planet.starbase?.canBuildShips === true`.
- [ ] Plus the workspace also applies search (PlanetList does this internally; the workspace does **not** need to apply search itself — it just passes the filter state through).
- [ ] When toggles change the filtered set such that the currently selected planet is no longer visible, leave the selection alone — selection persists; the centre pane keeps rendering. (Selecting an invisible row is fine; PRD 67 explicitly allows this.)
- [ ] Pre-select rule on mount: `initialPlanetId` if it appears in `ownedPlanets`; otherwise the first row in the *unfiltered* owned-planets list, sorted by name.

Unit tests in this step:

- [ ] Toggling `Empty queue` filters the rows shown but preserves the current selection.
- [ ] Search filters the rows shown (case-insensitive name match).
- [ ] Clearing the filter via the empty-state button resets all toggles and search.

---

## Step 6 — Centre pane: production summary

Inside `ProductionWorkspace`:

- [ ] Render the selected planet's production-focused summary block per [PRD 68 § "Pane 2 — Selected planet"](docs/prd/68-ui-production.md):
  - Header: planet name + scan-level chip (`detailed`) + a `Show on map` link button.
  - `Res/turn: <N>` — `planet.resources`. Append ` (leftover only)` when `planet.contributeOnlyLeftoverToResearch === true`.
  - `Mines / Factories: <M> / <F>` — `planet.mines` and `planet.factories`.
  - `Starbase: <label>` — concise label (`None` / `Dock` / `Dock (+ships)`).
  - `Minerals: I / B / G` — surface stockpile per mineral type, with one decimal where appropriate.
  - `Status: <state>` — derived: `Idle` (empty queue) or `Building (<N> remaining)` (first queue item's `quantity`). `Blocked` is deferred (no client signal yet; render `Building` for now).
- [ ] `Show on map` returns the app to Command mode and selects the planet (via the workspace prop bridge added in Step 12).
- [ ] When `selectedPlanetId == null` (only possible when `ownedPlanets.length === 0`), render the empty-workspace message.

Unit tests in this step:

- [ ] Summary lines render against a fixture own planet with known mineral and queue state.
- [ ] Leftover-only annotation appears when `contributeOnlyLeftoverToResearch === true`.
- [ ] Idle status renders for an empty queue; building status reflects the first item's quantity.
- [ ] `Show on map` calls the supplied prop to switch back to Command mode and select the planet.

---

## Step 7 — Centre pane: queue editor

Inside `ProductionWorkspace`:

- [ ] Render the selected planet's working queue using the same merge logic the planet detail panel uses today (`baseProductionQueue` + pending commands → `productionQueue`). Reuse [buildPlanetScopeCommands](frontend/src/lib/productionQueueCommands.ts) unchanged.
- [ ] One row per queue entry with the columns listed in [PRD 68 § "Queue editor"](docs/prd/68-ui-production.md):
  - Drag handle (`≡`).
  - Item label (ship design name for `ship`, friendly label otherwise).
  - Quantity `× N`.
  - Progress `res a/b` for the unit currently under construction (hidden when `a == 0`).
  - `+` / `−` quantity buttons.
  - `↑` / `↓` reorder buttons.
  - `×` remove-row button.
- [ ] Drag-to-reorder using dnd-kit (already in the repo for the ship designer — reuse the same dependency and patterns from [DragAndDropFitter](frontend/src/components/designer/DragAndDropFitter.tsx)). Drag operates only on existing rows; the palette does not participate.
- [ ] Arrow buttons (`↑` / `↓`) on each row are a keyboard-accessible equivalent to drag.
- [ ] `planetary_scanner` rows: `+` disabled (quantity always 1); `−` and `×` still work.
- [ ] `Clear queue` button below the queue. Disabled when empty; clicking calls `replaceCommands` with the appropriate `clear_production_queue` command via `buildPlanetScopeCommands`.
- [ ] All mutations go through `replaceCommands({ kind: "planet", id }, buildPlanetScopeCommands(...))` exactly as the existing planet detail panel does.

Unit tests in this step:

- [ ] Queue rows render in order with labels matching ship-design names and `PRODUCTION_ITEM_LABELS`.
- [ ] `+` and `−` adjust quantity and dispatch the expected `add_production_item` / `remove_production_item` commands.
- [ ] `×` removes the row entirely.
- [ ] `↑` / `↓` reorder rows and dispatch `move_production_item` commands referencing the correct `insertAfterItemId`.
- [ ] Drag-to-reorder dispatches the same commands as the arrow buttons (use dnd-kit's test helpers; if too heavy, assert via direct `onDragEnd` invocation against the component's exposed handler).
- [ ] `planetary_scanner` rows render with `+` disabled.
- [ ] `Clear queue` dispatches `clear_production_queue` and is disabled on an empty queue.

---

## Step 8 — Right pane: build palette

Inside `ProductionWorkspace`. New child component: `frontend/src/components/panels/BuildPalette.tsx`.

- [ ] Categories (in render order): `Infrastructure`, `Ships`, `Starbases`.
- [ ] `Infrastructure` rows:
  - `Mine` — cost `5r`.
  - `Factory` — cost `10r 4g`.
  - `Planetary Scanner` — cost `100r 10i 10b 70g`. Unavailable when `planet.hasScanner === true` or a `planetary_scanner` is already queued (mute + `Already installed` / `Already queued` note).
- [ ] `Ships` rows — one per owned design from `shipDesigns`. Cost shows resources + per-mineral totals from the design summary. Unavailable when `planet.starbase?.canBuildShips !== true` (mute + `Needs starbase`).
- [ ] `Starbases` rows — pull available upgrades for the planet from the existing starbase reference data path (see [PRD 17](docs/prd/17-starbases.md)). If no upgrades are available, the category renders with a single muted entry `Nothing buildable here`.
- [ ] Click handler appends to the queue:
  - `quantity = 1` on plain click, `quantity = 5` on Shift+click.
  - Compute the desired queue locally (existing rows + new row at the end), then call `replaceCommands` with `buildPlanetScopeCommands(...)`. The diff helper resolves to one `add_production_item` command with the correct `insertAfterItemId`.
- [ ] Unavailable rows are muted, non-clickable, and announce their reason via the small inline note.
- [ ] Reuse the Designer's palette row hover treatment (`hover:bg-white/8`) and label spacing for visual consistency.

Unit tests in this step (`frontend/src/components/panels/BuildPalette.test.tsx`):

- [ ] All three categories render with the expected entries for a fixture planet that satisfies every precondition.
- [ ] Click on `Mine` dispatches an `add_production_item` command with `itemType: "mine"` and `quantity: 1`.
- [ ] Shift+click on `Factory` dispatches a command with `quantity: 5`.
- [ ] `Planetary Scanner` is muted with `Already installed` when `planet.hasScanner === true`.
- [ ] `Planetary Scanner` is muted with `Already queued` when the queue already contains one.
- [ ] Ship rows are muted with `Needs starbase` when the planet's starbase can't build ships.
- [ ] No design entries renders an empty `Ships` category (collapsed or rendered with a muted "No designs" note — pick one and assert it).

---

## Step 9 — Planet detail: replace queue editor with summary + link

Edit [frontend/src/components/panels/PlanetDetail.tsx](frontend/src/components/panels/PlanetDetail.tsx).

- [ ] Remove the in-panel queue editor (the picker dropdown, queue rows, +/-, clear queue). The state hooks for the picker (`productionPickerOpen`, `productionPickerRef`, the outside-click handler) go away with it.
- [ ] Replace it with a `Production` section per [PRD 62 § "Production Summary"](docs/prd/62-ui-planet-detail.md):
  - Header: section label `Production` + a `Manage →` button on the right.
  - Body: one-line summary using the same `PRODUCTION_ITEM_LABELS` and ship-design names as the workspace. Empty queue → `Queue: empty`. One entry → `Queue: <qty>× <label>`. Two → `Queue: <qty>× <label>, <qty>× <label>`. Three or more → `Queue: <qty>× <label>, <qty>× <label>, +<N> more`.
- [ ] `Manage →` calls a new `onOpenProduction(planetId: string)` prop. The wiring at the `App.tsx` call site lands in Step 12.
- [ ] Visibility: gate on ownership only. The practical check is `planet.productionQueue != null` (the field is owner-only per PRD 13 visibility; an own planet is always `scanLevel: "detailed"` with `scanAge: 0` by PRD 11, so no separate scan / staleness gate is needed).
- [ ] Update / remove tests in [PlanetDetail.test.tsx](frontend/src/components/panels/PlanetDetail.test.tsx) that asserted on the queue editor's controls.

Unit tests in this step:

- [ ] Production section renders on own planets with the expected summary copy for each of the four queue-length buckets (0, 1, 2, ≥3).
- [ ] Production section is absent on enemy planets (no `productionQueue` field).
- [ ] Production section is absent on a carried-forward record of a previously-owned planet (`productionQueue == null` because ownership has been lost).
- [ ] Clicking `Manage →` calls `onOpenProduction(planet.id)`.
- [ ] Pre-existing assertions about the in-panel queue editor are removed (replaced or deleted to match the new shape).

---

## Step 10 — Production-summary helper

New module: `frontend/src/lib/productionSummary.ts`.

Both the planet detail summary line and the `queueHeadColumn` need the same friendly labels. Extract once.

- [ ] `export function describeQueueItem(item: PlayerProductionQueueItem, shipDesigns: ShipDesign[]): string` — returns the friendly label (`"Factory"`, design name for ship, etc.).
- [ ] `export function summariseQueue(queue: PlayerProductionQueueItem[], shipDesigns: ShipDesign[]): string` — returns the one-line summary copy described in Step 9 and PRD 62.
- [ ] Move `PRODUCTION_ITEM_LABELS` here if it currently lives inside `PlanetDetail.tsx`.

Unit tests in this step (`frontend/src/lib/productionSummary.test.ts`):

- [ ] `describeQueueItem` returns the design name for a `ship` item and the friendly label otherwise.
- [ ] `summariseQueue([])` returns `"Queue: empty"`.
- [ ] `summariseQueue` with one, two, and three+ items returns the four expected copy variants.
- [ ] Unknown design id falls back to a stable label (e.g. `"Ship"`).

---

## Step 11 — Keyboard shortcuts

Extend the global keyboard handler in [frontend/src/App.tsx](frontend/src/App.tsx) (currently handles `R` for research and `w`/`Escape` for waypoint editing).

- [ ] `P` switches to Production mode from Command view. Pressing `P` while already in Production returns to Command view. Same suppression rules: skip when a text input or textarea is focused; skip when the key was pressed with `Ctrl`, `Meta`, or `Alt`.
- [ ] `Esc` returns to Command from Production (and only from Production — leave the existing waypoint-mode `Esc` handler in place).
- [ ] Inside the planet list (focus within `PlanetList`), `Up` / `Down` move between rows and `Enter` / `Space` select. This is handled inside the `PlanetList` component itself (Step 1), not in the App-level handler.

Unit tests in this step (extend `frontend/src/App.test.tsx`):

- [ ] Pressing `P` with no input focused toggles between Command and Production mode.
- [ ] Pressing `P` while an input is focused does not toggle.
- [ ] Pressing `Esc` from Production returns to Command. Pressing `Esc` from Command does nothing (apart from any existing handlers).
- [ ] `P` does not fire when modifier keys are held.

---

## Step 12 — Wire Production at the App level

Edit [frontend/src/App.tsx](frontend/src/App.tsx):

- [ ] Widen `AppMode` to `"command" | "production" | "designer" | "research"`.
- [ ] Compute `ownedPlanets` (already done) and pass `productionEnabled={ownedPlanets.length > 0}` to `TopBar`.
- [ ] When `effectiveMode === "production"`, mount `<ProductionWorkspace ... />` with:
  - `ownedPlanets`
  - `currentPlayer={player}`
  - `shipDesigns={gameState.shipDesigns}`
  - `commands={gameState.commands.commands}`
  - `replaceCommands={gameState.replaceCommands}`
  - `basePlayerState={gameState.playerState}`
  - `initialPlanetId={selection?.kind === "planet" ? selection.id : null}` — when the player jumped in via `Manage →`, the selection is already on that planet.
  - `onShowOnMap={(planetId) => { setSelection({ kind: "planet", id: planetId }); setMode("command"); mapPanToRef.current?.(...); }}` — wires the centre-pane "Show on map" link.
- [ ] Wire the `onOpenProduction` prop on `<PlanetDetail>` (from Step 9): set `selection = { kind: "planet", id: planetId }` and `setMode("production")`. Pre-existing selection state already drives `initialPlanetId`, so no extra plumbing is needed beyond setting both.
- [ ] Effective-mode safety: if `mode === "production"` but `ownedPlanets.length === 0`, fall back to `"command"` (parallels the existing `research && !activeResearch` guard).

Unit tests in this step (`frontend/src/App.test.tsx`):

- [ ] Clicking the top-bar Production tab mounts the workspace.
- [ ] Production tab is disabled when there are no owned planets.
- [ ] Clicking `Manage production →` on a planet detail switches to Production with that planet selected.
- [ ] Mode auto-falls-back to `command` when a player loses all owned planets while in Production.
- [ ] Production-workspace edits populate the dirty buffer with the expected `planet`-scoped commands.

---

## Step 13 — Lint, typecheck, test

- [ ] `cd frontend && npm run lint` clean.
- [ ] `cd frontend && npm run typecheck` clean.
- [ ] `cd frontend && npm test` passes end-to-end.

---

## Deferred follow-ups

- **Turns-to-complete estimate** in palette rows and queue rows — backlog'd in [tasks/backlog.md](tasks/backlog.md) under Production.
- **Blocked status** on planets and queue items — needs a client-visible event hookup that doesn't yet exist; render `Building` until it lands.
- **Multi-planet selection / bulk operations** — PRD 67 leaves `selectedIds: string[]` as a clean extension point; not in this task.
- **Drag from palette into a specific queue index** — first cut only supports drag *within* the queue.
- **Cost preview for the whole queue** in the centre pane footer.
- **Keyboard type-ahead** in the planet list.
- **Per-user column preferences / column reordering** on the reusable list.

---

## Explicitly out of scope

- Any backend changes — production commands, costs, validation, and resolution all stay as defined in [PRD 13](docs/prd/13-production.md).
- New event codes or projection fields — the workspace reads only existing `PlayerState.planets`, `PlayerState.designs`, and `PlayerState.research` (for the leftover-only annotation).
- Browser / manual smoke tests — per [AGENTS.md](AGENTS.md) Cursor Cloud testing preference, automated checks (`npm test`, `typecheck`, `lint`) are the gate.
- Production templates and auto-build — separately listed in [tasks/backlog.md](tasks/backlog.md).
