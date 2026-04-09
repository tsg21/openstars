# Designer MVP (PRD 18 + PRD 20)

Implement the first-pass Designs mode and basic designer workflow described in:

- `docs/prd/18-ship-design.md`
- `docs/prd/19-hull-slot-definitions.md`
- `docs/prd/20-design-components-catalogue.md`

This MVP favours correctness and delivery speed over rich interaction: no silhouette canvas, no drag-and-drop, no icons required.

## Scope

In scope:

- Backend YAML component catalogue loader (one file per component type)
- Dummy component catalogue data for first-pass designer use
- Backend APIs needed for first-pass designer flow
- Frontend `Designs` mode and basic form-driven designer UI (select boxes + count inputs)
- Create-and-read design flow for ships (starbase parity scaffolded where practical)

Out of scope:

- Design editing and deletion
- Pixel-positioned hull silhouette rendering
- Drag-and-drop component placement
- Full balancing and complete real component catalogue values
- Full starbase design authoring completion (shared UI path can be scaffolded, final behaviour can follow-up)

---

## Step 1: Add component catalogue models and YAML loader (backend)

- [x] Add backend models for component catalogue documents and entries (shared/common fields + per-type effect blocks)
- [x] Add loader that reads `backend/openstars/data/components/*.yaml` and validates all files at load
- [x] Add deterministic error reporting for invalid YAML/schema (file + entry context)
- [x] Add unit tests for:
  - successful load of valid YAML
  - missing required top-level fields
  - invalid enum values (`component_type`)
  - invalid numeric constraints (`component_count_min/max`, negative costs)
- [x] Run `cd backend && uv run pytest tests/engine`

---

## Step 2: Add dummy component YAML files (one per type)

- [x] Create `backend/openstars/data/components/` with one YAML file per type:
  - `engines.yaml`
  - `scanners.yaml`
  - `weapons.yaml`
  - `shields.yaml`
  - `armour.yaml`
- [x] Populate each file with minimal dummy entries sufficient to exercise slot assignment and derived stat calculations
- [x] Add backend tests ensuring all expected files exist and parse as valid catalogue docs
- [x] Run `cd backend && uv run pytest tests/engine`

---

## Step 3: Add hull-definition read model for designer (backend)

- [x] Add backend-owned hull-definition read model derived from `PRD 19` slot definitions (ship hulls first)
- [x] Expose allowed slot categories, per-slot capacity, and engine requirements in a machine-readable form
- [x] Add unit tests for hull-definition integrity:
  - unique `slot_number` per hull
  - valid slot category enum mapping
  - required engine slots correctly marked
- [x] Run `cd backend && uv run pytest tests/engine`

---

## Step 4: Add first-pass designer APIs (backend)

- [x] Add API endpoint(s) to fetch designer reference data for the selected domain (`ship` initially):
  - hull definitions
  - component catalogue entries
- [x] Keep design list/detail/create endpoints aligned with PRD 18 (`GET summary`, `GET detail`, `POST create`)
- [x] Validate create payload against hull slot rules + component catalogue rules:
  - slot compatibility
  - required slots present
  - `component_count` bounds
- [x] Compute derived stats and cost from selected components (MVP formulas/placeholders as documented in code)
- [x] Add server tests for:
  - successful reference-data fetch
  - create validation failures
  - successful design creation with dummy components
  - summary/detail response shapes
- [x] Run `cd backend && uv run pytest tests/server tests/engine`

---

## Step 5: Implement `Designs` mode shell in frontend

- [x] Add top-level mode switch so `Designs` replaces Command View workspace
- [x] Add Designs landing view:
  - list existing designs
  - select design for read-only inspect
  - `Create New` action
- [x] Ensure `Create New` flow begins with hull selection
- [x] Add frontend tests for mode switch and landing flow
- [x] Run `cd frontend && npm test`
- [x] Run `cd frontend && npm run typecheck`

---

## Step 6: Implement basic form-driven designer UI (frontend MVP)

- [x] Build first-pass slot-list designer UI:
  - slot rows/table
  - per-slot component select box
  - `component_count` control
  - name input + save button
- [x] Surface validation feedback from backend and client pre-checks
- [x] Show derived stats and cost summary from backend response model
- [x] Submit create request and return to design list on success
- [x] Add frontend tests for:
  - slot assignment interactions
  - save enable/disable states
  - successful create flow
  - representative validation error rendering
- [x] Run `cd frontend && npm test`
- [x] Run `cd frontend && npm run typecheck`
- [x] Run `cd frontend && npm run lint`

---

## Step 7: End-to-end verification and cleanup

- [x] Verify backend checks:
  - `cd backend && uv run pytest tests/engine tests/server`
  - `cd backend && uv run ruff check .`
  - `cd backend && uv run ruff format --check .`
- [x] Verify frontend checks:
  - `cd frontend && npm test`
  - `cd frontend && npm run typecheck`
  - `cd frontend && npm run lint`
- [x] Manual smoke test:
  - enter `Designs` mode
  - create one ship design from dummy components
  - confirm new design appears in list and detail view
- [x] Update this task file, marking completed checkboxes as `[x]` and recording any follow-up work

---

## Notes / follow-ups

- Keep component catalogue semantics intentionally minimal in this pass; focus on schema stability and loading reliability.
- If deriving stats from components becomes too heavy for MVP, allow documented placeholder derivation rules as long as API contracts are stable.
- Starbase designer can share UI structure in this pass, but full starbase create behaviour may be completed in a dedicated follow-up task.
- Follow-up: summary list payload currently omits scanner/cargo detail by design; frontend keeps list items as summary objects and only hydrates full detail on demand, with neutral scanner/cargo fallbacks used purely for summary rendering.
- Follow-up: component-catalogue `slot_categories` was removed from both YAML and API schema; slot compatibility is now derived from `component_type` against hull slot categories.
- Follow-up: hull slot identifiers now use numeric `slot_number` (`>=1`) in backend and frontend designer contracts, replacing string `slot_id`.
- Follow-up: component catalogue no longer models `general_purpose` as a component type and no longer exposes `component_count_min/max`; per-slot `component_count` is only constrained by slot capacity for now.
