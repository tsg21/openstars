# Tailwind: MutedText migration + SectionLabel primitive

**Date:** 2026-05-12

**Goal:** Two follow-on Tailwind refactors from the UI standardisation task:
1. Replace raw `text-*-muted-foreground` class combos with the existing `<MutedText>` primitive where it's a clean substitution.
2. Extract a new `<SectionLabel>` `ui/` primitive for the `uppercase tracking-widest text-muted-foreground` section-header pattern.

---

## Step 1 — Migrate raw muted-text usages to `<MutedText>`

`MutedText` already exists at `frontend/src/components/ui/MutedText.tsx` — it renders `text-muted-foreground` and accepts `className` for size overrides. There are ~15 raw instances where the element's only classes are `text-sm text-muted-foreground` or `text-xs text-muted-foreground` (plus simple spacing like `mt-1`, `pr-2`, `block`). These are clean substitutions.

Files to update:

- [x] `DesktopGate.tsx` — 2 instances (`text-sm` / `text-xs mt-1`)
- [x] `DesignsWorkspace.tsx` — 4 instances (`text-xs` × 1, `text-sm` × 3)
- [x] `ResearchWorkspace.tsx` — 2 instances (`text-sm pr-2`, `text-xs`)
- [x] `DetailPanel.tsx` — 1 instance (`text-xs mt-2`)
- [x] `FleetDetail.tsx` — 2 instances (`text-xs`)
- [x] `FleetComposer.tsx` — 3 instances (`text-sm`, `text-xs pt-1`, `text-xs`)
- [x] `PlanetDetail.tsx` — 1 instance (`text-xs block`)
- [x] `EventLog.tsx` — 1 instance (`text-xs`)
- [x] `RaceSelectionScreen.tsx` — 1 instance (`text-sm`)

**Skip** any element where the class string also contains layout, border, background, or interactive tokens — those are containers or interactive elements that should stay as-is.

Relevant checks:
- `cd frontend && npm run typecheck`
- `cd frontend && npm test`

---

## Step 2 — Extract `<SectionLabel>` primitive

The `text-xs uppercase tracking-widest text-muted-foreground` pattern is used in 4 places in `PlanetDetail.tsx` as sub-section headings ("Fleets in Orbit", "Planet", "Starbase", "Research"). A close variant (`text-[10px] uppercase tracking-widest text-muted-foreground`) appears twice in `RaceSelectionScreen.tsx`.

- [x] Create `frontend/src/components/ui/SectionLabel.tsx`
  - Renders a `<div>` by default; accepts optional `as` prop (polymorphic, same pattern as `MutedText`)
  - Base classes: `text-xs uppercase tracking-widest text-muted-foreground`
  - Accepts `className` for overrides (e.g. `text-[10px]` for the smaller RaceSelectionScreen variant)
  - Accepts `children`
- [x] Unit test: renders children with correct base classes; `className` merges correctly
- [x] Export from `frontend/src/components/index.ts`
- [x] Update `frontend/AGENTS.md` `ui/` component list to include `SectionLabel`

Relevant checks:
- `cd frontend && npm test -- SectionLabel`
- `cd frontend && npm run typecheck`

---

## Step 3 — Replace raw instances with `<SectionLabel>`

- [x] `PlanetDetail.tsx` — replace all 4 instances (`text-xs uppercase tracking-widest text-muted-foreground`)
- [x] `RaceSelectionScreen.tsx` — replace both instances using `className="text-[10px]"` override

Relevant checks:
- `cd frontend && npm run typecheck`
- `cd frontend && npm test`
