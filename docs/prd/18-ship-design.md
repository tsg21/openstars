# PRD 18 — Ship Design

## Overview

This document defines the first ship design system for OpenStars!, staying faithful to classic Stars! gameplay while presenting it through a more modern UI.

The player flow is:

1. Select a hull
2. Drag components into hull slots
3. Enter a design name
4. Save the design

Ship design creation is explicitly **outside the turn command lifecycle**. Creating a design is handled by a dedicated API endpoint, not by turn commands, and does not require turn resolution.

---

## Design Goals

- **Mechanically faithful**: preserve the original Stars! design model of hull + slot-based components.
- **Modern interaction model**: use direct manipulation (drag/drop) instead of the original dense Windows-era widgeting.
- **Server authoritative**: backend validates legality and computes derived stats/costs.
- **Immutable designs**: once saved, a design cannot be edited in place.
- **Turn-lifecycle separation**: creating designs is independent from `POST /commands` and `POST /resolve`.

---

## Scope

### In Scope

- Ship designer UX flow for selecting hull, fitting components, naming, and saving
- Slot-compatibility validation rules (client pre-check + authoritative server validation)
- Dedicated endpoint for creating a new design
- Persistent design storage outside turn commands/resolution
- Design immutability after creation
- Returning player-owned designs via API for production and fleet composition displays

### Explicitly Out of Scope

- Editing an existing design
- Deleting or retiring designs
- Auto-upgrading fleets from one design to another
- Battle simulator integration in the designer
- Full tech-tree/race-trait unlock rules (beyond reserving API/schema hooks)

---

## Player Experience

### Designer Screen Structure

The screen should keep the original mental model, with modern presentation:

- **Hull panel**: hull list and hull summary stats
- **Design canvas**: selected hull silhouette with explicit slots
- **Component palette**: grouped components available for fitting
- **Design summary panel**: name input, derived stats, mineral/resource cost, save action

### Interaction Flow

1. **Select hull**
   - Player chooses one hull from allowed hulls.
   - Empty slot layout is shown immediately.
2. **Fit components**
   - Player drags a component from palette to a compatible slot.
   - Incompatible slots reject the drop and show feedback.
   - Player may remove a fitted component by dragging it out of the slot.
3. **Name design**
   - Player enters a display name.
4. **Save**
   - Save is enabled only when the design is valid.
   - On save, UI calls the add-design endpoint.
   - On success, new design appears in the player's design list and is immediately available for production queue use.

### Validation UX

The UI should show clear reasons a design cannot be saved, for example:

- required slot not filled
- incompatible component for slot
- unknown hull/component
- invalid design name

The backend remains authoritative. Client validation is a usability aid only.

---

## Core Rules

### Hull + Slot Model

- Each hull defines a fixed set of slots.
- Each slot accepts only a constrained set of component categories or items.
- A design is legal only if all required slots are validly filled.

### Derived Values

The server computes and stores derived values at design creation time, including:

- production cost (`resources`, `ironium`, `boranium`, `germanium`)
- `speed`
- cargo capacity
- scanner ranges (normal and penetrating, where applicable)

These are computed once and stored on the immutable design so downstream systems (production, movement, scanning) can consume stable values.

### Immutability

After creation:

- design fields cannot be mutated
- component loadout cannot be mutated
- derived values cannot be mutated

To make a variant, the player creates a new design.

Deletion and retirement semantics are deferred to a later PRD.

---

## Turn Lifecycle Separation

This PRD extends [PRD 03 — Turn Lifecycle](03-turn-lifecycle.md) and [PRD 13 — Production](13-production.md):

- design creation is **not** a turn command
- design creation does **not** require turn resolution
- design creation does **not** increment the turn

Designs must be persisted in a store that is independent from command submissions so they can be added at any time during a turn.

### Resolution Contract Update

To preserve deterministic resolution while allowing out-of-turn design creation, turn resolution should read a stable snapshot of current designs at resolve start.

Conceptually:

`resolve(previous_global_state, design_registry_snapshot, all_orders) -> new_global_state`

This keeps design creation outside command editing while preserving deterministic turn processing.

---

## API Contract

This PRD extends [PRD 50 — API](50-api.md).

### `POST /api/v1/games/{game_id}/designs`

Create a new immutable ship design for the authenticated player.

#### Request headers

- `X-Player: {username}`

#### Request body

```json
{
  "name": "Long Range Scout",
  "hull": "scout",
  "components": [
    { "slot_id": "engine_1", "component_id": "trans_galactic_drive" },
    { "slot_id": "scanner_1", "component_id": "rhino_scanner" }
  ]
}
```

#### Response: `201 Created`

```json
{
  "design": {
    "id": "DE9ab12c",
    "owner": "tim",
    "name": "Long Range Scout",
    "hull": "scout",
    "components": [
      { "slot_id": "engine_1", "component_id": "trans_galactic_drive" },
      { "slot_id": "scanner_1", "component_id": "rhino_scanner" }
    ],
    "cost": {
      "resources": 28,
      "ironium": 12,
      "boranium": 0,
      "germanium": 4
    },
    "speed": 8,
    "cargo_capacity": 0,
    "scanner_normal": 220,
    "scanner_penetrating": 0
  }
}
```

#### Validation rules

Server rejects the request if:

- player is not a participant in the game
- hull is unknown or unavailable to that player
- any slot assignment references an unknown slot
- any component is invalid for that slot
- required slots are missing
- name is invalid (empty/too long/invalid characters)

#### Errors

| Status | Condition |
|--------|-----------|
| `400` | Invalid payload or illegal design fit |
| `403` | Player is not a participant in this game |
| `404` | Game not found |

### `GET /api/v1/games/{game_id}/designs`

Remains the read endpoint for player-owned designs (introduced in PRD 13), but now returns full immutable design payloads including fitted components and derived values.

---

## Data Model

`ShipDesign` is extended to represent an immutable fitted design:

```python
class ShipDesignCost(BaseModel):
    resources: int
    ironium: int = 0
    boranium: int = 0
    germanium: int = 0

class ShipDesignComponent(BaseModel):
    slot_id: str
    component_id: str

class ShipDesign(BaseModel):
    id: str
    owner: str
    name: str
    hull: str
    components: list[ShipDesignComponent]
    cost: ShipDesignCost
    speed: int
    cargo_capacity: int
    scanner_normal: int = 0
    scanner_penetrating: int = 0
```

### Notes

- `id` remains `DE`-prefixed (PRD 04 conventions).
- `components` preserves slot-level fitting detail for UI and audits.
- Derived fields avoid recomputing from catalog tables during production/movement/scanning.

---

## Integration Notes

### Production (PRD 13)

- `add_production_item` with `item_type = "ship"` continues to reference `design_id`.
- Newly created designs are available for production in the same turn.
- Since designs are immutable, production cost remains stable and safe to read from the design.

### Movement and Scanning

- Fleet speed and scanner behaviour continue to be based on design-derived fields.
- No movement/scanner formula changes are introduced by this PRD; only authoring of design data changes.

---

## Deferred Follow-Ups

- Design deletion endpoint and rules
- Design retirement/obsolescence flags
- Starbase design editor parity
- Full tech prerequisite and race-trait unlock rules
- Save/load draft designs before final creation

