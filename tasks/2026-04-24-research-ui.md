# Research UI — frontend implementation

**Date:** 2026-04-24
**Goal:** Implement the research UI described in PRD 66 and the planet-detail research contribution section added to PRD 62. Players get a top-bar `Research` tab that switches the main area to a Research workspace where they edit `current_field`, `next_field`, and `allocation_percent`. Each own planet exposes a `contribute_only_leftover_to_research` toggle in its detail panel. All edits queue existing backend commands (`set_research`, `set_planet_production_mode`) through the shared command infrastructure — no new API shape.
**Relevant PRDs:** [66 — Research UI](docs/prd/66-ui-research.md), [62 — Planet Detail Panel](docs/prd/62-ui-planet-detail.md), [21 — Research & Technology](docs/prd/21-research-and-technology.md), [51 — Event Codes](docs/prd/51-event-codes.md), [60 — UI Overview](docs/prd/60-ui-overview.md)

Depends on the backend work in [2026-04-24-research-and-technology.md](tasks/2026-04-24-research-and-technology.md). This task targets the projection shape produced by Step 15 of that task (per-field `remaining_cost`, `reservable_resources_this_turn`); stubbed `PlayerState.research` fixtures are fine for UI-only iteration.

---

## Preamble — field constants and colours

The six canonical field ids (from PRD 21) and their UI accent colours (from PRD 66) are shared across the workspace's per-field rows and any future technology-browser follow-up. Colocate them in one module so future work doesn't duplicate the list.

New module: `frontend/src/lib/research.ts`.

- [x] `export const RESEARCH_FIELDS` — tuple of the six canonical ids in PRD 21 order: `["energy", "weapons", "propulsion", "construction", "electronics", "biotechnology"]`.
- [x] `export type ResearchField = (typeof RESEARCH_FIELDS)[number]`.
- [x] `export const RESEARCH_MAX_LEVEL = 26`.
- [x] `export const RESEARCH_FIELD_LABELS: Record<ResearchField, string>` — display names (`"Energy"`, `"Biotechnology"`, etc.).
- [x] `export const RESEARCH_FIELD_COLOURS: Record<ResearchField, string>` — CSS custom property references (`var(--color-research-energy)`, etc.). The actual palette values live only in [frontend/src/index.css](frontend/src/index.css) so downstream rendering can reuse one source of truth per [frontend/AGENTS.md](frontend/AGENTS.md) styling guidance.

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

Research edits flow through the existing `useGameCommands` / dirty-commands buffer (see [frontend/AGENTS.md](frontend/AGENTS.md) "Command Flow"). The workspace needs a single source of truth for "pending `set_research` command for this turn" that persists across tab switches.

- [x] Inspect [frontend/src/hooks/useGameCommands.ts](frontend/src/hooks/useGameCommands.ts) to understand the current scope/replace pattern — it already supports fleet and planet scoping.
- [x] Add a `research` scope so a pending `set_research` command can be replaced atomically via `replaceCommands("research", [...])`. If introducing a new scope string is heavier than warranted, accept the simpler `addCommand` + manual-dedup pattern and make the workspace enforce single-pending locally.
- [x] Planet-scoped `set_planet_production_mode` commands reuse the existing `planet` scope — no new scope needed.

Unit tests in this step:
- [x] `replaceCommands("research", [cmd])` followed by a second `replaceCommands("research", [cmd2])` leaves exactly one research command in the dirty buffer. (Mirror the existing fleet-scope test pattern in `useGameCommands`'s neighbouring tests.)
- [x] `replaceCommands("research", [])` removes the pending research command entirely.

---

## Step 3 — Top-bar Research tab

Render the Research entry in [frontend/src/components/TopBar.tsx](frontend/src/components/TopBar.tsx) as another tab in the left-side view selector alongside Command and Designer.

- [x] Add a `research: PlayerStateResearch | null` prop to `TopBar`.
- [x] When `research === null`, render nothing (graceful for pre-research fixtures).
- [x] When present, render a `Research` tab button. Do not duplicate current field, progress, paused state, or ETA in the top bar; those details live inside the workspace.
- [x] Make the tab a button (use the shared `Button`). Click switches `App` mode to `research`.
- [x] Add keyboard-friendly hover/focus ring styling via the existing shared button styles.
- [x] Wire research mode through `App.tsx` — mode state lives in `App.tsx` (cross-cutting UI per the frontend AGENTS guidance), tab dispatches, workspace mounts at the App level.

Unit tests in this step (`frontend/src/components/TopBar.test.tsx`):
- [x] Research tab renders when `research` is present.
- [x] The old top-right field/progress readout is absent.
- [x] The tab does not add paused copy when `allocationPercent === 0`.
- [x] Research tab is absent when `research === null`.
- [x] Clicking the tab switches to research mode.

---

## Step 4 — Research workspace shell

New component: `frontend/src/components/ResearchWorkspace.tsx`. In-flow workspace, mounted at `App.tsx` level when `mode === "research"`.

- [x] Workspace skeleton:
  - Full-height workspace area matching `DesignsWorkspace`.
  - Panel styled using the existing `panel-surface` + border tokens.
  - Header with `Research` title.
- [x] Props:
  - `research: PlayerStateResearch`
  - `ownedPlanetsLeftoverOnlyCount: number` — derived by the caller from `playerState.planets`.
  - `ownedPlanetsCount: number` — ditto.
  - `pendingCommand: SetResearchCommand | null` — current pending `set_research` from the dirty buffer; seeds the local edit state so returning to the workspace shows the in-flight edit.
  - `onChange: (cmd: SetResearchCommand | null) => void` — the caller translates this into `replaceCommands("research", cmd ? [cmd] : [])`. Passing `null` clears the pending command (used when the player resets all edits back to the server state).
- [x] Local state held in the component:
  - `currentField`, `nextField`, `allocationPercent` initialised from `pendingCommand ?? research`.
  - Command diffing compares local state to committed state whenever a control changes.
- [x] No manual Apply/Cancel controls; each committed control change auto-saves to the dirty command buffer.
- [x] `R` keyboard shortcut switches to Research from Command View and returns to Command View when already in Research. Suppress when a text input or textarea has focus (same pattern used for other app-wide shortcuts — grep for `addEventListener("keydown"` in `App.tsx` or neighbouring code).

Unit tests in this step (`frontend/src/components/ResearchWorkspace.test.tsx`):
- [x] Workspace renders with header and current state reflected in controls.
- [x] Workspace does not render as a modal dialog or include backdrop/close controls.
- [x] Manual Apply/Cancel controls are absent.
- [x] Editing any control calls `onChange` with only the changed fields.

---

## Step 5 — Allocation control

Inside `ResearchWorkspace`:

- [x] Render a numeric `<input type="number">` labelled `Resource Allocation`, bound to `allocationPercent`, min `0`, max `100`, step `1`, with a visible `%` suffix.
- [x] Show visible `-` and `+` buttons beside the number input for one-point adjustments.
- [x] Show `"Reserved this turn: ≈ N resources"` in the bottom summary, where `N = floor(research.reservableResourcesThisTurn * allocationPercent / 100)` — works at any value including `0`, no baseline branch needed. If `research.reservableResourcesThisTurn === 0` (player owns no non-leftover-only planets), render `"— (no reservable resources)"`.
- [x] Clamp numeric entry to `0..100` on blur.

Unit tests in this step:
- [x] Clicking the `+` / `-` buttons increments and decrements the live percent display.
- [x] Typing `60` into the number input and blurring updates local allocation state.
- [x] Typing `150` clamps to `100` on blur; `-10` clamps to `0`.
- [x] The reserved resources figure scales linearly with the allocation percent, computed as `floor(reservableResourcesThisTurn * pct / 100)`.
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
  - Current level as bold text in a pill immediately to the right of the field label, using the same accent colour as the field label and no `lvl` prefix.
  - A progress bar (simple div with a percent-width child) filled to `progress[f] / fieldCost(f)`.
  - `"progress / cost"` numeric pair.
  - Status marker: `● current`, `○ next`, or a click-to-switch `▷` affordance.
- [x] For fields at the cap (`levels[f] === RESEARCH_MAX_LEVEL`), show `MAX` and suppress the bar (the projection sets `remainingCost[f] === 0` for capped fields, so don't divide).
- [x] Clicking a row (or the `▷` affordance) when the field is below cap sets local state `currentField = f` (same effect as changing the dropdown).
- [x] The `● current` marker tracks *local* state, not the server's `research.currentField`, so the marker moves the moment the player edits.

Unit tests in this step:
- [x] Six rows render, one per canonical field, in canonical order.
- [x] The row matching the committed `currentField` shows `● current` on mount.
- [x] Clicking a different field's row moves the `● current` marker and updates local state.
- [x] A capped field renders `MAX` instead of the bar and numeric pair, and its row is disabled to click-to-switch.
- [x] The next marker (`○ next`) appears on the row matching `nextField`.

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

## Step 9 — Auto-save command diffing and wiring

- [x] On every committed control edit, build a `SetResearchCommand` with only the fields whose local value differs from `research` (the committed state), not from `pendingCommand`. This ensures the command carries the *full* set of edits-relative-to-server, which is what the backend expects.
- [x] `nextField` needs explicit `null` vs. `undefined` handling:
  - Omitted from the command if unchanged relative to the server.
  - Included as `null` when the player cleared it.
  - Included as a string when the player set it.
- [x] If every local field equals the committed state (i.e. the player reverted all edits manually), call `onChange(null)` so the caller can remove the pending research command entirely.
- [x] Otherwise call `onChange(cmd)` and remain in the workspace.
- [x] At the `App.tsx` call site, translate `onChange(cmd | null)` into `replaceCommands("research", cmd ? [cmd] : [])`.

Unit tests in this step:
- [x] Editing produces a command with only changed fields (assert via mock `onChange` receiving the expected partial).
- [x] Clearing `nextField` produces `{ nextField: null }` in the command.
- [x] Reverting every edit manually calls `onChange(null)`.
- [x] Edits leave the workspace mounted.

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

## Step 12 — Wire research workspace at App level

- [x] In `App.tsx`, extend mode state with `"research"`.
- [x] Pass `research={playerState.research}` and `mode="research"` support to `TopBar`.
- [x] Mount `<ResearchWorkspace ... />` as the main content when `mode === "research"`.
- [x] Add the `R` global keyboard handler (suppressed when a text input is focused) that switches to research mode, or returns to command mode when already in research. Reuse any existing `useGlobalShortcut`-style helper if one is present; otherwise inline the handler following the pattern already used for other top-level shortcuts.
- [x] Derive `ownedPlanetsLeftoverOnlyCount` and `ownedPlanetsCount` from `playerState.planets` at the call site.
- [x] Pass `pendingCommand` by reading the current dirty buffer's `research` scope and picking the single command (if any).
- [x] Wire `onChange` to `replaceCommands("research", cmd ? [cmd] : [])`.

Unit tests in this step (App-level integration, `frontend/src/App.test.tsx`):
- [x] Clicking the top-bar Research tab shows the workspace.
- [x] Pressing `R` with no input focused toggles between Command and Research mode.
- [x] Pressing `R` while an input is focused does not toggle.
- [x] Editing a control in the workspace populates the dirty buffer with exactly one `set_research` command.
- [x] Returning to the workspace shows the pending edit (not the server state).

---

## Step 13 — Lint, typecheck, test

- [x] `cd frontend && npm run lint` clean.
- [x] `cd frontend && npm run typecheck` clean.
- [x] `cd frontend && npm test` passes end-to-end.

---

## Step 14 — Backend next-field regression

While exercising the Research workspace, we found that completing a level did not switch `current_field` to `next_field`; research continued in the same field. This was a backend resolution bug, not a frontend state issue.

- [x] Add a backend regression test in [backend/tests/engine/test_research_resolution.py](../backend/tests/engine/test_research_resolution.py) proving that a level-up switches to `next_field`, clears `next_field`, and applies leftover points to the new current field.
- [x] Fix [backend/openstars/engine/resolve_steps/research.py](../backend/openstars/engine/resolve_steps/research.py) so `apply_research_points` switches to a valid non-capped `next_field` immediately after a level-up.
- [x] Run backend targeted test and checks:
  - `cd backend && uv sync --all-extras`
  - `cd backend && uv run pytest tests/engine/test_research_resolution.py`
  - `cd backend && uv run ruff check .`
  - `cd backend && uv run ruff format --check .`

---

## Deferred follow-ups

- **Projected leftover** line in the per-planet Research Contribution section — needs a queue-cost helper that doesn't yet exist client-side. Easy add once that helper lands.
- **Cross-planet allocation overview** inside the research workspace (beyond the simple `K of M` count).
- **Technology Browser** — a separate screen listing components/hulls by unlock; owned PRD-wise, not UI-wise, by this task. PRD 66's own deferred list calls this out.
- **Miniaturisation preview** surfaces for designer/production panes, dependent on the backend build-time-miniaturisation work in the neighbouring task file.
- **Multi-level-up bar animation** — cosmetic.
- **Per-field ETA column** for all six fields.
- **Allocation presets** (`0 / 15 / 50 / 100` buttons).
- **Multi-tab concurrent-edit warning** — deferred per PRD 66.

---

## Explicitly out of scope

- New backend feature work beyond the next-field regression fix recorded in Step 14 — this task otherwise assumes the backend work in [2026-04-24-research-and-technology.md](tasks/2026-04-24-research-and-technology.md) is landed (or mocked via fixtures).
- Browser/manual smoke tests — per [AGENTS.md](AGENTS.md) Cursor Cloud testing preference, automated checks (`npm test`, `typecheck`, `lint`) are the gate.
- Any rework of the event log rendering surface — PRD 66 explicitly routes level-up feedback through the existing log.
