# Ship Designer — drag-and-drop UI

**Date:** 2026-05-09
**Goal:** Replace the select-box-based ship/starbase fitter in [DesignsWorkspace.tsx](frontend/src/components/DesignsWorkspace.tsx) with a drag-and-drop designer that renders each hull's slot grid (cross / T / asymmetric layouts) and lets the player drag components from a palette into slots. Reads hull layouts from the backend (`GET /api/v1/games/{game_id}/designs/reference-data`), which now serves the `layout_grid`, `position`, `size`, `cargo_layout`, and `dock_layout` fields added to [hulls.yaml](backend/openstars/data/hulls.yaml) on 2026-05-09.
**Relevant PRDs:** [18 — Ship Design](docs/prd/18-ship-design.md), [19 — Hull Slot Definitions](docs/prd/19-hull-slot-definitions.md), [20 — Design Components Catalogue](docs/prd/20-design-components-catalogue.md), [60 — UI Overview](docs/prd/60-ui-overview.md)

---

## Preamble — PRD 18 update

PRD 18 currently scopes drag-and-drop and pixel-positioned hull rendering as deferred ("Drag-and-drop is also deferred for MVP", "Pixel-positioned hull silhouette rendering in the first pass designer UI"). This task makes the drag-and-drop slot-grid designer the canonical interaction model, so PRD 18 needs to be brought into line per [AGENTS.md](AGENTS.md) PRD authoring rules.

- [x] Edit [docs/prd/18-ship-design.md](docs/prd/18-ship-design.md):
  - Remove the bullet "Pixel-positioned hull silhouette rendering in the first pass designer UI" from the Out of Scope list.
  - Replace the "Designer Screen Structure (first pass MVP)" section with the **Designer Screen Structure** that we are now implementing: a hull-layout canvas of slot cells (positions sourced from PRD 19's layout fields), a draggable component palette, per-slot capacity badges, and a derived-stats panel.
  - Replace the line "Hull silhouette/canvas rendering is deferred. Drag-and-drop is also deferred for MVP. The first pass should focus on correctness of slot legality, component counts, derived stats, and save flow." with prose making drag-and-drop and grid-positioned slot rendering canonical, while keeping a note that per-slot up/down steppers remain available alongside DnD for accessibility / non-mouse use.
  - In the Interaction Flow, change "per-slot select boxes and count controls" to "drag from the component palette into compatible slots, with up/down steppers as a fallback".
- [x] Edit [docs/prd/19-hull-slot-definitions.md](docs/prd/19-hull-slot-definitions.md):
  - Update the "Source and fidelity" / "This is a logical slot reference, not a pixel-placement or silhouette-shape reference" wording — it now is also the source of grid-positioned slot layout for the designer.
  - Add a short subsection documenting the layout schema added to [hulls.yaml](backend/openstars/data/hulls.yaml) and exposed in `component_catalogue.py`: `layout_grid {w,h}`, per-slot `position {x,y}` and `size {w,h}`, plus hull-level `cargo_layout` / `dock_layout` rectangles. Coordinates are integer cells; `(0,0)` is top-left.
  - Remove the "Add page-image-backed coordinate extraction if silhouette-position layout becomes necessary later" follow-up — superseded.
- [x] Re-index the RAG: `scripts/rag-index`.

No code unit tests in this preamble (docs-only).

---

## Step 1 — Frontend type alignment

The backend schema added several slot categories and layout fields that [frontend/src/types/designer.ts](frontend/src/types/designer.ts) doesn't yet model. Bring it back in sync so the API client surfaces the data.

- [x] In [frontend/src/types/designer.ts](frontend/src/types/designer.ts):
  - Extend `ComponentType` with the missing variants: `"electrical" | "mechanical" | "bomb" | "mine_layer" | "robot_miner" | "torpedo" | "planetary"`. Note: `ComponentType` and `SlotCategory` are presently the same alias — split them. `ComponentType` follows the backend `Literal[...]` in [component_catalogue.py](backend/openstars/engine/component_catalogue.py); `SlotCategory` separately includes `"general_purpose"` and `"orbital"`, which are slot kinds, not concrete component types.
  - Add the missing per-component stat blocks: `electrical?: { ability: number }`, `mechanical?: { ability: number }`, plus `torpedo?` and `planetary?` if needed for completeness.
  - Add `GridPosition`, `GridSize`, `GridRect` interfaces matching the backend models.
  - Extend `HullSlotDefinition` with `position?: GridPosition` and `size?: GridSize`.
  - Extend `HullDefinition` with: `domain: "ship" | "starbase"`, `fuelCapacity: number`, `cargoCapacity: number`, `dockCapacity: number`, `armourPoints: number`, `initiative: number`, `layoutGrid?: GridSize`, `cargoLayout?: GridRect`, `dockLayout?: GridRect`. Today the type only has `engineRequiredSlots` and `fuelCapacity` — derive `engineRequiredSlots` from the slot list rather than expecting a top-level field, and remove it from the interface.
  - Confirm `keysToCamel` in [frontend/src/api/client.ts](frontend/src/api/client.ts) handles the nested `{x,y,w,h}` mappings in flow-style YAML (these come through as plain JSON objects, so should already work — verify).
- [x] Update any `HullDefinition` literals in tests under [frontend/src/components/DesignsWorkspace.test.tsx](frontend/src/components/DesignsWorkspace.test.tsx) to either include the new required fields or use a small `makeHull(...)` factory.

Unit tests in this step:
- [x] In `frontend/src/api/client.test.ts`, add a fixture asserting that a designer reference-data response containing `layout_grid: {w:4,h:1}` and a slot with `position: {x:0,y:0}, size: {w:1,h:2}` round-trips through `keysToCamel` to `layoutGrid` / `position` / `size` correctly.

---

## Step 2 — Backend: allow starbase domain in reference-data

The `GET /designs/reference-data` route in [backend/openstars/server/routes/designs.py](backend/openstars/server/routes/designs.py) currently rejects `domain != "ship"` with `UNSUPPORTED_DOMAIN`. The new starbase hulls in [hulls.yaml](backend/openstars/data/hulls.yaml) need to be reachable through the same endpoint so one designer surface serves both domains (per PRD 18).

- [x] In [backend/openstars/server/routes/designs.py](backend/openstars/server/routes/designs.py), accept `domain in {"ship", "starbase"}` and pass through to `_hulls_for_domain`. Reject other values with `UNSUPPORTED_DOMAIN`.
- [x] Component list returned in the response is the same regardless of domain (slot/component compatibility is enforced per-slot, not at the catalogue level).

Unit tests in this step (`backend/tests/server/test_designs_route.py`):
- [x] `GET /designs/reference-data?domain=starbase` returns 200 with `domain: "starbase"` and a non-empty `hulls` list whose entries all have `hull.domain == "starbase"` (e.g. `orbital_fort`, `space_dock`, `death_star`).
- [x] `GET /designs/reference-data?domain=invalid` still returns 400 `UNSUPPORTED_DOMAIN`.
- [x] Existing `domain=ship` behaviour is unchanged.

---

## Step 3 — Add a drag-and-drop library

`@dnd-kit/core` is the recommended choice: TypeScript-first, accessible (keyboard-draggable out of the box, which matters for the stepper-fallback parity), no HTML5 drag image quirks, ~10kB gzipped, MIT, actively maintained. `react-dnd` is heavier and has flakier touch behaviour.

- [x] `cd frontend && npm install @dnd-kit/core` (no sortable extension needed for v1 — slots are positional drop targets, not a sortable list).
- [x] Add to the appropriate dependency block in [frontend/package.json](frontend/package.json) (runtime deps, not devDeps).

No unit tests for the install itself.

---

## Step 4 — `HullLayout` read-only renderer

A pure visual component that draws a hull's slot grid from its `HullDefinition`. No interactivity yet — used in the next step as the canvas for drop targets, but standalone-testable now.

New file: [frontend/src/components/designer/HullLayout.tsx](frontend/src/components/designer/HullLayout.tsx).

- [x] Component signature: `HullLayout({ hull, renderSlot, renderCargo?, renderDock? })`. Default render functions show an empty slot box labelled with the slot's category abbreviation and "0/N" capacity badge; default cargo/dock render shows the kt capacity. Children-as-render-prop keeps the layout component dumb and reusable.
- [x] Translate the `(x, y, w, h)` cell coordinates into CSS Grid placement: `gridColumn: \`${x+1} / span ${w}\``, `gridRow: \`${y+1} / span ${h}\``. Outer container uses `display: grid` with `grid-template-columns: repeat(layoutGrid.w, var(--designer-cell-size))` and the same for rows.
- [x] Add `--designer-cell-size: 4rem` (configurable) as a CSS custom property in [frontend/src/index.css](frontend/src/index.css) per the styling-tokens guidance in [frontend/AGENTS.md](frontend/AGENTS.md).
- [x] Empty cells should remain visually distinguishable (faint border, no fill) so cross-shaped hulls read correctly.
- [x] Where `cargoLayout` / `dockLayout` is present, render that rect inside the grid before slots so slots stack on top if they share a cell (they shouldn't per the validator we ran, but defensive ordering helps catch authoring bugs visually).

Unit tests in this step (`frontend/src/components/designer/HullLayout.test.tsx`):
- [x] Renders the correct number of slot cells for `small_freighter` (3 slots) and reads slot labels from the categories.
- [x] Reads slot positions: a slot with `position: {x:2,y:1}, size: {w:1,h:2}` renders with `gridColumn: 3 / span 1` and `gridRow: 2 / span 2` (assert via inline style or `data-grid-pos` attribute).
- [x] Renders cargo box for a hull with `cargoLayout` (e.g. `large_freighter`).
- [x] Renders dock box for a starbase with `dockLayout` (e.g. `space_dock`).
- [x] Uses fixture hulls in the test (don't fetch from the backend); a `makeHull(...)` factory beside the component is fine.

---

## Step 5 — `ComponentPalette` read-only renderer

A vertical panel listing available components grouped by `componentType`, each entry showing the component's name, mass, and (if a primary stat exists) a one-line summary. Visual only at this step.

New file: [frontend/src/components/designer/ComponentPalette.tsx](frontend/src/components/designer/ComponentPalette.tsx).

- [x] Component signature: `ComponentPalette({ components, slotCategoryFilter? })`. The optional `slotCategoryFilter` parameter dims components that aren't compatible with any slot of that category — useful when the player has a slot selected.
- [x] Group order matches PRD 20 / `ComponentType` declaration order: engines, scanners, weapons, torpedoes, shields, armour, electrical, mechanical, bombs, mine layers, robot miners, planetary.
- [x] Each component card renders with `data-component-id` so the next step can attach drag handlers.
- [x] Filter components by player tech levels — if the API response in this game already filters server-side, leave client filtering off; otherwise, accept a `playerTech` prop and dim locked components. Confirm by reading the `_catalogue` shape returned from `GET /designs/reference-data`. (Currently the backend returns the full catalogue without per-player filtering — flag this as a separate PRD-21 follow-up if it bites.)

Unit tests in this step (`frontend/src/components/designer/ComponentPalette.test.tsx`):
- [x] Groups components by type with the canonical ordering.
- [x] Renders mass and the primary stat (e.g. shield points for shields, fuel curve summary for engines).
- [x] When `slotCategoryFilter="weapon"` is set, weapon components are highlighted and others are dimmed (assert via class or `aria-disabled`).
- [x] No drag behaviour is asserted yet (added in step 6).

---

## Step 6 — Wire drag-and-drop: palette → slots

This is the core of the feature. Components in the palette become `useDraggable`, slots become `useDroppable`, and a `DndContext` at the workspace root mediates drops. Fit state lives in a lifted `useState` in the workspace, replacing the current `slotDrafts` array.

- [x] In a new [frontend/src/components/designer/DragAndDropFitter.tsx](frontend/src/components/designer/DragAndDropFitter.tsx), compose `<DndContext>`, `<HullLayout>`, and `<ComponentPalette>`. Owns the fit state: `Map<slotNumber, { componentId: string; componentCount: number }>` (one fitted component type per slot — see the "one component type per slot" rule below).
- [x] Each palette card uses `useDraggable({ id: \`palette-${componentId}\`, data: { kind: "palette", componentId } })`.
- [x] Each slot cell rendered via `HullLayout`'s `renderSlot` prop uses `useDroppable({ id: \`slot-${slotNumber}\`, data: { kind: "slot", slotNumber, slotCategories } })`.
- [x] On `onDragEnd`, look up the dragged component's `componentType`, check it intersects the target slot's `slotCategories`, and if compatible, increment that slot's count for that component (capped at the slot's `capacity`). Reject silently with a brief shake animation if not compatible.
- [x] **One component type per slot.** A slot's `slotCategories` lists which categories are *legal* for it (e.g. `[shield, armour]` means either kind can go there), but a fitted slot holds exactly one component type. Dragging a *different* component type onto an already-occupied slot replaces the existing fit, with a confirm prompt if the slot currently has anything in it. Dragging the *same* component type onto an occupied slot increments its count up to `capacity`. The fit-state shape `Map<slotNumber, { componentId, componentCount }>` (single object per slot, not a list) reflects this rule directly — drop the `[]` wrapper from the earlier shape.
- [x] Slots already containing components also accept a click on a `−` button to decrement, mirror of the existing stepper. Drag-to-remove out of the slot back to the palette is **out of scope** for v1 — clicks/keys handle removal.
- [x] Keyboard equivalence: `@dnd-kit/core` has `KeyboardSensor` built in. Wire it so a slot can be focused and components added via keyboard, satisfying the "stepper fallback" mention in PRD 18.

Unit tests in this step (`frontend/src/components/designer/DragAndDropFitter.test.tsx`):
- [x] Dragging a `colloidal_phaser` onto a Cruiser slot 4 (`weapon`) results in fit state `[{slotNumber: 4, componentId: "colloidal_phaser", componentCount: 1}]`. Use `@dnd-kit`'s testing utilities or simulate the `onDragEnd` callback directly.
- [x] Dragging the same component onto a non-weapon slot (e.g. Cruiser slot 1, `engine`) leaves fit state unchanged.
- [x] Dragging a 3rd `colloidal_phaser` onto a Cruiser slot 4 (capacity 2) caps the count at 2.
- [x] Dragging a second component **type** onto an occupied slot triggers the replacement path (assert via callback or confirm-prompt mock).
- [x] Pressing `Enter` on a focused slot with a focused palette item adds the component (keyboard parity).

---

## Step 7 — Validation feedback and required-slot UX

Make legality visible at all times: required slots that aren't filled, slots over capacity (shouldn't be possible after step 6 but guard anyway), missing engine count.

- [x] Engine slots have `required: true` and a `capacity` that means "needs exactly N engines" (note: in the backend YAML this is encoded as `capacity: N, required: true`, where `required` flips the semantic from "up to N" to "exactly N"). Display required slots with a coloured outline when unfilled.
- [x] Compute a `validationErrors: string[]` from the fit state on every render. Errors include: "Engine slot 1 needs 4 engines" / "Slot 3 (Shield/Armour) is required".
- [x] Show errors in a `ValidationPanel` rendered alongside the derived-stats panel.
- [x] Disable the Save button when `validationErrors.length > 0`.
- [x] Do **not** duplicate the server's authoritative validation logic — this is a usability aid only (per PRD 18 "Validation UX"). Server still runs its full check on `POST /designs`.

Unit tests in this step (extend `DragAndDropFitter.test.tsx`):
- [x] Cruiser with no engines fitted reports `"Slot 1 (Engine) needs 2 engines"`.
- [x] Cruiser with 1 engine fitted (capacity 2, required) still reports an error until 2 are fitted.
- [x] Cruiser with all required slots filled reports zero errors.
- [x] Save button is disabled when `validationErrors.length > 0`, enabled when empty.

---

## Step 8 — Live derived-stats preview

The server is authoritative on save, but the player should see cost / mass / fuel / scanner range as they fit. This mirrors the original Stars! "Save Design" status panel.

- [x] New helper [frontend/src/lib/designerStats.ts](frontend/src/lib/designerStats.ts): pure function `computeDerivedStats(hull, components, fitState)` returning `{ cost: ComponentCost, mass: number, fuelCapacity: number, cargoCapacity: number, armour: number, scanner: { normal, penetrating } | null }`.
- [x] Cost = hull cost + Σ(component cost × count). Mass = hull mass + Σ(component mass × count). Scanner range = max of fitted scanner components (per Stars! rules — confirm against PRD 11). Armour = hull armour + Σ(armour component points × count).
- [x] New component [frontend/src/components/designer/StatsPanel.tsx](frontend/src/components/designer/StatsPanel.tsx) renders the result as a labelled list. Costs go through the existing minerals colour tokens in [frontend/src/index.css](frontend/src/index.css).

Unit tests in this step (`frontend/src/lib/designerStats.test.ts`):
- [x] Empty fit returns hull-only stats (e.g. small freighter cost = 20/12/0/17).
- [x] Adding 1 quick jump 5 engine increases mass by the engine's mass and cost by the engine's cost.
- [x] Adding 2 of the same scanner doesn't double the scan range (max, not sum).
- [x] Cargo capacity is taken from the hull, not affected by fitted components.

---

## Step 9 — Replace select-box fitter in `DesignsWorkspace`

Swap the existing per-slot select-box section in [DesignsWorkspace.tsx](frontend/src/components/DesignsWorkspace.tsx) for the new `DragAndDropFitter`. Keep the surrounding flow (list of saved designs, hull picker, name field, save button, error display) intact.

- [x] Where `slotDrafts` is set up and rendered today, mount `<DragAndDropFitter hull={selectedHull} components={referenceData.components} value={fitState} onChange={setFitState} />`.
- [x] Translate the new `Map<slotNumber, ...>` fit state into the existing `DesignerCreateDesignComponent[]` shape just before calling `createDesign(...)`.
- [x] Keep the existing `creating` / `saving` / `error` state machine as-is; only the fit editor changes.
- [x] Hull picker should now show both ship and starbase hulls when a domain selector is added — but keep the v1 designer scoped to ships unless the hull picker's domain switch is trivial. (Add a `domain` toggle in a follow-up if not.)
- [x] Remove the now-unused `SelectInput`-driven slot row code and its associated state. Don't leave dead code or a feature flag.

Unit tests in this step:
- [x] Existing [DesignsWorkspace.test.tsx](frontend/src/components/DesignsWorkspace.test.tsx) tests should still pass — update assertions for any text/structure changes (the design list, hull picker, save flow shouldn't change behaviour).
- [x] Add one new test: selecting a hull, dragging the minimum required components in via the fitter, entering a name, and clicking Save calls `createDesign` with the expected payload.

---

## Step 10 — Lint, typecheck, manual smoke

- [x] `cd frontend && npm run lint` passes.
- [x] `cd frontend && npm run typecheck` passes.
- [x] `cd frontend && npm test` passes (all designer-related tests + unaffected suites).
- [x] `cd backend && uv run pytest` passes.
- [ ] **Manual UI smoke** (only when explicitly invoked — see [AGENTS.md](AGENTS.md) testing preference): start the backend (`STORAGE_BACKEND=memory uv run uvicorn ...`) and frontend (`npm run dev`), open the Designs workspace in a real browser, and verify:
  - Hull picker lists all 32 ship hulls.
  - Selecting a Cruiser shows the cross-shaped slot grid (engine left, weapons top/bottom, GP right).
  - Dragging a Quick Jump 5 engine onto slot 1 increments its count to 1; dragging a second increments to 2.
  - Dragging a Phaser onto slot 1 (engine slot) is rejected.
  - Save button enables once all required slots are filled and a name is entered.
  - Saved design appears in the list with correct derived cost.

---

## Out of scope for this task

- **Drag-to-remove** out of slots back to the palette (use the `−` stepper or click-to-clear instead).
- **Tooltips** with full component stats on hover.
- **Per-player tech filtering of the component palette** — relies on PRD 21 player-tech surfacing in the reference-data response. Track as a follow-up.
- **Starbase designer parity in `DesignsWorkspace`** — the `domain=starbase` API works after step 2, but a domain toggle in the workspace UI is deferred unless trivial in step 9.
- **Battle simulator integration**, **edit existing design**, **delete design**, **auto-upgrade** — all already deferred by PRD 18.

---

## Post-task refinements

- [x] Show original 64×64 component images from the assets manifest in the draggable palette entries.
- [x] Replace the all-groups palette with a right-hand component navigation section: a vertical component-type tab rail and a filtered draggable list for the active type.
- [x] Move the design name field to the top of the create form and remove the visible validation section while retaining save validation.
- [x] Arrange the designer as two columns: name/hull/hull-layout/save on the left, and a full-height component palette on the right.
- [x] Show fitted component images in hull slots instead of "Empty" text or component names.

---

## Follow-ups to log when complete

- Domain toggle (ship ↔ starbase) in `DesignsWorkspace`.
- Per-player tech filtering of the component palette (depends on PRD 21).
- Drag-to-remove and component tooltips.
- Persisting an in-progress design as a draft before save.
