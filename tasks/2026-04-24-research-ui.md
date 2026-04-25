# Research UI — frontend implementation

**Date:** 2026-04-24
**Goal:** Implement the research UI described in PRD 66 and the planet-detail research contribution section added to PRD 62. Players get a top-bar indicator that opens a Research dialog where they edit `current_field`, `next_field`, and `allocation_percent`. Each own planet exposes a `contribute_only_leftover_to_research` toggle in its detail panel. All edits queue existing backend commands (`set_research`, `set_planet_production_mode`) through the shared command infrastructure — no new API shape.
**Relevant PRDs:** [66 — Research UI](docs/prd/66-ui-research.md), [62 — Planet Detail Panel](docs/prd/62-ui-planet-detail.md), [21 — Research & Technology](docs/prd/21-research-and-technology.md), [51 — Event Codes](docs/prd/51-event-codes.md), [60 — UI Overview](docs/prd/60-ui-overview.md)

Depends on the backend work in [2026-04-24-research-and-technology.md](tasks/2026-04-24-research-and-technology.md). This task can be developed against the backend's player-state shape once the projection in Step 11 of that task lands, but stubbed `PlayerState.research` fixtures are fine for UI-only iteration.

---

## Preamble — field constants and colours

The six canonical field ids (from PRD 21) and their UI accent colours (from PRD 66) are shared across the top-bar indicator, the dialog's per-field rows, and any future technology-browser follow-up. Colocate them in one module so future work doesn't duplicate the list.

New module: `frontend/src/lib/research.ts`.

- [ ] `export const RESEARCH_FIELDS` — tuple of the six canonical ids in PRD 21 order: `["energy", "weapons", "propulsion", "construction", "electronics", "biotechnology"]`.
- [ ] `export type ResearchField = (typeof RESEARCH_FIELDS)[number]`.
- [ ] `export const RESEARCH_MAX_LEVEL = 26`.
- [ ] `export const RESEARCH_FIELD_LABELS: Record<ResearchField, string>` — display names (`"Energy"`, `"Biotechnology"`, etc.).
- [ ] `export const RESEARCH_FIELD_COLOURS: Record<ResearchField, string>` — Tailwind-compatible colour strings matching the PRD 66 palette (`#fbbf24`, `#ef4444`, `#3b82f6`, `#a3a3a3`, `#22d3ee`, `#22c55e`). Add matching CSS custom properties in [frontend/src/index.css](frontend/src/index.css) (`--color-research-energy`, etc.) so downstream canvas rendering can reuse them per [frontend/AGENTS.md](frontend/AGENTS.md) styling guidance.

Unit tests in this step (`frontend/src/lib/research.test.ts`):
- [ ] `RESEARCH_FIELDS` contains the six PRD ids in canonical order.
- [ ] `RESEARCH_FIELD_LABELS` has an entry for every `ResearchField` value.
- [ ] `RESEARCH_FIELD_COLOURS` has an entry for every `ResearchField` value.

---

## Step 1 — Client-side cost formula

The dialog needs cost lookups for *any* field, not just `current_field`, to power the click-to-switch per-field numerics. Reproduce the Fibonacci table + total-levels penalty on the client rather than round-tripping to the server.

Add to `frontend/src/lib/research.ts`:

- [ ] `BASE_COST: readonly number[]` — 26 entries, built from a Fibonacci recurrence seeded at `50, 80` (mirrors `backend/openstars/engine/research/costs.py` on the backend side). Build via a short loop at module load — do not hand-type the table.
- [ ] `baseCost(level: number): number` — returns `BASE_COST[level]`; throws for `level < 0` or `level >= RESEARCH_MAX_LEVEL`.
- [ ] `levelUpCost(currentLevel: number, totalLevels: number): number` — returns `baseCost(currentLevel) + 10 * totalLevels`; throws when `currentLevel === RESEARCH_MAX_LEVEL`.
- [ ] `totalLevels(levels: Record<ResearchField, number>): number` — sum across `RESEARCH_FIELDS`.

Unit tests in this step:
- [ ] `BASE_COST[0] === 50`, `BASE_COST[1] === 80`, `BASE_COST[25] === 8_320_400`, length 26.
- [ ] `BASE_COST[L] === BASE_COST[L-1] + BASE_COST[L-2]` for `L` in `2..25`.
- [ ] `levelUpCost(0, 0) === 50`; `levelUpCost(0, 12) === 170`.
- [ ] `levelUpCost(26, 0)` throws.
- [ ] `totalLevels({...all 6 at 3})` returns `18`.

---

## Step 2 — TypeScript types for player state

Extend [frontend/src/types/game.ts](frontend/src/types/game.ts) so the API client's camelCase projection carries the new research fields.

- [ ] Add `export interface PlayerStateResearch` with:
  - `levels: Record<ResearchField, number>`
  - `progress: Record<ResearchField, number>`
  - `currentField: ResearchField`
  - `nextField: ResearchField | null`
  - `allocationPercent: number`
  - `currentFieldRemainingCost: number`
  - `estimatedResourcesThisTurn: number`
- [ ] Add `research: PlayerStateResearch | null` to the `PlayerState` interface (nullable so fixtures that predate this work don't need updating all at once — treat `null` as "research UI hidden").
- [ ] Add `contributeOnlyLeftoverToResearch: boolean | null` to `PlayerPlanet` (nullable — populated only for own planets per PRD 21).
- [ ] If `PlayerCommand` is a discriminated union in the frontend, extend it with:
  - `{ type: "set_research"; currentField?: ResearchField; nextField?: ResearchField | null; allocationPercent?: number }`
  - `{ type: "set_planet_production_mode"; planetId: string; contributeOnlyLeftoverToResearch: boolean }`
- [ ] Update any test fixtures under `frontend/src/**/*.test.tsx` that construct `PlayerState` or `PlayerPlanet` literals only if the new nullable fields actually break the test (they shouldn't — they default to `null` when absent).

Unit tests in this step: none — type-level only; typecheck is the gate.

---

## Step 3 — Dirty/edit state plumbing for research

Research edits flow through the existing `useGameCommands` / dirty-commands buffer (see [frontend/AGENTS.md](frontend/AGENTS.md) "Command Flow"). The dialog needs a single source of truth for "pending `set_research` command for this turn" that persists across dialog opens.

- [ ] Inspect [frontend/src/hooks/useGameCommands.ts](frontend/src/hooks/useGameCommands.ts) to understand the current scope/replace pattern — it already supports fleet and planet scoping.
- [ ] Add a `research` scope so a pending `set_research` command can be replaced atomically via `replaceCommands("research", [...])`. If introducing a new scope string is heavier than warranted, accept the simpler `addCommand` + manual-dedup pattern and make the dialog enforce single-pending locally.
- [ ] Planet-scoped `set_planet_production_mode` commands reuse the existing `planet` scope — no new scope needed.

Unit tests in this step:
- [ ] `replaceCommands("research", [cmd])` followed by a second `replaceCommands("research", [cmd2])` leaves exactly one research command in the dirty buffer. (Mirror the existing fleet-scope test pattern in `useGameCommands`'s neighbouring tests.)
- [ ] `replaceCommands("research", [])` removes the pending research command entirely.

---

## Step 4 — Top-bar research indicator

Render the compact research readout in [frontend/src/components/TopBar.tsx](frontend/src/components/TopBar.tsx) between the turn indicator and the submission status.

- [ ] Add a `research: PlayerStateResearch | null` prop to `TopBar`.
- [ ] When `research === null`, render nothing (graceful for pre-research fixtures).
- [ ] When present:
  - Compose the label from `RESEARCH_FIELD_LABELS[research.currentField]`, `"lvl " + levels[currentField]`, and the progress percent `floor(100 * progress[currentField] / (progress[currentField] + research.currentFieldRemainingCost))`. Note: `currentFieldRemainingCost` is the *remaining* cost (`max(0, total - progress)`), not the absolute level cost — adding `progress` back recovers the denominator. Guard against the maxed case (next bullet) before doing this division.
  - If `levels[currentField] === RESEARCH_MAX_LEVEL`: render `<field> · lvl 26 · MAX`, no percent, no arrow.
  - If `allocationPercent === 0`: render the label dimmed with a trailing `· paused` pill.
  - Otherwise render the percent and a `→ lvl <L+1>` target indicator.
- [ ] Make the indicator a button (use the shared `Button` with a ghost variant). Click invokes a new `onOpenResearch` callback prop.
- [ ] Add keyboard-friendly hover/focus ring styling via the existing shared button styles.
- [ ] Wire `onOpenResearch` through `App.tsx` — open state lives in `App.tsx` (cross-cutting UI per the frontend AGENTS guidance), indicator dispatches, dialog mounts at the App level.

Unit tests in this step (`frontend/src/components/TopBar.test.tsx`):
- [ ] Indicator renders with field label, level, and percent when `research` is present and the current field is below cap.
- [ ] Indicator renders `MAX` (no percent) when `levels[currentField] === 26`.
- [ ] Indicator is dimmed / shows `paused` when `allocationPercent === 0`.
- [ ] Indicator is absent when `research === null`.
- [ ] Clicking the indicator calls `onOpenResearch`.

---

## Step 5 — Research dialog shell

New component: `frontend/src/components/ResearchDialog.tsx`. Modal dialog, mounted at `App.tsx` level, opened/closed via boolean state.

- [ ] Dialog skeleton:
  - Backdrop overlay with click-to-close.
  - Centred modal panel styled using the existing `panel-surface` + border tokens.
  - Close button (`✕`) in the header.
- [ ] Props:
  - `open: boolean`
  - `onClose: () => void`
  - `research: PlayerStateResearch`
  - `ownedPlanetsLeftoverOnlyCount: number` — derived by the caller from `playerState.planets`.
  - `ownedPlanetsCount: number` — ditto.
  - `pendingCommand: SetResearchCommand | null` — current pending `set_research` from the dirty buffer; seeds the local edit state so re-opening the dialog shows the in-flight edit.
  - `onApply: (cmd: SetResearchCommand | null) => void` — the caller translates this into `replaceCommands("research", cmd ? [cmd] : [])`. Passing `null` clears the pending command (used when the player resets all edits back to the server state).
- [ ] Local state held in the component:
  - `currentField`, `nextField`, `allocationPercent` initialised from `pendingCommand ?? research`.
  - `isDirty = serialised(local) !== serialised(committed)`.
- [ ] **Apply** button disabled when `!isDirty`; enabled otherwise.
- [ ] **Cancel** button discards local state and closes.
- [ ] `Escape` closes (cancel semantics).
- [ ] `R` keyboard shortcut toggles the dialog — bind at `App.tsx` level so it works from Command View. Suppress when a text input or textarea has focus (same pattern used for other app-wide shortcuts — grep for `addEventListener("keydown"` in `App.tsx` or neighbouring code).

Unit tests in this step (`frontend/src/components/ResearchDialog.test.tsx`):
- [ ] Dialog renders with header, close button, current state reflected in controls.
- [ ] Clicking the backdrop or close button calls `onClose`.
- [ ] Pressing `Escape` while open calls `onClose`.
- [ ] Apply is disabled when nothing has changed.
- [ ] Apply is enabled after any edit and calls `onApply` with only the changed fields.

---

## Step 6 — Allocation slider

Inside `ResearchDialog`:

- [ ] Render a range `<input type="range">` bound to `allocationPercent`, min `0`, max `100`, step `1`.
- [ ] Show the current percent beside the slider.
- [ ] Show `"≈ N resources this turn"` to the right of the percent, where `N = floor(research.estimatedResourcesThisTurn * allocationPercent / (research.allocationPercent || 1))` — a live approximation that scales the server-provided figure by the ratio of the new slider value to the committed one. If `research.allocationPercent === 0` (no server baseline), render `"— (no baseline)"`.
- [ ] Add a paired number `<input type="number">` so keyboard entry works (mirrors the original Stars! slider-plus-number UX). Clamp to `0..100` on blur.

Unit tests in this step:
- [ ] Dragging the slider updates the live percent display.
- [ ] Typing `60` into the number input and blurring updates the slider.
- [ ] Typing `150` clamps to `100` on blur; `-10` clamps to `0`.
- [ ] `estimatedResourcesThisTurn` scales linearly with the slider relative to the committed allocation.

---

## Step 7 — Current / Next field selectors

- [ ] Two `<select>` dropdowns labelled `Current field` and `Next field`.
- [ ] Both dropdowns list all six fields via `RESEARCH_FIELDS` + `RESEARCH_FIELD_LABELS`.
- [ ] `Next field` has an additional `(none)` option at the top representing `null`.
- [ ] In the `Current field` dropdown, options whose `levels[f] === RESEARCH_MAX_LEVEL` are rendered `disabled`.
- [ ] If `currentField === nextField` in local state, show an inline note: *"Same as current — next field will reset to none on apply."* Don't auto-correct — leave the reset behaviour to the engine, consistent with PRD 21 semantics.
- [ ] Selecting a new `currentField` does **not** alter the per-field progress display (progress is per-field, preserved on switch).

Unit tests in this step:
- [ ] Changing `Current field` updates local state and the progress-row `● current` marker moves to the new row (visual assertion via test ids).
- [ ] A field at level 26 is disabled in the `Current field` dropdown but selectable in `Next field`.
- [ ] Setting `Next field` to `(none)` sets local state to `null`.
- [ ] Setting `Current field === Next field` renders the inline warning.

---

## Step 8 — Per-field rows

- [ ] Render one row per field in `RESEARCH_FIELDS` order.
- [ ] Each row contains:
  - Field label, coloured via `RESEARCH_FIELD_COLOURS`.
  - A progress bar (simple div with a percent-width child) filled to `progress[f] / fieldCost(f)`.
  - `"lvl N"` label.
  - `"progress / cost"` numeric pair.
  - Status marker: `● current`, `○ queued next`, or a click-to-switch `▷` affordance.
- [ ] `fieldCost(f)` uses `levelUpCost(levels[f], totalLevels(levels))` from Step 1. For fields at the cap, show `MAX` and suppress the bar.
- [ ] Clicking a row (or the `▷` affordance) when the field is below cap sets local state `currentField = f` (same effect as changing the dropdown).
- [ ] The `● current` marker tracks *local* state, not the server's `research.currentField`, so the marker moves the moment the player edits.

Unit tests in this step:
- [ ] Six rows render, one per canonical field, in canonical order.
- [ ] The row matching the committed `currentField` shows `● current` on mount.
- [ ] Clicking a different field's row moves the `● current` marker and updates local state.
- [ ] A capped field renders `MAX` instead of the bar and numeric pair, and its row is disabled to click-to-switch.
- [ ] The queued-next marker (`○ queued next`) appears on the row matching `nextField`.

---

## Step 9 — Cost / ETA summary

Below the per-field rows:

- [ ] Line 1: `"Cost to next level (<CurrentFieldLabel>): <cost> resources"`, where `<cost>` is recomputed client-side from `levelUpCost(levels[currentField], totalLevels(levels))`. This tracks the local `currentField` so the line updates immediately when the player switches.
- [ ] Line 2: `"Estimated completion: ≈ <N> turns"`, where `N = ceil((cost - progress[currentField]) / estimatedResourcesThisTurn_local)` and `estimatedResourcesThisTurn_local` is the scaled figure from Step 6.
- [ ] If `estimatedResourcesThisTurn_local === 0`, render `"— (no research income)"`.
- [ ] If the current field is capped, render `"Cost to next level: — (maxed)"` and omit the ETA line.
- [ ] Optional: below the ETA line, a tiny summary `"<K> of <M> planets set to leftover-only"` when `ownedPlanetsLeftoverOnlyCount > 0`. Omit when the count is 0.

Unit tests in this step:
- [ ] Cost line shows `levelUpCost(levels[currentField], totalLevels(levels))` for the committed state.
- [ ] Switching to a different field updates the cost line in-place.
- [ ] ETA line shows `"no research income"` when the scaled estimate is zero.
- [ ] Capped current field renders `"— (maxed)"` and no ETA.
- [ ] Leftover-only planet count line appears when the count is non-zero and is absent otherwise.

---

## Step 10 — Apply: command diffing and wiring

- [ ] On Apply, build a `SetResearchCommand` with only the fields whose local value differs from `research` (the committed state), not from `pendingCommand`. This ensures the command carries the *full* set of edits-relative-to-server, which is what the backend expects.
- [ ] `nextField` needs explicit `null` vs. `undefined` handling:
  - Omitted from the command if unchanged relative to the server.
  - Included as `null` when the player cleared it.
  - Included as a string when the player set it.
- [ ] If every local field equals the committed state (i.e. the player reverted all edits manually), call `onApply(null)` so the caller can remove the pending research command entirely.
- [ ] Otherwise call `onApply(cmd)` and close the dialog.
- [ ] At the `App.tsx` call site, translate `onApply(cmd | null)` into `replaceCommands("research", cmd ? [cmd] : [])`.

Unit tests in this step:
- [ ] Apply produces a command with only changed fields (assert via mock `onApply` receiving the expected partial).
- [ ] Clearing `nextField` produces `{ nextField: null }` in the command.
- [ ] Reverting every edit manually then pressing Apply calls `onApply(null)`.
- [ ] Apply closes the dialog.

---

## Step 11 — Planet detail: Research Contribution section

Extend [frontend/src/components/PlanetDetail.tsx](frontend/src/components/PlanetDetail.tsx) with the section specified in the PRD 62 addition.

- [ ] Gate the section on `planet.contributeOnlyLeftoverToResearch !== null` — this is the definitive owner-only signal (see PRD 62 gating note).
- [ ] Also require `playerState.research != null` (otherwise the "Reserved this turn" figure has no source).
- [ ] Also require `planet.scanLevel === "detailed"` *and* `planet.scanAge === 0` to avoid rendering on stale-own-planet views.
- [ ] Layout:
  - Section header: `Research`.
  - Checkbox labelled `Contribute only leftover resources to research`, bound to the toggle.
  - Line: `Reserved this turn: ≈ <N> resources (<P>% of <total>)` when the toggle is off, using `research.allocationPercent`, the planet's current resource total, and `floor(total * pct / 100)`. Use `planet.totalResources` if that field exists in the current API shape — otherwise compute from `population`, `factories`, `mines` and habitability using the same helper the mineral/resource bars already call. Grep for existing `total_resources` usage in the frontend; reuse a helper if one exists.
  - When the toggle is on, show `Reserved this turn: — (leftover only)`.
  - Projected leftover: a best-effort estimate. If the data is not readily available in the first pass (requires walking the production queue), omit this line and note it in the follow-up list below.
- [ ] Clicking the checkbox:
  - Flips local state immediately (optimistic render).
  - If the new value differs from the server-side value, `addCommand({ type: "set_planet_production_mode", planetId: planet.id, contributeOnlyLeftoverToResearch: newValue })` scoped by the existing `planet` scope — with per-planet dedup: a second flip for the same planet replaces the first, and a flip back to the server value removes the pending command entirely.
- [ ] Wire through the existing `PlanetDetail` dirty-edit pattern (it already handles planet-scoped commands — mirror that shape).

Unit tests in this step (`frontend/src/components/PlanetDetail.test.tsx`):
- [ ] Research Contribution section renders on an own detailed planet with research state present.
- [ ] Section is absent when `contributeOnlyLeftoverToResearch === null` (enemy planet under penetrating scan).
- [ ] Section is absent on a stale own planet (`scanAge > 0`).
- [ ] Section is absent when `playerState.research === null`.
- [ ] Toggling the checkbox queues a `set_planet_production_mode` command via `addCommand`.
- [ ] Flipping back to the server value removes the pending command from the dirty buffer.
- [ ] Reserved-this-turn line shows `≈ <N> resources` when toggle is off, and `— (leftover only)` when on.

---

## Step 12 — Event log messages for `research.level_up`

- [ ] Extend [frontend/src/components/eventMessages.ts](frontend/src/components/eventMessages.ts) with a `research.level_up` case.
- [ ] Message shape: `"{FieldLabel} advanced to level {N}"` using `values[0]` as field id (translated via `RESEARCH_FIELD_LABELS`) and `values[1]` as the new level integer.
- [ ] No toast, no pulse — the event log is the only channel per PRD 66.

Unit tests in this step (`frontend/src/components/eventMessages.test.ts`):
- [ ] `research.level_up` with `values: ["propulsion", 4]` renders `"Propulsion advanced to level 4"`.
- [ ] An unknown field id falls through to a safe fallback (e.g. the existing unknown-code behaviour) rather than throwing.

---

## Step 13 — Wire research dialog at App level

- [ ] In `App.tsx`, add `const [researchOpen, setResearchOpen] = useState(false)`.
- [ ] Pass `research={playerState.research}` and `onOpenResearch={() => setResearchOpen(true)}` to `TopBar`.
- [ ] Mount `<ResearchDialog open={researchOpen} ... />` alongside the other top-level modals.
- [ ] Add the `R` global keyboard handler (suppressed when a text input is focused) that toggles `researchOpen`. Reuse any existing `useGlobalShortcut`-style helper if one is present; otherwise inline the handler following the pattern already used for other top-level shortcuts.
- [ ] Derive `ownedPlanetsLeftoverOnlyCount` and `ownedPlanetsCount` from `playerState.planets` at the call site.
- [ ] Pass `pendingCommand` by reading the current dirty buffer's `research` scope and picking the single command (if any).
- [ ] Wire `onApply` to `replaceCommands("research", cmd ? [cmd] : [])`.

Unit tests in this step (App-level integration, `frontend/src/App.test.tsx`):
- [ ] Clicking the top-bar indicator opens the dialog.
- [ ] Pressing `R` with no input focused toggles the dialog.
- [ ] Pressing `R` while an input is focused does not toggle.
- [ ] Applying a change in the dialog populates the dirty buffer with exactly one `set_research` command.
- [ ] Re-opening the dialog shows the pending edit (not the server state).

---

## Step 14 — Lint, typecheck, test

- [ ] `cd frontend && npm run lint` clean.
- [ ] `cd frontend && npm run typecheck` clean.
- [ ] `cd frontend && npm test` passes end-to-end.

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
