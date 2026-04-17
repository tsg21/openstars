# Planetary Scanners (PRD 11 + PRD 13)

Implements planetary scanner installations as described in `docs/prd/11-scanners.md` and `docs/prd/13-production.md`: a one-time production queue item that marks a planet as having a scanner installation, contributes to fog-of-war coverage, and is displayed in the planet detail panel.

## Scope

This task covers the Phase 1 planetary scanner model. Planets start with no scanner; the player builds one by adding a `planetary_scanner` item to the production queue. Once built, the installation auto-upgrades for free as tech levels improve — but since tech research is not yet implemented, Phase 1 always uses the Viewer 50 tier (Electronics 0, no penetrating capability).

Out of scope for this task:

- Tech-level-driven tier upgrades (Scoper / Snooper tiers)
- Penetrating scanner coverage (no penetrating scanners in Phase 1)
- Racial scanner traits (AR population scanning, JOAT built-in ship scanners, SD/PP/IS)
- Historical knowledge (last-seen data for out-of-range planets)

---

## Step 1: Extend engine models

Add `has_scanner` to `PlanetState` and the resolved scanner field to `PlayerPlanet`.

- [x] Add `has_scanner: bool = False` to `PlanetState` in [`backend/openstars/engine/models.py`](/Users/tim/code/openstars/backend/openstars/engine/models.py)
- [x] Add `scanner` to `PlayerPlanet` in [`backend/openstars/engine/models.py`](/Users/tim/code/openstars/backend/openstars/engine/models.py):
  - For own planets: `scanner: PlayerPlanetScannerState | None = None` (full tier name + ranges)
  - For scanned enemy planets: `scanner: PlayerPlanetScannerSummary | None = None` (presence boolean only)
  - Add `PlayerPlanetScannerState(installed: bool, name: str, normal: int, penetrating: int)` model
  - Add `PlayerPlanetScannerSummary(installed: bool)` model
- [x] Extend `item_type` Literal to include `"planetary_scanner"` in `ProductionQueueItem`, `PlayerProductionQueueItem`, and `AddProductionItemCommand` in `models.py`
- [x] Add `@model_validator` rule: `quantity` must equal `1` for `planetary_scanner` items
- [x] Add/update backend schema tests covering defaults, serialisation, and the new model shapes
- [x] Run `cd backend && uv run pytest tests/engine tests/server`

---

## Step 2: Add planetary scanner production costs and completion

Extend the production resolution layer with `planetary_scanner` support.

- [x] Add `"planetary_scanner"` cost entry to `ITEM_COSTS` in [`backend/openstars/engine/resolve_steps/production.py`](/Users/tim/code/openstars/backend/openstars/engine/resolve_steps/production.py): `resources=100, ironium=10, boranium=10, germanium=70`
- [x] Extend `get_queue_item_cost` (or equivalent) to handle `planetary_scanner` items
- [x] Add a `resolve_planetary_scanner_tier(electronics: int, bio_tech: int) -> tuple[str, int, int]` helper that returns `(tier_name, normal_range_pc, penetrating_range_pc)` — Phase 1 always returns `("Viewer 50", 50, 0)` since tech levels are not yet implemented; document the hook for future tech integration
- [x] Add completion handling: when a `planetary_scanner` item completes, set `planet.has_scanner = True`
- [x] Add validation in command application: reject `add_production_item` with `item_type="planetary_scanner"` if `planet.has_scanner` is already `True` or if the queue already contains an unfinished `planetary_scanner` item
- [x] Add focused unit tests covering:
  - `planetary_scanner` cost lookup
  - completion sets `has_scanner = True`
  - duplicate scanner rejection (already installed)
  - duplicate queue item rejection
  - `resolve_planetary_scanner_tier` returns correct Phase 1 values
- [x] Run `cd backend && uv run pytest tests/engine/test_production.py`

---

## Step 3: Wire planetary scanner positions into fog-of-war coverage

Teach `fog.py` to include planetary scanner installations when computing scanner coverage, and expose the resolved scanner field on `PlayerPlanet`.

- [x] Update `_scanner_positions` in [`backend/openstars/engine/fog.py`](/Users/tim/code/openstars/backend/openstars/engine/fog.py) to include a `(x, y, normal_range, pen_range)` entry for each owned planet where `has_scanner` is `True`; derive the range using `resolve_planetary_scanner_tier` with Phase 1 tech defaults
- [x] Populate `PlayerPlanet.scanner` in the fog-of-war derivation:
  - Own planet: `PlayerPlanetScannerState(installed=True, name=..., normal=..., penetrating=...)` if `has_scanner` else `None`
  - Enemy planet at `"detailed"` scan level: `PlayerPlanetScannerSummary(installed=has_scanner)` if `has_scanner` else `None`
  - Enemy planet at `"basic"` or `"none"`: `scanner` omitted
- [x] Add/update backend tests covering:
  - planet with scanner contributes to normal coverage
  - scanner range correctly extends fog-of-war for that planet's owner
  - own planet scanner field includes tier name and range
  - enemy planet at detailed scan shows presence only
  - enemy planet at basic/none scan omits scanner field
- [x] Run `cd backend && uv run pytest tests/engine tests/server`

---

## Step 4: Frontend — scanner installation display in planet detail

Show the planetary scanner installation status in the planet detail panel per `docs/prd/62-ui-planet-detail.md`.

- [x] Read [`frontend/AGENTS.md`](/Users/tim/code/openstars/frontend/AGENTS.md) before making any frontend changes
- [x] Add TypeScript types for `PlayerPlanetScannerState` and `PlayerPlanetScannerSummary` alongside the existing planet types
- [x] Add a `ScannerInstallation` sub-component to the planet detail panel that renders:
  - Own planet with scanner: tier name and normal range (and penetrating range if non-zero), e.g. `Scoper 220 (normal 220 pc)`
  - Own planet without scanner: muted `None installed`
  - Enemy planet (detailed scan) with scanner: `Installed`
  - Enemy planet (detailed scan) without scanner: `None`
  - Basic / none scan: omit the scanner row entirely
- [x] Position the scanner row between factory count and mineral display, consistent with the PRD 62 field order
- [x] Add frontend tests for all four rendering branches
- [x] Run `cd frontend && npm test`
- [x] Run `cd frontend && npx tsc --noEmit`
- [x] Run `cd frontend && npm run lint`

---

## Step 5: Frontend — add planetary scanner to production queue UI

Allow the player to queue a `planetary_scanner` item from the owned-planet production panel.

- [x] Add a `Planetary Scanner` option to the "add item" controls in the production queue UI, visible only on own planets where `has_scanner` is `false`
- [x] Hide (or disable) the option once `has_scanner` is `true` or a `planetary_scanner` item is already in the queue
- [x] Send `{ item_type: "planetary_scanner", quantity: 1 }` in the `add_production_item` command payload
- [x] Add frontend tests covering:
  - option visible when scanner not installed and not in queue
  - option absent when already installed
  - option absent when already queued
- [x] Run `cd frontend && npm test`
- [x] Run `cd frontend && npx tsc --noEmit`
- [x] Run `cd frontend && npm run lint`

---

## Step 6: End-to-end verification

- [x] Run `cd backend && uv run pytest`
- [x] Run `cd backend && uv run ruff check .`
- [x] Run `cd backend && uv run ruff format --check .`
- [x] Run `cd frontend && npm test`
- [x] Run `cd frontend && npx tsc --noEmit`
- [x] Run `cd frontend && npm run lint`
- [x] Update this task file with `[x]` for completed work and notes on any deferred gaps

---

## Notes

- Phase 1 tech level is hardcoded to Electronics=0 → Viewer 50 (50 pc normal, no penetrating). The `resolve_planetary_scanner_tier` helper is the single place to update when tech research is added.
- The scanner installation auto-upgrades for free as tech improves — there is no second production item to build; `has_scanner` is set once and never reset.
- Planetary scanner positions use `PARSEC` unit conversion (same as fleet scanners in `fog.py`).
- `quantity` for `planetary_scanner` items is always 1; the server rejects any other value.


### Completion notes

- Manual browser testing was intentionally skipped per repository guidance; verification was done via automated backend/frontend tests, type-checking, and linting.
- Planet detail now places the scanner field directly under resources in the top summary row, and own-planet scanner text shows the tier name without bracketed range details.
