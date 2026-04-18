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

Normal scanners are the baseline. Every scanner component provides at least normal scanning.

### Penetrating Scanners

See **through** planetary defences and provide detailed intel:
- **Planets:** everything normal scanners see, plus: population, mineral concentrations, surface minerals, factories, mines, defences, habitability values, starbase presence.
- **Fleets:** no additional benefit over normal scanners. Penetrating scanning only applies to planets and minefields.
- **Minefields:** within penetrating range, the player sees the minefield's owner, position, and approximate radius.

Penetrating scanner range is always **shorter** than normal scanner range for the same component. A typical ratio is roughly 1:2 to 1:3 (penetrating : normal).

### Range Hierarchy

Every scanner-equipped ship design has two attributes:
- `scanner.normal` — normal (non-penetrating) range in parsecs
- `scanner.penetrating` — penetrating range in parsecs (0 if no penetrating capability)

## Scanner Sources

Scanners operate from multiple sources, all contributing to a player's aggregate visibility:

### Fleet Scanners
Every ship design can include scanner components. A fleet's effective scanner range is the **maximum** scanner range of any ship design in its composition (not cumulative — the best scanner wins).

### Planetary Scanners

Colonised planets can have a **planetary scanner installation** — a surface-based scanner built through the production queue (see PRD 13). One installation per planet; it is built once and then **automatically upgrades** as the owning player's Electronics (and Bio-Tech) research advances.

Planetary scanner installations fall into two families:

- **Viewers / Scopers** — normal (non-penetrating) scanners only
- **Snoopers (X-series)** — penetrating scanners; require both Electronics and Bio-Tech research to unlock

Scanner range by installation type (from appendix B-10 of the original Stars! manual; the `Ability` column is the range in parsecs):

| Name | Electronics | Bio-Tech | Normal Range (pc) | Penetrating Range (pc) |
|------|-------------|----------|-------------------|------------------------|
| Viewer 50 | 0 | 0 | 50 | 0 |
| Viewer 90 | 1 | 0 | 90 | 0 |
| Scoper 150 | 3 | 0 | 150 | 0 |
| Scoper 220 | 6 | 0 | 220 | 0 |
| Scoper 280 | 8 | 0 | 280 | 0 |
| Snooper 320X | 10 | 3 | 320 | 160 |
| Snooper 400X | 13 | 6 | 400 | 200 |
| Snooper 500X | 16 | 7 | 500 | 250 |
| Snooper 620X | 23 | 9 | 620 | 310 |

*Penetrating ranges for Snoopers are half the normal range, following the Stars! strategy guide convention.*

A planet without a scanner installation provides no scanner coverage. Uncolonised planets never have scanners.

**Current implementation:** planets contribute to scanner coverage once a planetary scanner is built through the production queue. Until one is built, only fleets provide scanner coverage for that location.

## Visibility Rules

### Own Assets — Always Visible
- Own planets: full detail, always
- Own fleets: full detail (composition, waypoints, cargo), always
- Own minefields: always visible
- Own designs: always visible

### Planets

All planets are **always visible** on the galaxy map — their name and position are known to every player from the start of the game. What changes with scanner coverage is how much you know about them:

| Condition | Detail Level |
|-----------|--------------|
| Own planet | Full (population, minerals, factories, mines, defences, hab values) |
| Within penetrating range | Detailed (same as own, minus production queue; scanner shows `installed` boolean only — no tier name or range) |
| Within normal range | Basic (owner, population if colonised) |
| Outside range, previously scanned | Stale — last-known data with `scan_age` indicator (retains original `scan_level`) |
| Outside range, never scanned | Position and name only — no owner, population, or other data |

### Fleets
| Condition | Visible? | Detail Level |
|-----------|----------|--------------|
| Own fleet | Yes | Full (composition, waypoints, cargo, fuel) |
| Within normal range | Yes | Limited (owner, position, bearing — no composition, waypoints, or cargo) |
| Outside all scanner range | No | Not in player state |

Penetrating scanners do **not** provide extra fleet detail — only normal scanning applies to fleets.

### Minefields
| Condition | Visible? | Detail Level |
|-----------|----------|--------------|
| Own minefield | Yes | Full (position, radius, type) |
| Within penetrating range | Yes | Limited (owner, position, approximate radius) |
| Within normal range only | No | Invisible — normal scanners cannot detect minefields |
| Outside all scanner range | No | Not in player state |

Minefields are a hidden threat — fleets can blunder into them without warning unless the player has penetrating scanner coverage of the area. This makes penetrating scanners strategically critical for safe fleet movement.

### Bearing
When an enemy fleet is detected by normal scanners, the player sees its **bearing** — the direction of travel based on the fleet's first waypoint (if it has one). If the fleet is stationary, no bearing is shown.

This is represented as an angle or as a delta direction. It gives the observing player a hint about where the enemy is heading without revealing exact waypoints.

## Ship Scanner Range by Tech Level

Ship scanner components improve with Electronics (and occasionally other) tech levels. Values from appendix B-11 of the original Stars! manual, with penetrating ranges from the companion reference table in the same document:

| Component | Electronics | Other | Normal Range (pc) | Penetrating Range (pc) |
|-----------|-------------|-------|-------------------|------------------------|
| Bat Scanner | 0 | — | 0 | 0 |
| Rhino Scanner | 1 | — | 50 | 0 |
| Mole Scanner | 4 | — | 100 | 0 |
| DNA Scanner | 0 | Propulsion 3, Bio 6 | 125 | 0 |
| Possum Scanner | 5 | — | 150 | 0 |
| Pick Pocket Scanner | 4 | Energy 4, Bio 4 | 80 | 0 |
| Chameleon Scanner | 6 | Energy 3 | 160 | 45 |
| Ferret Scanner | 7 | Energy 3, Bio 2 | 185 | 50 |
| Dolphin Scanner | 10 | Energy 5, Bio 4 | 220 | 100 |
| Gazelle Scanner | 8 | Energy 4 | 225 | 0 |
| Elephant Scanner | 16 | Energy 6, Bio 7 | 300 | 200 |
| Eagle Eye Scanner | 14 | Energy 6 | 335 | 0 |
| Robber Baron Scanner | 15 | Energy 10, Bio 10 | 220 | 120 |
| Peerless Scanner | 24 | Energy 7 | 500 | 0 |

*Note: the Bat Scanner (tech 0) has no long-range fleet detection capability — it provides orbit-only planet scanning per the original manual. All other values are from the appendix B-11 table and companion penetrating-range reference.*

### Phase 1 Defaults

Phase 1 uses a single pre-built scout design with:
- `scanner.normal`: 150 (parsecs)
- `scanner.penetrating`: 0 (no penetrating scanning)

Penetrating scanning becomes available once Snooper-class planetary scanner installations are built (requires Electronics 10+ and Bio-Tech 3+).

## Schema Changes

### Global State — `PlanetState`

Add one field to track whether a planetary scanner installation has been built:

```python
class PlanetState(BaseModel):
    # ... existing fields ...
    has_scanner: bool = False    # NEW — true once a planetary_scanner production item completes
```

This field is internal engine state. The active scanner tier (Viewer 50, Scoper 150, etc.) is derived at runtime from `has_scanner` plus the planet owner's current Electronics and Bio-Tech levels — it is not stored separately.

### Design (PRD 05)

Add `scanner` to the design model:

```json
{
  "id": "DEa3f0p5",
  "owner": "tim",
  "name": "Long Range Scout",
  "hull": "scout",
  "speed": 6,
  "scanner": {
    "normal" : 150,
    "penetrating" : 0
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `scanner.normal` | integer | Normal (non-penetrating) scanner range in parsecs. 0 = no scanner. |
| `scanner.penetrating` | integer | Penetrating scanner range in parsecs. 0 = no penetrating capability. Always ≤ `scanner.normal`. |

### Player State — Planet Detail Levels

The player state (PRD 03/09) currently returns the same fields for all visible planets. With three visibility tiers, the response needs to distinguish between them.

Since all planets are always visible, every planet in the galaxy appears in the player state — but with varying levels of detail.

**Unseen** (outside all scanner range):
```json
{
  "id": "PL4fn9v6",
  "name": "Alpha Centauri",
  "x": 550148141952,
  "y": 549755867136,
  "scan_level": "none"
}
```

**Basic scan** (normal scanner range):
```json
{
  "id": "PL4fn9v6",
  "name": "Alpha Centauri",
  "x": 550148141952,
  "y": 549755867136,
  "owner": "matt",
  "scan_level": "basic"
}
```

**Detailed scan** (own planet):
```json
{
  "id": "PL4fn9v6",
  "name": "Alpha Centauri",
  "x": 550148141952,
  "y": 549755867136,
  "owner": "tim",
  "population": 45000,
  "minerals": { "ironium": 50, "boranium": 30, "germanium": 80 },
  "mineral_concentrations": { "ironium": 90, "boranium": 45, "germanium": 120 },
  "factories": 100,
  "mines": 50,
  "defences": 10,
  "scanner": { "installed": true, "name": "Scoper 220", "normal": 220, "penetrating": 0 },
  "scan_level": "detailed"
}
```

**Detailed scan** (enemy planet, within penetrating scanner range):
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
  "scanner": { "installed": true },
  "scan_level": "detailed"
}
```

For own planets, `scanner` includes the resolved tier name and range values derived from `has_scanner` + current Electronics/Bio-Tech levels. For enemy planets at penetrating scan, only the presence boolean is returned — the server omits tier name and range values. `scanner` is `null` (or omitted) when `has_scanner` is false.

The `scan_level` field tells the frontend what to render:
- `"none"` — just a dot on the map with a name; never scanned
- `"basic"` — show owner colour, population count
- `"detailed"` — full planet report panel


Staleness is orthogonal to scan level: a planet retains its original `scan_level` (`"basic"` or `"detailed"`) when it leaves scanner range. The `scan_age` field (default 0) indicates how many turns ago the data was captured. `scan_age > 0` means the data is stale.

**Phase 1:** `scan_level` is `"none"` or `"basic"` for non-own planets (no penetrating scanners, no economy fields yet). Own planets show `"detailed"` but with only the fields that exist in Phase 1 (owner, population).

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

A player's total scanner coverage is the **union** of all their scanner circles (fleet scanners + planetary scanner installations).

There is no stacking or range bonus from multiple overlapping scanners — if any single scanner can see a position, it's visible. The best applicable scan level wins (penetrating > normal).

### Algorithm

Player scanners are all fleet scanners plus any planetary scanner installations on owned planets. Each contributes its `normal` and `penetrating` ranges centred on its location.

```
For each planet in the galaxy:
  1. Check if within pen_scanner_range of any player scanner → detailed
  2. Else check if within scanner_range of any player scanner → basic
  3. Else look up planet in previous player state (T{N-1}):
       if previous scan_level is basic or detailed → carry forward with scan_age incremented by 1
       else → none (position and name only)

For each fleet/minefield in the game:
  1. Check if own → full detail
  2. Check if within pen_scanner_range (minefields) or scanner_range (fleets) → visible
  3. Else → not in player state
```

For performance, the fog-of-war derivation can use squared distances to avoid square roots (compare `dist² ≤ range²`).

## Historical Knowledge

In the original Stars!, planets you've previously scanned retain their last-known data even after they leave scanner range. The UI shows this stale data with an indicator ("Last scanned: Turn N").

### Stale Planet Data

When a planet is outside all scanner range but has been previously scanned, it retains its original `scan_level` (`"basic"` or `"detailed"`) with `scan_age` incremented each turn it remains out of range. `scan_age` is 0 for fresh data and increases by 1 each turn the planet stays outside scanner range.

Stale data represents the state of the planet at the last moment it was in range. It does not update until the planet re-enters scanner range, at which point `scan_age` resets to 0.

### History Source: Previous Player State

No separate history store is maintained. Instead, stale planet data is sourced directly from the **previous player state file** (`player-state-P{id}-T{N-1}.json`) when deriving the current turn's player state.

The previous player state already contains the exact view the player had last turn — including any planets that were in range at that time, at whatever detail level was achieved. Using it directly means stale data is always a faithful copy of what the player last saw, with no duplication in global state.

### Derivation Rules

When deriving `player-state-P{id}-T{N}`:

1. Compute current scanner coverage from global state T{N} (same as before).
2. For each planet in the galaxy:
   - If within current scanner range → resolve to `"basic"` or `"detailed"` as normal (fresh data, `scan_age: 0`).
   - If **not** within current scanner range → look up the planet in `player-state-P{id}-T{N-1}`:
     - If the previous state has an entry with `scan_level` of `"basic"` or `"detailed"` → carry it forward with the same `scan_level`, incrementing `scan_age` by 1.
     - If the previous state has no entry, or has `scan_level: "none"` → include as `scan_level: "none"`.
3. For Turn 0 (no previous state exists), all out-of-range planets are `scan_level: "none"`.

Stale data chains automatically: a planet with `scan_age: 1` in T{N-1} becomes `scan_age: 2` in T{N} unless re-scanned. When re-scanned, `scan_age` resets to 0.

Own planets are always `scan_level: "detailed"` with `scan_age: 0` in the current state. If a player loses a planet to an enemy, the most recent own-planet detail entry is retained in subsequent player states as stale (with incrementing `scan_age`) until the planet re-enters scanner range.

### Player State Schema for Stale Planets

After a basic scan, 3 turns stale:

```json
{
  "id": "PL4fn9v6",
  "name": "Alpha Centauri",
  "x": 550148141952,
  "y": 549755867136,
  "scan_level": "basic",
  "scan_age": 3,
  "owner": "matt"
}
```

After a detailed scan, 2 turns stale:

```json
{
  "id": "PL4fn9v6",
  "name": "Alpha Centauri",
  "x": 550148141952,
  "y": 549755867136,
  "scan_level": "detailed",
  "scan_age": 2,
  "owner": "sara",
  "population": 45000,
  "minerals": { "ironium": 50, "boranium": 30, "germanium": 80 },
  "mineral_concentrations": { "ironium": 90, "boranium": 45, "germanium": 120 },
  "factories": 100,
  "mines": 50,
  "defences": 10
}
```

The depth of detail (which fields are present) reflects what was last observed — `scan_age > 0` tells the UI to present all data as potentially outdated.

## Racial Scanner Traits (Future)

Several Stars! primary racial traits modify scanner behaviour:

- **Jack of All Trades (JOAT):** Scout, Frigate, and Destroyer hulls get a built-in ship scanner with normal/penetrating range of `2x / x` parsecs, where `x = 10 × Electronics tech level`.
- **Alternate Reality (AR):** cannot build planetary scanner installations; instead, population acts as a natural scanner (equivalent capability provided by the race's biology rather than technology).
- **Space Demolition (SD):** minefields act as non-penetrating scanners.
- **Packet Physics (PP):** mineral packets have built-in penetrating scanners with range equal to the square of their warp speed.
- **Inner Strength (IS):** the Tachyon Detector component (reduces enemy cloak effectiveness) is exclusive to this trait — not a scanner range modifier but affects detection of cloaked fleets.

These are out of scope until race design is implemented.

## Relationship to Other PRDs

- **PRD 03** — Player state derivation (fog of war is a step in the turn lifecycle)
- **PRD 07** — Resolution pipeline (scanners evaluate after movement)
- **PRD 10** — Fleet movement (scanners determine visibility of movement results)
