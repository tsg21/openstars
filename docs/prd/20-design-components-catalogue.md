# PRD 20 — Design Components Catalogue (YAML Source of Truth)

## Overview

This document defines the component catalogue used by the ship/starbase designer.

For the first pass, component definitions are stored as YAML files and loaded by the backend as the canonical source of truth. The catalogue is intentionally minimal but structured enough to support dummy data now and richer balancing data later.

This PRD owns:

- component catalogue file layout
- common component schema
- per-type stat block structures
- loader/validation rules

This PRD does not attempt to finalise balance values yet.

---

## Design goals

- **Single source of truth**: component stats are defined once, in backend-owned YAML files.
- **Human-editable**: files should be easy to read and update during tuning.
- **Strongly validated**: backend validates all YAML at load time before gameplay uses it.
- **Incremental detail**: schema supports placeholder/dummy values now and full data later.
- **Shared across designers**: ship and starbase design read from the same catalogue model.

---

## Scope

### In Scope

- YAML file format for component data
- One YAML file per component type
- Backend-side schema validation rules
- Minimal required fields for MVP designer operation
- Dummy data support for first-pass UI and API integration

### Explicitly Out of Scope

- Final balance numbers
- Complete technology progression and unlock matrix
- Full combat simulation semantics for every component
- Racial modifiers and trait-specific component variants

---

## Ownership and location

The canonical catalogue lives in the backend repository under:

- `backend/openstars/data/components/`

One YAML file per component type:

- `engines.yaml`
- `scanners.yaml`
- `weapons.yaml`
- `shields.yaml`
- `armour.yaml`
- `orbital.yaml`

Notes:

- File names use snake_case and plural form.
- Empty/placeholder files are allowed as long as they are valid YAML with a valid top-level structure.
- File name is the type grouping. There is no top-level `component_type` field.

---

## YAML file structure

Each file uses the same top-level structure:

```yaml
schema_version: 1
components:
  - id: rhino_scanner
    name: Rhino Scanner
    component_type: scanner
    slot_type: scanner
    cost:
      resources: 5
      ironium: 3
      boranium: 0
      germanium: 2
    mass: 3
    max_per_slot: null
    scanner:
      normal: 75
      penetrating: 0
```

### Top-level fields

| Field | Type | Required | Notes |
|------|------|----------|------|
| `schema_version` | integer | yes | Starts at `1`. |
| `components` | list | yes | May be empty for placeholder files. |

### Component common fields

| Field | Type | Required | Notes |
|------|------|----------|------|
| `id` | string | yes | Stable machine identifier, snake_case, globally unique across all component files. |
| `name` | string | yes | Display name. |
| `component_type` | string | yes | Explicit per-item type (e.g. `scanner`, `engine`, `weapon`). Must match file grouping. |
| `slot_type` | string | yes | Single slot type this item is fitted into. |
| `cost.resources` | integer | yes | `>= 0` |
| `cost.ironium` | integer | yes | `>= 0` |
| `cost.boranium` | integer | yes | `>= 0` |
| `cost.germanium` | integer | yes | `>= 0` |
| `mass` | integer | yes | `>= 0` |
| `max_per_slot` | integer \| null | yes | `null` = limited only by slot capacity; integer must be `>= 1`. |

---

## Canonical slot types

`slot_type` may be one of:

- `engine`
- `scanner`
- `weapon`
- `shield`
- `armour`
- `orbital`
- `general_purpose`

These values map to hull-slot compatibility rules from [PRD 19 — Hull Slot Definitions](19-hull-slot-definitions.md).

---

## Type-specific stat blocks (MVP shape)

For MVP, each component entry must include one typed stat block at the root level (not under `attributes`):

### Engines

```yaml
engine:
  max_warp: 8
  is_ramscoop: false
```

### Scanners

```yaml
scanner:
  normal: 75
  penetrating: 0
```

### Weapons

```yaml
weapon:
  range: 1
  damage: 10
  initiative: 6
```

### Shields

```yaml
shield:
  shield_points: 25
```

### Armour

```yaml
armour:
  armour_points: 50
```

### Orbital

```yaml
orbital:
  orbital_type: "stargate"
```

MVP rule: values may be placeholders/dummy values if they pass type validation.

---

## Backend loading and validation

The backend loads all component YAML files at startup (or first access with caching) and validates them before accepting design operations.

Validation rules:

- all required files exist and parse as valid YAML
- `schema_version` is supported
- every component `component_type` matches file grouping
- all `id` values are unique across all files
- `slot_type` values are from the canonical enum
- numeric fields satisfy non-negative and min constraints
- exactly one typed stat block exists and matches `component_type`

Failure behaviour:

- invalid catalogue must fail fast (startup/load error), not silently degrade
- error message should include file and component ID context

---

## API and designer integration

This PRD extends [PRD 18 — Ship Design](18-ship-design.md):

- designer component pickers are populated from this catalogue
- slot legality checks use `slot_type` + hull slot definitions
- derived values are computed from hull + selected component entries
- `component_id` values in design payloads must reference catalogue IDs

---

## Dummy data policy (first pass)

To unblock MVP implementation:

- each component type file may include a small placeholder set (`1-3` components)
- placeholder components should still follow real schema and IDs
- clearly dummy effect values are acceptable

Example placeholder IDs:

- `trans_galactic_drive`
- `rhino_scanner`
- `laser_mk1`
- `moleskin_shield`
- `titanium_armour`

---

## Deferred follow-ups

- Full stat model parity with original Stars! component behaviour
- Electrical/mechanical component modelling (deferred until behaviour model is defined correctly)
- Bomb/mine-layer/robot-miner component modelling (deferred until behaviour model is defined correctly)
- Tech unlock rules and race-trait modifiers
- Localisation-ready display strings
- Component obsolescence/replacement metadata
- Automated docs generation from YAML catalogue
