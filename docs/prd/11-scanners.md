# PRD 11 — Scanners & Fog of War

## Overview

Scanners are the primary information-gathering mechanic in Stars!. Every player sees only what their scanners reveal — the rest of the galaxy is hidden. This PRD defines the scanner model, visibility rules, and how scanner data flows into the player state (PRD 03).

The scanner system has two key properties:
1. **Information is always incomplete** — you never see the full map unless you scan it all
2. **Information decays** — planets and fleets you scanned last turn may have changed since

## Scanner Types

Stars! has two distinct scanner types with different capabilities and ranges:

### Normal Scanners (Non-Penetrating)

Detect the **presence** of objects within range:
- **Planets:** name, position, owner (if colonised). No mineral or population detail.
- **Fleets:** owner, position, bearing (direction of travel). No composition, cargo, or waypoint detail.
- **Minefields:** presence, owner, approximate size (future phase).

Normal scanners are the baseline. Every scanner component provides at least normal scanning.

### Penetrating Scanners

See **through** planetary defences and provide detailed intel:
- **Planets:** everything normal scanners see, plus: population, mineral concentrations, surface minerals, factories, mines, defences, habitability values, starbase presence.
- **Fleets:** no additional benefit over normal scanners. Penetrating scanning only applies to planets.

Penetrating scanner range is always **shorter** than normal scanner range for the same component. A typical ratio is roughly 1:2 to 1:3 (penetrating : normal).

### Range Hierarchy

Every scanner-equipped ship has two ranges:
- `scanner_range` — normal (non-penetrating) range in parsecs
- `pen_scanner_range` — penetrating range in parsecs (0 if no penetrating capability)

A planet at distance D from a scanner is:
- **Not visible** if `D > scanner_range`
- **Visible (basic)** if `pen_scanner_range < D ≤ scanner_range`
- **Visible (detailed)** if `D ≤ pen_scanner_range`

## Scanner Sources

Scanners operate from multiple sources, all contributing to a player's aggregate visibility:

### Fleet Scanners
Every ship design can include scanner components. A fleet's effective scanner range is the **maximum** scanner range of any ship design in its composition (not cumulative — the best scanner wins).

### Planetary Scanners
Colonised planets have an innate scanner based on population. In the original Stars!, every planet scans at a base range that increases with population. Planets with starbases may have additional scanner components.

**Phase 1 implementation:** planets do not scan. Only fleets provide scanner coverage. Planetary scanners will be added with the economy/starbase phase.

### Orbital Scanners (Future)
Starbases can mount scanner components, typically with much larger ranges than ship-mounted scanners.

## Visibility Rules

### Own Assets — Always Visible
- Own planets: full detail, always
- Own fleets: full detail (composition, waypoints, cargo), always
- Own designs: always visible

### Planets
| Condition | Visible? | Detail Level |
|-----------|----------|--------------|
| Own planet | Yes | Full (population, minerals, factories, mines, defences, hab values) |
| Within penetrating range | Yes | Full (same as own, minus production queue) |
| Within normal range | Yes | Basic (name, position, owner, population if colonised) |
| Outside all scanner range | No | Not in player state |

### Fleets
| Condition | Visible? | Detail Level |
|-----------|----------|--------------|
| Own fleet | Yes | Full (composition, waypoints, cargo, fuel) |
| Within normal range | Yes | Limited (owner, position, bearing — no composition, waypoints, or cargo) |
| Outside all scanner range | No | Not in player state |

Penetrating scanners do **not** provide extra fleet detail — only normal scanning applies to fleets.

### Bearing
When an enemy fleet is detected by normal scanners, the player sees its **bearing** — the direction of travel based on the fleet's first waypoint (if it has one). If the fleet is stationary, no bearing is shown.

This is represented as an angle or as a delta direction. It gives the observing player a hint about where the enemy is heading without revealing exact waypoints.

## Scanner Range by Tech Level

Scanner components improve with Electronics tech level. Example progression (values in parsecs, subject to balancing):

| Component | Tech Level | Normal Range (pc) | Penetrating Range (pc) |
|-----------|------------|-------------------|----------------------|
| Bat Scanner | 0 | 50 | 0 |
| Rhino Scanner | 1 | 75 | 0 |
| Mole Scanner | 4 | 100 | 40 |
| DNA Scanner | 7 | 125 | 50 |
| Possum Scanner | 5 | 150 | 75 |
| Pick Pocket Scanner | 8 | 80 | 80 |
| Chameleon Scanner | 10 | 200 | 100 |
| Ferret Scanner | 12 | 185 | 185 |
| Elephant Scanner | 14 | 300 | 150 |
| Eagle Eye Scanner | 16 | 400 | 200 |
| Robber Baron Scanner | 18 | 220 | 220 |

*Note: these names and values reference the original Stars! scanner components. Exact values will be confirmed during balancing. Some scanners prioritise penetrating range over normal range — this is a deliberate design choice from the original.*

### Phase 1 Defaults

Phase 1 uses a single pre-built scout design with:
- `scanner_range: 150` (parsecs)
- `pen_scanner_range: 0` (no penetrating scanning)

Penetrating scanning will be implemented alongside the planet economy (when there's something to penetrate).

## Schema Changes

### Design (PRD 05)

Add `pen_scanner_range` to the design model:

```json
{
  "id": "DEa3f0p5",
  "owner": "tim",
  "name": "Long Range Scout",
  "hull": "scout",
  "speed": 6,
  "scanner_range": 150,
  "pen_scanner_range": 0
}
```

| Field | Type | Description |
|-------|------|-------------|
| `scanner_range` | integer | Normal (non-penetrating) scanner range in parsecs. 0 = no scanner. |
| `pen_scanner_range` | integer | Penetrating scanner range in parsecs. 0 = no penetrating capability. Always ≤ `scanner_range`. |

### Player State — Planet Detail Levels

The player state (PRD 03/09) currently returns the same fields for all visible planets. With two scanner tiers, the response needs to distinguish between basic and detailed scans.

**Basic scan** (normal scanner range):
```json
{
  "id": "PL4fn9v6",
  "name": "Alpha Centauri",
  "x": 550148141952,
  "y": 549755867136,
  "owner": null,
  "scan_level": "basic"
}
```

**Detailed scan** (penetrating scanner range or own planet):
```json
{
  "id": "PL4fn9v6",
  "name": "Alpha Centauri",
  "x": 550148141952,
  "y": 549755867136,
  "owner": "matt",
  "population": 45000,
  "minerals": { "ironium": 50, "boranium": 30, "germanium": 80 },
  "mineral_concentrations": { "ironium": 90, "boranium": 45, "germanium": 120 },
  "factories": 100,
  "mines": 50,
  "defences": 10,
  "scan_level": "detailed"
}
```

The `scan_level` field tells the frontend whether to render the full planet report or just the basic overlay.

**Phase 1:** `scan_level` is always `"basic"` for non-own planets (no penetrating scanners, no economy fields yet). Own planets show `"detailed"` but with only the fields that exist in Phase 1 (owner, population).

### Player State — Fleet Bearing

Add optional `bearing` to enemy fleet entries:

```json
{
  "id": "FLp4h8e2",
  "owner": "matt",
  "position": { "x": 552952127488, "y": 551903297536 },
  "bearing": 135.0
}
```

| Field | Type | Description |
|-------|------|-------------|
| `bearing` | float/null | Direction of travel in degrees (0 = north/up, clockwise). `null` if the fleet is stationary. |

Bearing is computed from the fleet's position toward its first waypoint. This is derived during fog-of-war filtering — the server calculates it from the global state but never reveals the actual waypoint coordinates.

## Aggregate Scanner Coverage

A player's total scanner coverage is the **union** of all their scanner circles (fleet scanners + planetary scanners when implemented).

There is no stacking or range bonus from multiple overlapping scanners — if any single scanner can see a position, it's visible. The best applicable scan level wins (penetrating > normal).

### Algorithm

```
For each object (planet/fleet) in the game:
  1. Check if within pen_scanner_range of any player scanner → detailed
  2. Else check if within scanner_range of any player scanner → basic
  3. Else → not visible
```

For performance, the fog-of-war derivation can use squared distances to avoid square roots (compare `dist² ≤ range²`).

## Historical Knowledge (Future)

In the original Stars!, planets you've previously scanned retain their last-known data even after they leave scanner range. The UI shows this stale data with an indicator (e.g. "last scanned turn 5").

This is **out of scope** for the initial implementation. Currently, planets outside scanner range are simply absent from the player state. Historical knowledge tracking will be added as a future enhancement — likely a per-player history store that records the last scan of each planet.

## Racial Scanner Traits (Future)

Several Stars! primary racial traits modify scanner behaviour:

- **Jack of All Trades (JOAT):** planets get built-in penetrating scanners
- **Inner Strength (IS):** no special scanner effect, but population grows in fleets
- **Space Demolition (SD):** minefields act as scanners
- **Packet Physics (PP):** mineral packets have scanners

These are out of scope until race design is implemented.

## Relationship to Other PRDs

- **PRD 03** — Player state derivation (fog of war is a step in the turn lifecycle)
- **PRD 05** — Design schema (scanner_range, pen_scanner_range fields)
- **PRD 07** — Resolution pipeline (scanners evaluate after movement)
- **PRD 09** — API response format for player state
- **PRD 10** — Fleet movement (scanners determine visibility of movement results)
