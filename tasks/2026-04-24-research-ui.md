# Research UI — frontend implementation

**Date:** 2026-04-24
**Goal:** Implement the research UI described in PRD 66 and the planet-detail research contribution section added to PRD 62. Players get a top-bar indicator that opens a Research dialog where they edit `current_field`, `next_field`, and `allocation_percent`. Each own planet exposes a `contribute_only_leftover_to_research` toggle in its detail panel. All edits queue existing backend commands (`set_research`, `set_planet_production_mode`) through the shared command infrastructure — no new API shape.
**Relevant PRDs:** [66 — Research UI](docs/prd/66-ui-research.md), [62 — Planet Detail Panel](docs/prd/62-ui-planet-detail.md), [21 — Research & Technology](docs/prd/21-research-and-technology.md), [51 — Event Codes](docs/prd/51-event-codes.md), [60 — UI Overview](docs/prd/60-ui-overview.md)

Depends on the backend work in [2026-04-24-research-and-technology.md](tasks/2026-04-24-research-and-technology.md). This task targets the projection shape produced by Step 15 of that task (per-field `remaining_cost`, `reservable_resources_this_turn`); stubbed `PlayerState.research` fixtures are fine for UI-only iteration.

---

## Preamble — field constants and colours

The six canonical field ids (from PRD 21) and their UI accent colours (from PRD 66) are shared across the top-bar indicator, the dialog's per-field rows, and any future technology-browser follow-up. Colocate them in one module so future work doesn't duplicate the list.

New module: `frontend/src/lib/research.ts`.

- [x] `export const RESEARCH_FIELDS` — tuple of the six canonical ids in PRD 21 order: `["energy", "weapons", "propulsion", "construction", "electronics", "biotechnology"]`.
- [x] `export type ResearchField = (typeof RESEARCH_FIELDS)[number]`.
- [x] `export const RESEARCH_MAX_LEVEL = 26`.
- [x] `export const RESEARCH_FIELD_LABELS: Record<ResearchField, string>` — display names (`"Energy"`, `"Biotechnology"`, etc.).
- [x] `export const RESEARCH_FIELD_COLOURS: Record<ResearchField, string>` — Tailwind-compatible colour strings matching the PRD 66 palette (`#fbbf24`, `#ef4444`, `#3b82f6`, `#a3a3a3`, `#22d3ee`, `#22c55e`). Add matching CSS custom properties in [frontend/src/index.css](frontend/src/index.css) (`--color-research-energy`, etc.) so downstream canvas rendering can reuse them per [frontend/AGENTS.md](frontend/AGENTS.md) styling guidance.

Unit tests in this step (`frontend/src/lib/research.test.ts`):
- [x] `RESEARCH_FIELDS` contains the six PRD ids in canonical order.
- [x] `RESEARCH_FIELD_LABELS` has an entry for every `ResearchField` value.
- [x] `RESEARCH_FIELD_COLOURS` has an entry for every `ResearchField` value.

---

## Step 1 — TypeScript types for player state

Extend [frontend/src/types/game.ts](frontend/src/types/game.ts) so the API client's camelCase projection carries the new research fields.

- [x] Add `export interface PlayerStateResearch` with:
  - `levels: Record<ResearchField, number>`
  - `progress: Record<ResearchField, number>`
  - `currentField: ResearchField`
  - `nextField: ResearchField | null`
  - `allocationPercent: number`
  - `remainingCost: Record<ResearchField, number>`
  - `reservableResourcesThisTurn: number`
- [x] Add `research: PlayerStateResearch | null` to the `PlayerState` interface (nullable so fixtures that predate this work don't need updating all at once — treat `null` as "research UI hidden").
- [x] Add `contributeOnlyLeftoverToResearch: boolean | null` to `PlayerPlanet` (nullable — populated only for own planets per PRD 21).
- [x] If `PlayerCommand` is a discriminated union in the frontend, extend it with:
  - `{ type: "set_research"; currentField?: ResearchField; nextField?: ResearchField | null; allocationPercent?: number }`
  - `{ type: "set_planet_production_mode"; planetId: string; contributeOnlyLeftoverToResearch: boolean }`
- [x] Update any test fixtures under `frontend/src/**/*.test.tsx` that construct `PlayerState` or `PlayerPlanet` literals only if the new nullable fields actually break the test (they shouldn't — they default to `null` when absent).

Unit tests in this step: none — type-level only; typecheck is the gate.

---

## Step 2 — Dirty/edit state plumbing for research

Research edits flow through the existing `useGameCommands` / dirty-commands buffer (see [frontend/AGENTS.md](frontend/AGENTS.md) "Command Flow"). The dialog needs a single source of truth for "pending `set_research` command for this turn" that persists across dialog opens.

- [x] Inspect [frontend/src/hooks/useGameCommands.ts](frontend/src/hooks/useGameCommands.ts) to understand the current scope/replace pattern — it already supports fleet and planet scoping.
- [x] Add a `research` scope so a pending `set_research` command can be replaced atomically via `replaceCommands("research", [...])`. If introducing a new scope string is heavier than warranted, accept the simpler `addCommand` + manual-dedup pattern and make the dialog enforce single-pending locally.
- [x] Planet-scoped `set_planet_production_mode` commands reuse the existing `planet` scope — no new scope needed.

Unit tests in this step:
- [x] `replaceCommands("research", [cmd])` followed by a second `replaceCommands("research", [cmd2])` leaves exactly one research command in the dirty buffer. (Mirror the existing fleet-scope test pattern in `useGameCommands`'s neighbouring tests.)
- [x] `replaceCommands("research", [])` removes the pending research command entirely.

---

## Step 3 — Top-bar research indicator

Render the compact research readout in [frontend/src/components/TopBar.tsx](frontend/src/components/TopBar.tsx) between the turn indicator and the submission status.

- [x] Add a `research: PlayerStateResearch | null` prop to `TopBar`.
- [x] When `research === null`, render nothing (graceful for pre-research fixtures).
- [x] When present:
  - Compose the label from `RESEARCH_FIELD_LABELS[research.currentField]`, `"lvl " + levels[currentField]`, and the progress percent `floor(100 * progress[currentField] / (progress[currentField] + research.remainingCost[currentField]))`. (Adding `progress` back to `remainingCost` recovers the absolute level cost; guard the maxed case in the next bullet before dividing.)
  - If `levels[currentField] === RESEARCH_MAX_LEVEL`: render `<field> · lvl 26 · MAX`, no percent, no arrow.
  - If `allocationPercent === 0`: render the label dimmed with a trailing `· paused` pill.
  - Otherwise render the percent and a `→ lvl <L+1>` target indicator.
- [x] Make the indicator a button (use the shared `Button` with a ghost variant). Click invokes a new `onOpenResearch` callback prop.
- [x] Add keyboard-friendly hover/focus ring styling via the existing shared button styles.
- [x] Wire `onOpenResearch` through `App.tsx` — open state lives in `App.tsx` (cross-cutting UI per the frontend AGENTS guidance), indicator dispatches, dialog mounts at the App level.

Unit tests in this step (`frontend/src/components/TopBar.test.tsx`):
- [x] Indicator renders with field label, level, and percent when `research` is present and the current field is below cap.
- [x] Indicator renders `MAX` (no percent) when `levels[currentField] === 26`.
- [x] Indicator is dimmed / shows `paused` when `allocationPercent === 0`.
- [x] Indicator is absent when `research === null`.
- [x] Clicking the indicator calls `onOpenResearch`.

---

## Step 4 — Research dialog shell

New component: `frontend/src/components/ResearchDialog.tsx`. Modal dialog, mounted at `App.tsx` level, opened/closed via boolean state.

- [x] Dialog skeleton:
  - Backdrop overlay with click-to-close.
  - Centred modal panel styled using the existing `panel-surface` + border tokens.
  - Close button (`✕`) in the header.
- [x] Props:
  - `open: boolean`
  - `onClose: () => void`
  - `research: PlayerStateResearch`
  - `ownedPlanetsLeftoverOnlyCount: number` — derived by the caller from `playerState.planets`.
  - `ownedPlanetsCount: number` — ditto.
  - `pendingCommand: SetResearchCommand | null` — current pending `set_research` from the dirty buffer; seeds the local edit state so re-opening the dialog shows the in-flight edit.
  - `onApply: (cmd: SetResearchCommand | null) => void` — the caller translates this into `replaceCommands("research", cmd ? [cmd] : [])`. Passing `null` clears the pending command (used when the player resets all edits back to the server state).
- [x] Local state held in the component:
  - `currentField`, `nextField`, `allocationPercent` initialised from `pendingCommand ?? research`.
  - `isDirty = serialised(local) !== serialised(committed)`.
- [x] **Apply** button disabled when `!isDirty`; enabled otherwise.
- [x] **Cancel** button discards local state and closes.
- [x] `Escape` closes (cancel semantics).
- [x] `R` keyboard shortcut toggles the dialog — bind at `App.tsx` level so it works from Command View. Suppress when a text input or textarea has focus (same pattern used for other app-wide shortcuts — grep for `addEventListener("keydown"` in `App.tsx` or neighbouring code).

Unit tests in this step (`frontend/src/components/ResearchDialog.test.tsx`):
- [x] Dialog renders with header, close button, current state reflected in controls.
- [x] Clicking the backdrop or close button calls `onClose`.
- [x] Pressing `Escape` while open calls `onClose`.
- [x] Apply is disabled when nothing has changed.
- [x] Apply is enabled after any edit and calls `onApply` with only the changed fields.

---

## Step 5 — Allocation slider

Inside `ResearchDialog`:

- [x] Render a range `<input type="range">` bound to `allocationPercent`, min `0`, max `100`, step `1`.
- [x] Show the current percent beside the slider.
- [x] Show `"≈ N resources this turn"` to the right of the percent, where `N = floor(research.reservableResourcesThisTurn * allocationPercent / 100)` — works at any slider value including `0`, no baseline branch needed. If `research.reservableResourcesThisTurn === 0` (player owns no non-leftover-only planets), render `"— (no reservable resources)"`.
- [x] Add a paired number `<input type="number">` so keyboard entry works (mirrors the original Stars! slider-plus-number UX). Clamp to `0..100` on blur.

Unit tests in this step:
- [x] Dragging the slider updates the live percent display.
- [x] Typing `60` into the number input and blurring updates the slider.
- [x] Typing `150` clamps to `100` on blur; `-10` clamps to `0`.
- [x] The `≈ N resources this turn` figure scales linearly with the slider, computed as `floor(reservableResourcesThisTurn * pct / 100)`.
- [x] When `reservableResourcesThisTurn === 0`, the "no reservable resources" placeholder renders.

---

## Step 6 — Current / Next field selectors

- [x] Two `<select>` dropdowns labelled `Current field` and `Next field`.
- [x] Both dropdowns list all six fields via `RESEARCH_FIELDS` + `RESEARCH_FIELD_LABELS`.
- [x] `Next field` has an additional `(none)` option at the top representing `null`.
- [x] In the `Current field` dropdown, options whose `levels[f] === RESEARCH_MAX_LEVEL` are rendered `disabled`.
- [x] If `currentField === nextField` in local state, show an inline note: *"Same as current — next field will reset to none on apply."* Don't auto-correct — leave the reset behaviour to the engine, consistent with PRD 21 semantics.
- [x] Selecting a new `currentField` does **not** alter the per-field progress display (progress is per-field, preserved on switch).

Unit tests in this step:
- [x] Changing `Current field` updates local state and the progress-row `● current` marker moves to the new row (visual assertion via test ids).
- [x] A field at level 26 is disabled in the `Current field` dropdown but selectable in `Next field`.
- [x] Setting `Next field` to `(none)` sets local state to `null`.
- [x] Setting `Current field === Next field` renders the inline warning.

---

## Step 7 — Per-field rows

- [x] Render one row per field in `RESEARCH_FIELDS` order.
- [x] Define `fieldCost(f) = progress[f] + research.remainingCost[f]` — recovers the absolute level cost from the projection without any client-side cost recomputation.
- [x] Each row contains:
  - Field label, coloured via `RESEARCH_FIELD_COLOURS`.
  - A progress bar (simple div with a percent-width child) filled to `progress[f] / fieldCost(f)`.
  - `"lvl N"` label.
  - `"progress / cost"` numeric pair.
  - Status marker: `● current`, `○ queued next`, or a click-to-switch `▷` affordance.
- [x] For fields at the cap (`levels[f] === RESEARCH_MAX_LEVEL`), show `MAX` and suppress the bar (the projection sets `remainingCost[f] === 0` for capped fields, so don't divide).
- [x] Clicking a row (or the `▷` affordance) when the field is below cap sets local state `currentField = f` (same effect as changing the dropdown).
- [x] The `● current` marker tracks *local* state, not the server's `research.currentField`, so the marker moves the moment the player edits.

Unit tests in this step:
- [x] Six rows render, one per canonical field, in canonical order.
- [x] The row matching the committed `currentField` shows `● current` on mount.
- [x] Clicking a different field's row moves the `● current` marker and updates local state.
- [x] A capped field renders `MAX` instead of the bar and numeric pair, and its row is disabled to click-to-switch.
- [x] The queued-next marker (`○ queued next`) appears on the row matching `nextField`.

---

## Step 8 — Cost / ETA summary

Below the per-field rows:

- [x] Line 1: `"Cost to next level (<CurrentFieldLabel>): <cost> resources"`, where `<cost> = progress[localCurrentField] + research.remainingCost[localCurrentField]`. Tracks the *local* `currentField` so the line updates immediately when the player switches rows.
- [x] Line 2: `"Estimated completion: ≈ <N> turns"`, where `N = ceil(research.remainingCost[localCurrentField] / scaledReservable)` and `scaledReservable = floor(research.reservableResourcesThisTurn * localAllocationPercent / 100)`.
- [x] If `scaledReservable === 0`, render `"— (no research income)"`.
- [x] If the local current field is capped (`levels[localCurrentField] === RESEARCH_MAX_LEVEL`), render `"Cost to next level: — (maxed)"` and omit the ETA line.
- [x] Optional: below the ETA line, a tiny summary `"<K> of <M> planets set to leftover-only"` when `ownedPlanetsLeftoverOnlyCount > 0`. Omit when the count is 0.

Unit tests in this step:
- [x] Cost line shows `progress[currentField] + remainingCost[currentField]` for the committed state.
- [x] Switching to a different field updates the cost line in-place using that field's `remainingCost`.
- [x] ETA line shows `"no research income"` when the scaled reservable resources is zero.
- [x] Capped current field renders `"— (maxed)"` and no ETA.
- [x] Leftover-only planet count line appears when the count is non-zero and is absent otherwise.

---

## Step 9 — Apply: command diffing and wiring

- [x] On Apply, build a `SetResearchCommand` with only the fields whose local value differs from `research` (the committed state), not from `pendingCommand`. This ensures the command carries the *full* set of edits-relative-to-server, which is what the backend expects.
- [x] `nextField` needs explicit `null` vs. `undefined` handling:
  - Omitted from the command if unchanged relative to the server.
  - Included as `null` when the player cleared it.
  - Included as a string when the player set it.
- [x] If every local field equals the committed state (i.e. the player reverted all edits manually), call `onApply(null)` so the caller can remove the pending research command entirely.
- [x] Otherwise call `onApply(cmd)` and close the dialog.
- [x] At the `App.tsx` call site, translate `onApply(cmd | null)` into `replaceCommands("research", cmd ? [cmd] : [])`.

Unit tests in this step:
- [x] Apply produces a command with only changed fields (assert via mock `onApply` receiving the expected partial).
- [x] Clearing `nextField` produces `{ nextField: null }` in the command.
- [x] Reverting every edit manually then pressing Apply calls `onApply(null)`.
- [x] Apply closes the dialog.

---

## Step 10 — Planet detail: Research Contribution section

Extend [frontend/src/components/PlanetDetail.tsx](frontend/src/components/PlanetDetail.tsx) with the section specified in the PRD 62 addition.

- [x] Gate the section on `planet.contributeOnlyLeftoverToResearch !== null` — this is the definitive owner-only signal (see PRD 62 gating note).
- [x] Also require `playerState.research != null` (otherwise the "Reserved this turn" figure has no source).
- [x] Also require `planet.scanLevel === "detailed"` *and* `planet.scanAge === 0` to avoid rendering on stale-own-planet views.
- [x] Layout:
  - Section header: `Research`.
  - Checkbox labelled `Contribute only leftover resources to research`, bound to the toggle.
  - Line: `Reserved this turn: ≈ <N> resources (<P>% of <total>)` when the toggle is off, where `total = planet.resources` (already on `PlayerPlanet`), `pct = research.allocationPercent`, and `N = floor(total * pct / 100)`.
  - When the toggle is on, show `Reserved this turn: — (leftover only)`.
  - Projected leftover: a best-effort estimate. If the data is not readily available in the first pass (requires walking the production queue), omit this line and note it in the follow-up list below.
- [x] Clicking the checkbox:
  - Flips local state immediately (optimistic render).
  - If the new value differs from the server-side value, `addCommand({ type: "set_planet_production_mode", planetId: planet.id, contributeOnlyLeftoverToResearch: newValue })` scoped by the existing `planet` scope — with per-planet dedup: a second flip for the same planet replaces the first, and a flip back to the server value removes the pending command entirely.
- [x] Wire through the existing `PlanetDetail` dirty-edit pattern (it already handles planet-scoped commands — mirror that shape).

Unit tests in this step (`frontend/src/components/PlanetDetail.test.tsx`):
- [x] Research Contribution section renders on an own detailed planet with research state present.
- [x] Section is absent when `contributeOnlyLeftoverToResearch === null` (enemy planet under penetrating scan).
- [x] Section is absent on a stale own planet (`scanAge > 0`).
- [x] Section is absent when `playerState.research === null`.
- [x] Toggling the checkbox queues a `set_planet_production_mode` command via `addCommand`.
- [x] Flipping back to the server value removes the pending command from the dirty buffer.
- [x] Reserved-this-turn line shows `≈ <N> resources` when toggle is off, and `— (leftover only)` when on.

---

## Step 11 — Event log messages for `research.level_up`

- [x] Extend [frontend/src/components/eventMessages.ts](frontend/src/components/eventMessages.ts) with a `research.level_up` case.
- [x] Message shape: `"{FieldLabel} advanced to level {N}"` using `values[0]` as field id (translated via `RESEARCH_FIELD_LABELS`) and `values[1]` as the new level integer.
- [x] No toast, no pulse — the event log is the only channel per PRD 66.

Unit tests in this step (`frontend/src/components/eventMessages.test.ts`):
- [x] `research.level_up` with `values: ["propulsion", 4]` renders `"Propulsion advanced to level 4"`.
- [x] An unknown field id falls through to a safe fallback (e.g. the existing unknown-code behaviour) rather than throwing.

---

## Step 12 — Wire research dialog at App level

- [x] In `App.tsx`, add `const [researchOpen, setResearchOpen] = useState(false)`.
- [x] Pass `research={playerState.research}` and `onOpenResearch={() => setResearchOpen(true)}` to `TopBar`.
- [x] Mount `<ResearchDialog open={researchOpen} ... />` alongside the other top-level modals.
- [x] Add the `R` global keyboard handler (suppressed when a text input is focused) that toggles `researchOpen`. Reuse any existing `useGlobalShortcut`-style helper if one is present; otherwise inline the handler following the pattern already used for other top-level shortcuts.
- [x] Derive `ownedPlanetsLeftoverOnlyCount` and `ownedPlanetsCount` from `playerState.planets` at the call site.
- [x] Pass `pendingCommand` by reading the current dirty buffer's `research` scope and picking the single command (if any).
- [x] Wire `onApply` to `replaceCommands("research", cmd ? [cmd] : [])`.

Unit tests in this step (App-level integration, `frontend/src/App.test.tsx`):
- [x] Clicking the top-bar indicator opens the dialog.
- [x] Pressing `R` with no input focused toggles the dialog.
- [x] Pressing `R` while an input is focused does not toggle.
- [x] Applying a change in the dialog populates the dirty buffer with exactly one `set_research` command.
- [x] Re-opening the dialog shows the pending edit (not the server state).

---

## Step 13 — Lint, typecheck, test

- [x] `cd frontend && npm run lint` clean.
- [x] `cd frontend && npm run typecheck` clean.
- [x] `cd frontend && npm test` passes end-to-end.

---

## Deferred follow-ups

- **Projected leftover** line in the per-planet Research Contribution section — needs a queue-cost helper that doesn't yet exist client-side. Easy add once that helper lands.
- **Cross-planet allocation overview** inside the research dialog (beyond the simple `K of M` count).
- **Technology Browser** — a separate screen listing components/hulls by unlock; owned PRD-wise, not UI-wise, by this task. PRD 66's own deferred list calls this out.
- **Miniaturisation preview** surfaces for designer/production panes, dependent on the backend build-time-miniaturisation work in the neighbouring task file.
- **Multi-level-up bar animation** — cosmetic.
- **Per-field ETA column** for all six fields.
- **Allocation presets** (`0 / 15 / 50 / 100` buttons).
- **Multi-tab concurrent-edit warning** — deferred per PRD 66.

---

## Explicitly out of scope

- Backend changes of any kind — this task assumes the backend work in [2026-04-24-research-and-technology.md](tasks/2026-04-24-research-and-technology.md) is landed (or mocked via fixtures).
- Browser/manual smoke tests — per [AGENTS.md](AGENTS.md) Cursor Cloud testing preference, automated checks (`npm test`, `typecheck`, `lint`) are the gate.
- Any rework of the event log rendering surface — PRD 66 explicitly routes level-up feedback through the existing log.
