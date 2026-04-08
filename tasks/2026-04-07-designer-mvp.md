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

- [ ] Add backend models for component catalogue documents and entries (shared/common fields + per-type effect blocks)
- [ ] Add loader that reads `backend/openstars/data/components/*.yaml` and validates all files at load
- [ ] Add deterministic error reporting for invalid YAML/schema (file + entry context)
- [ ] Add unit tests for:
  - successful load of valid YAML
  - missing required top-level fields
  - invalid enum values (`component_type`, `slot_categories`)
  - invalid numeric constraints (`component_count_min/max`, negative costs)
- [ ] Run `cd backend && uv run pytest tests/engine`

---

## Step 2: Add dummy component YAML files (one per type)

- [ ] Create `backend/openstars/data/components/` with one YAML file per type:
  - `engines.yaml`
  - `scanners.yaml`
  - `weapons.yaml`
  - `shields.yaml`
  - `armour.yaml`
  - `general_purpose.yaml`
  - `bombs.yaml`
  - `mine_layers.yaml`
  - `robot_miners.yaml`
  - `orbitals.yaml`
- [ ] Populate each file with minimal dummy entries sufficient to exercise slot assignment and derived stat calculations
- [ ] Add backend tests ensuring all expected files exist and parse as valid catalogue docs
- [ ] Run `cd backend && uv run pytest tests/engine`

---

## Step 3: Add hull-definition read model for designer (backend)

- [ ] Add backend-owned hull-definition read model derived from `PRD 19` slot definitions (ship hulls first)
- [ ] Expose allowed slot categories, per-slot capacity, and engine requirements in a machine-readable form
- [ ] Add unit tests for hull-definition integrity:
  - unique `slot_id` per hull
  - valid slot category enum mapping
  - required engine slots correctly marked
- [ ] Run `cd backend && uv run pytest tests/engine`

---

## Step 4: Add first-pass designer APIs (backend)

- [ ] Add API endpoint(s) to fetch designer reference data for the selected domain (`ship` initially):
  - hull definitions
  - component catalogue entries
- [ ] Keep design list/detail/create endpoints aligned with PRD 18 (`GET summary`, `GET detail`, `POST create`)
- [ ] Validate create payload against hull slot rules + component catalogue rules:
  - slot compatibility
  - required slots present
  - `component_count` bounds
- [ ] Compute derived stats and cost from selected components (MVP formulas/placeholders as documented in code)
- [ ] Add server tests for:
  - successful reference-data fetch
  - create validation failures
  - successful design creation with dummy components
  - summary/detail response shapes
- [ ] Run `cd backend && uv run pytest tests/server tests/engine`

---

## Step 5: Implement `Designs` mode shell in frontend

- [ ] Add top-level mode switch so `Designs` replaces Command View workspace
- [ ] Add Designs landing view:
  - list existing designs
  - select design for read-only inspect
  - `Create New` action
- [ ] Ensure `Create New` flow begins with hull selection
- [ ] Add frontend tests for mode switch and landing flow
- [ ] Run `cd frontend && npm test`
- [ ] Run `cd frontend && npm run typecheck`

---

## Step 6: Implement basic form-driven designer UI (frontend MVP)

- [ ] Build first-pass slot-list designer UI:
  - slot rows/table
  - per-slot component select box
  - `component_count` control
  - name input + save button
- [ ] Surface validation feedback from backend and client pre-checks
- [ ] Show derived stats and cost summary from backend response model
- [ ] Submit create request and return to design list on success
- [ ] Add frontend tests for:
  - slot assignment interactions
  - save enable/disable states
  - successful create flow
  - representative validation error rendering
- [ ] Run `cd frontend && npm test`
- [ ] Run `cd frontend && npm run typecheck`
- [ ] Run `cd frontend && npm run lint`

---

## Step 7: End-to-end verification and cleanup

- [ ] Verify backend checks:
  - `cd backend && uv run pytest tests/engine tests/server`
  - `cd backend && uv run ruff check .`
  - `cd backend && uv run ruff format --check .`
- [ ] Verify frontend checks:
  - `cd frontend && npm test`
  - `cd frontend && npm run typecheck`
  - `cd frontend && npm run lint`
- [ ] Manual smoke test:
  - enter `Designs` mode
  - create one ship design from dummy components
  - confirm new design appears in list and detail view
- [ ] Update this task file, marking completed checkboxes as `[x]` and recording any follow-up work

---

## Notes / follow-ups

- Keep component catalogue semantics intentionally minimal in this pass; focus on schema stability and loading reliability.
- If deriving stats from components becomes too heavy for MVP, allow documented placeholder derivation rules as long as API contracts are stable.
- Starbase designer can share UI structure in this pass, but full starbase create behaviour may be completed in a dedicated follow-up task.
