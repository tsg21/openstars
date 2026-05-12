# Frontend UI standardisation

**Date:** 2026-05-12

**Goal:** Reduce Tailwind CSS repetition by reorganising the component directory into `ui/` (primitives) and `panels/` (feature views), filling the three highest-repetition gaps with new primitives, and refactoring all panels to use them consistently.

## Background

Analysis identified ~300+ raw Tailwind class pattern occurrences across 23 component files. The highest-value gaps:
- 15+ instances of the same compact input/select field styling (scattered across WaypointTaskEditor, FleetDetail, RaceSelectionScreen, FleetComposer)
- 15+ instances of rounded-pill status badge styling
- 8+ instances of the same red validation error container
- `PanelCard` and `DetailPanelCard` overlap without a clear hierarchy

---

## Step 1 — Reorganise directory structure

Move files into `ui/` and `panels/` subdirectories. No logic changes; only import paths update.

**`components/ui/`** — reusable primitives (no game-domain knowledge):
- [x] Move `Button.tsx`
- [x] Move `FormField.tsx`
- [x] Move `MutedText.tsx`
- [x] Move `PanelCard.tsx`
- [x] Move `DetailPanelLayout.tsx`
- [x] Move `ResourceBars.tsx`
- [x] Move `DesktopGate.tsx`

**`components/panels/`** — feature views (game-domain, composed from `ui/`):
- [x] Move `DetailPanel.tsx`
- [x] Move `PlanetDetail.tsx`
- [x] Move `FleetDetail.tsx`
- [x] Move `ResearchWorkspace.tsx`
- [x] Move `DesignsWorkspace.tsx`
- [x] Move `EventLog.tsx`
- [x] Move `TopBar.tsx`
- [x] Move `GalaxyMap.tsx`
- [x] Move `GameLobby.tsx`
- [x] Move `RaceSelectionScreen.tsx`
- [x] Move `WaypointTaskEditor.tsx`
- [x] Move `FleetComposer.tsx`

Update all import paths in:
- [x] `App.tsx`
- [x] All moved files that import each other
- [x] Test files (including `vi.mock` paths)

Relevant checks:
- `cd frontend && npm run typecheck`
- `cd frontend && npm test`

---

## Step 2 — Add `CompactInput` and `CompactSelect` to `ui/FormField.tsx`

The existing `TextInput` / `SelectInput` are full-width, `text-sm`, `px-3 py-1.5`. Add compact variants for inline use:

```
rounded border border-[var(--color-panel-border)] bg-black/30 px-1.5 py-0.5 text-xs text-foreground
```

- [x] Add `CompactInput` component (same props as `TextInput` minus width constraint)
- [x] Add `CompactSelect` component (same props as `SelectInput`)
- [x] Unit tests for both variants render correctly

Relevant checks:
- `cd frontend && npm test -- FormField`
- `cd frontend && npm run typecheck`

---

## Step 3 — Add `ErrorBox` to `ui/`

Consolidate the red validation error container used in 8+ places:

```
rounded-md border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-400
```

- [x] Create `frontend/src/components/ui/ErrorBox.tsx` — accepts `children`
- [x] Unit test: renders children inside the styled container

Relevant checks:
- `cd frontend && npm test -- ErrorBox`
- `cd frontend && npm run typecheck`

---

## Step 4 — Add `StatusBadge` to `ui/`

Consolidate the rounded-pill badge (research levels, race trait indicators, etc.):

```
rounded-full border border-[var(--color-panel-border)] bg-background/60 px-2.5 py-0.5 text-sm font-bold
```

- [x] Create `frontend/src/components/ui/StatusBadge.tsx` — accepts `children` and optional `className` for colour overrides
- [x] Unit test: renders children with correct base classes

Relevant checks:
- `cd frontend && npm test -- StatusBadge`
- `cd frontend && npm run typecheck`

---

## Step 5 — Consolidate `PanelCard` / `DetailPanelCard`

- [x] Audited usages: `PanelCard` = outer lobby/race cards; `DetailPanelCard` = inner elevated surfaces in detail panels
- [x] Added `variant="surface"` prop to `PanelCard` (uses `elevated-surface` CSS class for shadow + `bg-surface-2`, `rounded-md`, `p-3`)
- [x] Migrated all `DetailPanelCard` usages in `PlanetDetail` and `FleetDetail` to `<PanelCard variant="surface">`
- [x] Deleted `DetailPanelCard` from `DetailPanelLayout.tsx`

Relevant checks:
- `cd frontend && npm run typecheck`
- `cd frontend && npm test`

---

## Step 6 — Refactor panels to use new primitives

Replace raw Tailwind instances in panel files with the new components from Steps 2–5.

- [x] `WaypointTaskEditor.tsx` — replaced raw selects/inputs → `CompactSelect` / `CompactInput`
- [x] `FleetDetail.tsx` — replaced warp input → `CompactInput`
- [x] `GameLobby.tsx` — replaced error containers → `ErrorBox`
- [x] `ResearchWorkspace.tsx` — replaced research level badge → `StatusBadge`
- [x] Note: `FleetComposer.tsx` table inputs use `bg-transparent` (different context, intentionally left as-is); `RaceSelectionScreen.tsx` uses `--color-status-danger` semantic token rather than the `red-*` utility pattern, so `ErrorBox` was not applied there

Relevant checks:
- `cd frontend && npm run typecheck` ✓
- `cd frontend && npm test` ✓ (279/279)

---

## Step 7 — Finish surface-card consolidation in RaceSelectionScreen

`RaceSelectionScreen.tsx` still has 5 raw instances of:

```
rounded-md border border-[var(--color-panel-border)] bg-[var(--color-surface-2)] p-3
```

Replace each with `<PanelCard variant="surface">` to complete the surface-card consolidation.

- [x] Replaced 3 convertible instances (disabled PRT button, disabled locked-LRT button, economy field div) → `<PanelCard variant="surface">`
- [x] Note: 2 remaining instances are `<label>` elements wrapping checkboxes — must stay as `<label>` for accessibility; PanelCard does not support `as="label"`

Relevant checks:
- `cd frontend && npm run typecheck` ✓
- `cd frontend && npm test` ✓ (279/279)
