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
- [ ] Move `Button.tsx`
- [ ] Move `FormField.tsx`
- [ ] Move `MutedText.tsx`
- [ ] Move `PanelCard.tsx`
- [ ] Move `DetailPanelLayout.tsx`
- [ ] Move `ResourceBars.tsx`
- [ ] Move `DesktopGate.tsx`

**`components/panels/`** — feature views (game-domain, composed from `ui/`):
- [ ] Move `DetailPanel.tsx`
- [ ] Move `DetailPanelLayout.tsx` (re-export from `ui/` or move entirely — decide on move)
- [ ] Move `PlanetDetail.tsx`
- [ ] Move `FleetDetail.tsx`
- [ ] Move `ResearchWorkspace.tsx`
- [ ] Move `DesignsWorkspace.tsx`
- [ ] Move `EventLog.tsx`
- [ ] Move `TopBar.tsx`
- [ ] Move `GalaxyMap.tsx`
- [ ] Move `GameLobby.tsx`
- [ ] Move `RaceSelectionScreen.tsx`
- [ ] Move `WaypointTaskEditor.tsx`
- [ ] Move `FleetComposer.tsx`

Update all import paths in:
- [ ] `App.tsx`
- [ ] `Root.tsx`
- [ ] All moved files that import each other
- [ ] Test files

Relevant checks:
- `cd frontend && npm run typecheck`
- `cd frontend && npm test`

---

## Step 2 — Add `CompactInput` and `CompactSelect` to `ui/FormField.tsx`

The existing `TextInput` / `SelectInput` are full-width, `text-sm`, `px-3 py-1.5`. Add compact variants for inline use:

```
rounded border border-[var(--color-panel-border)] bg-black/30 px-1.5 py-0.5 text-xs text-foreground
```

- [ ] Add `CompactInput` component (same props as `TextInput` minus width constraint)
- [ ] Add `CompactSelect` component (same props as `SelectInput`)
- [ ] Unit tests for both variants render correctly

Relevant checks:
- `cd frontend && npm test -- FormField`
- `cd frontend && npm run typecheck`

---

## Step 3 — Add `ErrorBox` to `ui/`

Consolidate the red validation error container used in 8+ places:

```
rounded-md border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-400
```

- [ ] Create `frontend/src/components/ui/ErrorBox.tsx` — accepts `children`
- [ ] Unit test: renders children inside the styled container

Relevant checks:
- `cd frontend && npm test -- ErrorBox`
- `cd frontend && npm run typecheck`

---

## Step 4 — Add `StatusBadge` to `ui/`

Consolidate the rounded-pill badge (research levels, race trait indicators, etc.):

```
rounded-full border border-[var(--color-panel-border)] bg-background/60 px-2.5 py-0.5 text-sm font-bold
```

- [ ] Create `frontend/src/components/ui/StatusBadge.tsx` — accepts `children` and optional `className` for colour overrides
- [ ] Unit test: renders children with correct base classes

Relevant checks:
- `cd frontend && npm test -- StatusBadge`
- `cd frontend && npm run typecheck`

---

## Step 5 — Consolidate `PanelCard` / `DetailPanelCard`

Currently two overlapping surface-card patterns exist. Decide on one and remove the other.

- [ ] Audit usages of `PanelCard` vs `DetailPanelCard` (from `DetailPanelLayout`)
- [ ] Decide which to keep as the canonical surface card (likely `PanelCard` — it's already polymorphic)
- [ ] Migrate `DetailPanelCard` usages to `PanelCard` (or promote `DetailPanelCard` and deprecate `PanelCard`)
- [ ] Delete the redundant component
- [ ] Add a `surface` variant or prop if needed to cover the `bg-[var(--color-surface-2)]` use case

Relevant checks:
- `cd frontend && npm run typecheck`
- `cd frontend && npm test`

---

## Step 6 — Refactor panels to use new primitives

Replace raw Tailwind instances in panel files with the new components from Steps 2–5.

- [ ] `WaypointTaskEditor.tsx` — replace raw compact inputs/selects → `CompactInput` / `CompactSelect`
- [ ] `FleetDetail.tsx` — replace raw compact inputs, validation errors → `CompactInput`, `ErrorBox`
- [ ] `FleetComposer.tsx` — replace raw compact inputs → `CompactInput` / `CompactSelect`
- [ ] `RaceSelectionScreen.tsx` — replace raw inputs, error boxes, status badges → new components
- [ ] `GameLobby.tsx` — replace error boxes → `ErrorBox`
- [ ] `ResearchWorkspace.tsx` — replace status badges → `StatusBadge`
- [ ] `PlanetDetail.tsx` — replace any remaining raw panel patterns → `PanelCard`
- [ ] Verify no remaining raw instances of the consolidated class strings

Relevant checks:
- `cd frontend && npm run typecheck`
- `cd frontend && npm test`
- `cd frontend && npm run lint`
