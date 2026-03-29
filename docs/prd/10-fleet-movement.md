# PRD 10 — Fleet Movement

## Overview

This document extracts and consolidates all fleet movement mechanics from PRD 07 into a dedicated reference. PRD 07 retains ownership of the turn resolution pipeline and player command schema; this PRD owns the movement rules.

Phase 1 movement is deliberately simple: fleets move toward waypoints at a fixed speed, with no fuel or mass considerations. Later phases layer fuel consumption, engine types, stargates, wormholes, and minefield interaction on top of this foundation.

## Distance Units

### The Parsec

All game distances and speeds are expressed in **parsecs (pc)** — an abstract distance unit with a fixed size in coordinate units, independent of galaxy size.

**1 parsec = 2^29 coordinate units (536,870,912).**

This is constant across all galaxy sizes. Bigger galaxies are simply more parsecs across:

| Galaxy Size | Bits | Galaxy width (pc) | Placement region (pc) |
|-------------|------|--------------------|-----------------------|
| Small       | 40   | 2,048              | ~1,024                |
| Medium      | 42   | 8,192              | ~4,096                |
| Large       | 44   | 32,768             | ~16,384               |
| Huge        | 46   | 131,072            | ~65,536               |

To convert: **coordinate units → parsecs** = shift right by 29. **Parsecs → coordinate units** = shift left by 29.

### Why Powers of Two?

The scale factor is a power of two so that coordinate ↔ parsec conversion uses bit shifts rather than division. This keeps all arithmetic fast and exact with integers — no rounding errors from division.

## Warp Speed

### Phase 1 (Current)

Fleet speed is simple: a fleet moves up to `speed` parsecs per turn toward its first waypoint. Multi-ship fleets move at the speed of their slowest design.

Speed is a flat value: `speed: 6` means 6 parsecs per turn.

### Future: Warp Factor System

The original Stars! uses a warp factor system:

- **Warp N** = N² light-years per turn of movement
- **Fuel cost** scales with warp factor cubed (warp³) × fleet mass
- Players choose warp speed per waypoint leg, trading speed against fuel

This will be implemented when the fuel model is added. The movement algorithm below is designed to accommodate it — only the distance budget calculation changes.

## Movement Algorithm

Fleet movement uses **integer arithmetic only** — no floating-point at any step.

Given:
- Fleet position `(fx, fy)` in coordinate units
- First waypoint `(wx, wy)` in coordinate units
- Fleet speed `S` in parsecs
- Scale factor `K = 2^29` (coordinate units per parsec)

```
1. Compute displacement:
     dx = wx - fx
     dy = wy - fy

2. Compute squared distance:
     dist_sq = dx² + dy²

3. Compute movement budget in coordinate units:
     budget = S × K

4. If dist_sq ≤ budget²:
     → Fleet arrives at waypoint. Set position to (wx, wy).
       Remove this waypoint from the list.
       Remaining movement = budget - isqrt(dist_sq).
       If waypoints remain and remaining > 0, repeat from step 1
       with the next waypoint and the remaining movement as budget.

5. Otherwise (fleet doesn't reach waypoint):
     → Move along the vector toward the waypoint:
       new_x = fx + (dx × budget) / isqrt(dist_sq)
       new_y = fy + (dy × budget) / isqrt(dist_sq)
       (integer division, truncating toward zero)
       Set position to (new_x, new_y).
```

### Integer Square Root (`isqrt`)

`isqrt(n)` returns the largest integer `r` such that `r² ≤ n`. Implemented via Newton's method on integers — deterministic, exact, and platform-independent.

The engine defines its own `isqrt`, not a platform library function. This guarantees identical results across Python and any future client-side validation.

### Rounding and Precision

Integer division truncates. Fleets may move very slightly less than their full speed budget each turn. Given the coordinate space is 40+ bits and movements are at the parsec scale (2^29 coordinate units), truncation error is negligible.

The key property: movement is **deterministic**. The same inputs always produce the same position.

### Stationary Fleets

A fleet with an empty waypoint list does not move.

### Waypoint Consumption

When a fleet arrives at a waypoint (distance ≤ budget), the waypoint is removed from the front of the list. If the fleet has remaining movement and more waypoints exist, it continues toward the next waypoint in the same turn.

A fleet can pass through multiple waypoints in a single turn if its speed is sufficient.

### Fleet Processing Order

Fleets are processed in sorted order by fleet ID (lexicographic). In Phase 1 fleets don't interact during movement, but deterministic ordering matters for future phases (combat at arrival, minefield hits).

## Future Movement Features

These are documented here for context but are **out of scope** for initial implementation:

### Fuel Consumption
- Each engine type has a fuel efficiency curve
- Fuel cost = f(warp_factor, fleet_mass, engine_type) per parsec
- Fleets without enough fuel move at reduced speed or stop
- Refuelling at starbases and fuel depots

### Stargates
- Instant fleet transfer between two starbases with stargates
- Mass and range limits — exceeding limits risks losing ships
- Gate ranges vary by tech level

### Wormholes
- Natural connections between distant points
- Stability varies — endpoints wander over time
- Must be within scanner range to detect

### Minefield Interaction
- Fleets moving through enemy minefields have a per-light-year chance of hitting a mine
- Hit probability depends on minefield type and fleet speed
- Damage applied mid-movement

### Speed Selection per Leg
- Players can set a different warp speed for each waypoint leg
- Higher speed = more fuel, but faster arrival
- Useful for managing fuel on long multi-stop routes

## Relationship to Other PRDs

- **PRD 02** — Coordinate system and galaxy bounds
- **PRD 04** — Determinism requirements, integer arithmetic rules
- **PRD 05** — Fleet schema in global state (position, waypoints, composition)
- **PRD 07** — Turn resolution pipeline (when movement happens in the resolution order)
- **PRD 11** — Scanner ranges determine what players can see after movement
