# PRD 51 — Event Codes

## Overview

This document is the canonical registry of all event codes used by the generic event envelope. Every code listed here is part of the API contract and must remain stable.

The generic envelope itself is defined in [PRD 03 — Turn Lifecycle](03-turn-lifecycle.md):

```json
{
  "owner": "tim",
  "source_id": "PLk8m3x2",
  "code": "movement.fleet_arrived",
  "values": ["Scout Alpha", "Proxima"]
}
```

- `owner` — player username that should see the event
- `source_id` — entity ID to anchor UI interactions (usually a planet or fleet ID); `null` when no specific entity applies
- `code` — stable event identifier defined in this document
- `values` — ordered inserts for frontend message templates; types are `string | number`

Human-readable text is frontend-owned and can evolve or be localised without backend changes. `values` are the backend contract.

---

## Movement

### `movement.fleet_arrived`

Emitted when a fleet arrives at a waypoint.

| Field | Value |
|-------|-------|
| `source_id` | destination planet ID, or `null` if the waypoint is a deep-space coordinate |
| `values[0]` | `fleet_name` |
| `values[1]` | `planet_name`, or the string `"deep space"` if no planet is at the destination |

```json
{
  "owner": "tim",
  "source_id": "PLk8m3x2",
  "code": "movement.fleet_arrived",
  "values": ["Scout Alpha", "Proxima"]
}
```

---

## Scanning

### `scanner.planet_scanned`

Emitted when a planet comes into scanner range for the first time this turn (i.e. newly visible after fog of war).

| Field | Value |
|-------|-------|
| `source_id` | planet ID |
| `values[0]` | `planet_name` |

```json
{
  "owner": "tim",
  "source_id": "PLr2j5b8",
  "code": "scanner.planet_scanned",
  "values": ["Sirius II"]
}
```

### `scanner.fleet_detected`

Emitted when an enemy fleet is detected within scanner range.

| Field | Value |
|-------|-------|
| `source_id` | fleet ID |
| `values[0]` | `owner_name` |

```json
{
  "owner": "tim",
  "source_id": "FLa9c3k2",
  "code": "scanner.fleet_detected",
  "values": ["matt"]
}
```

---

## Mining

### `mining.complete`

Emitted per planet per turn when minerals are extracted.

| Field | Value |
|-------|-------|
| `source_id` | planet ID |
| `values[0]` | `planet_name` |
| `values[1]` | `ironium` extracted (kT) |
| `values[2]` | `boranium` extracted (kT) |
| `values[3]` | `germanium` extracted (kT) |

```json
{
  "owner": "tim",
  "source_id": "PLk8m3x2",
  "code": "mining.complete",
  "values": ["Proxima", 10, 8, 6]
}
```

---

## Production

### `production.completed`

Emitted when one or more mine or factory units complete on a planet in a turn.

| Field | Value |
|-------|-------|
| `source_id` | planet ID |
| `values[0]` | `planet_name` |
| `values[1]` | `item_type` — `"mine"` or `"factory"` |
| `values[2]` | `quantity` completed |

```json
{
  "owner": "tim",
  "source_id": "PLk8m3x2",
  "code": "production.completed",
  "values": ["Earth", "factory", 2]
}
```

### `production.ship_built`

Emitted when one or more ships of a design complete on a planet in a turn.

| Field | Value |
|-------|-------|
| `source_id` | planet ID |
| `values[0]` | `planet_name` |
| `values[1]` | `design_name` |
| `values[2]` | `quantity` completed |

```json
{
  "owner": "tim",
  "source_id": "PLk8m3x2",
  "code": "production.ship_built",
  "values": ["Earth", "Scout", 1]
}
```

---

## Population

### `population.colonists_died`

Emitted when colonists die on a planet due to environmental conditions.

| Field | Value |
|-------|-------|
| `source_id` | planet ID |
| `values[0]` | `planet_name` |
| `values[1]` | `deaths` (number of colonists) |
| `values[2]` | `cause` — `"hostile_environment"` |

```json
{
  "owner": "tim",
  "source_id": "PLr2j5b8",
  "code": "population.colonists_died",
  "values": ["Sirius", 50, "hostile_environment"]
}
```

### `population.planet_abandoned`

Emitted when the last colonists on a planet die and the planet becomes unowned.

| Field | Value |
|-------|-------|
| `source_id` | planet ID |
| `values[0]` | `planet_name` |

```json
{
  "owner": "tim",
  "source_id": "PLr2j5b8",
  "code": "population.planet_abandoned",
  "values": ["Sirius"]
}
```

---

## Colonisation

### `colonisation.colonised`

Emitted when a fleet successfully colonises a planet.

| Field | Value |
|-------|-------|
| `source_id` | planet ID |
| `values[0]` | `fleet_name` |
| `values[1]` | `planet_name` |
| `values[2]` | `colonists_landed` |
| `values[3]` | `recovered_ironium` (kT from scrapped colony ship) |
| `values[4]` | `recovered_boranium` (kT) |
| `values[5]` | `recovered_germanium` (kT) |

```json
{
  "owner": "tim",
  "source_id": "PL4fn9v6",
  "code": "colonisation.colonised",
  "values": ["Colony Ship 1", "Proxima II", 2500, 1, 1, 5]
}
```

### `colonisation.failed`

Emitted when a colonisation attempt fails.

| Field | Value |
|-------|-------|
| `source_id` | planet ID, or `null` if no planet exists at the waypoint |
| `values[0]` | `fleet_name` |
| `values[1]` | `planet_name`, or `"Unknown planet"` if `source_id` is `null` |
| `values[2]` | `reason` |

Valid `reason` values are defined in [PRD 16 — Colonisation](16-colonisation.md).

```json
{
  "owner": "tim",
  "source_id": "PL4fn9v6",
  "code": "colonisation.failed",
  "values": ["Colony Ship 1", "Proxima II", "planet_already_owned"]
}
```

---

## Starbases

### `starbase.constructed`

Emitted when a planet completes construction of its first starbase.

| Field | Value |
|-------|-------|
| `source_id` | planet ID |
| `values[0]` | `planet_name` |
| `values[1]` | `starbase_type` |

```json
{
  "owner": "tim",
  "source_id": "PLk8m3x2",
  "code": "starbase.constructed",
  "values": ["Earth", "space_station"]
}
```

### `starbase.upgraded`

Emitted when a planet completes an upgrade to a different starbase type.

| Field | Value |
|-------|-------|
| `source_id` | planet ID |
| `values[0]` | `planet_name` |
| `values[1]` | `old_starbase_type` |
| `values[2]` | `new_starbase_type` |

```json
{
  "owner": "tim",
  "source_id": "PLk8m3x2",
  "code": "starbase.upgraded",
  "values": ["Earth", "orbital_fort", "space_station"]
}
```

---

## Freight

### `freight.loaded`

Emitted when a fleet loads cargo at a planet.

| Field | Value |
|-------|-------|
| `source_id` | planet ID |
| `values[0]` | `fleet_name` |
| `values[1]` | `planet_name` |
| `values[2]` | `ironium` loaded (kT) |
| `values[3]` | `boranium` loaded (kT) |
| `values[4]` | `germanium` loaded (kT) |
| `values[5]` | `colonists` loaded |

```json
{
  "owner": "tim",
  "source_id": "PLk8m3x2",
  "code": "freight.loaded",
  "values": ["Freighter 1", "Earth", 50, 0, 25, 0]
}
```

### `freight.unloaded`

Emitted when a fleet unloads cargo at a planet.

| Field | Value |
|-------|-------|
| `source_id` | planet ID |
| `values[0]` | `fleet_name` |
| `values[1]` | `planet_name` |
| `values[2]` | `ironium` unloaded (kT) |
| `values[3]` | `boranium` unloaded (kT) |
| `values[4]` | `germanium` unloaded (kT) |
| `values[5]` | `colonists` unloaded |

```json
{
  "owner": "tim",
  "source_id": "PL4fn9v6",
  "code": "freight.unloaded",
  "values": ["Freighter 1", "Proxima", 50, 0, 25, 0]
}
```

---

## Combat

### `combat.resolved`

Emitted to each participating owner when a battle is resolved during turn resolution (PRD 80 §Resolution Placement).

| Field | Value |
|-------|-------|
| `source_id` | fleet ID for this recipient's battle anchor; if the owner has multiple participating fleets, use their lexicographically first participating fleet ID from the pre-battle site group |
| `values[0]` | `battle_id` — `BT`-prefixed id used to fetch the combat log |
| `values[1]` | `location_name` — planet name, or `"deep space"` if no planet is at the coordinates |
| `values[2]` | `ships_lost` — number of ships this owner lost in the battle (summed across all their fleets at the site) |

```json
{
  "owner": "tim",
  "source_id": "FLa9c3k2",
  "code": "combat.resolved",
  "values": ["BTq0w2r4", "Earth", 3]
}
```
