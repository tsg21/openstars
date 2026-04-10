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

Fleet speed is expressed as a **warp factor** chosen by the player per waypoint leg. Distance traveled in one turn equals the warp factor squared in parsecs:

| Warp | Parsecs per turn |
|------|-----------------|
| 1 | 1 |
| 2 | 4 |
| 3 | 9 |
| 4 | 16 |
| 5 | 25 |
| 6 | 36 |
| 7 | 49 |
| 8 | 64 |
| 9 | 81 |
| 10 | 100 |

### Per-Leg Warp Selection

Each waypoint carries an optional `warp` field. If `warp` is absent or `null`, the engine selects the fleet's **optimum warp**: the highest speed at which the fleet has enough fuel to complete the entire leg. Ties prefer higher warp.

The optimum is computed at resolution time using the fuel formula below before movement begins.

### Warp 10 Risk

All engines have a `fuel_usage` entry at index 9 (Warp 10). Whether a given engine can travel safely at Warp 10 — or has a 10% chance of each ship being lost — is deferred to a future PRD.

## Fuel

Fuel is a manufactured commodity measured in **milligrams (mg)**. It is shared across all ships in a fleet — a fleet has a single fuel pool equal to the sum of the `fuel_capacity` values of all its ships.

### Fuel Capacity

Each ship design has a `fuel_capacity` (mg per ship). A fleet's total fuel capacity is:

```python
fleet_fuel_capacity = sum(
    design.fuel_capacity * entry.count
    for entry, design in fleet_designs
)
```

Current fuel is stored as `fleet.fuel` (integer mg, `0 ≤ fuel ≤ fleet_fuel_capacity`).

### Fuel Consumption Formula

Fuel is consumed per ship per movement step. For a single ship traveling `distance` parsecs at `warp`:

```
ship_fuel_used = (ship_mass × efficiency × distance / 200 + 9) / 10
```

Where:
- `ship_mass` — hull base mass + fitted component masses + cargo mass (kT). Cargo mass: 1 kT per kT of minerals; 1 kT per 100 colonists (rounded up).
- `efficiency` — `engine.fuel_usage[warp - 1]` (integer from the engine catalogue; `0` = free at that speed)
- `distance` — parsecs traveled this step (integer; `isqrt(dist_sq) >> 29` clamped to the step budget)

The `+9` in the numerator rounds the division by 10 upward (ceiling). All arithmetic is integer only.

Fleet fuel deducted in one movement step:

```python
fuel_used = sum(
    ((ship_mass(entry, design, fleet.cargo) * engine.fuel_usage[warp - 1] * distance // 200) + 9) // 10
    * entry.count
    for entry, design in fleet_designs
)
fleet.fuel = max(0, fleet.fuel - fuel_used)
```

### Free Travel

Any engine can travel at **Warp 1** at no fuel cost — `fuel_usage[0]` is `0` for all engines. Ramscoop engines (`is_ramscoop: true`) can travel free at higher speeds; their free warp is implicit from the leading `0` entries in `fuel_usage`.

### Insufficient Fuel

Before beginning a leg, the engine computes the fuel needed at the requested `warp`. If the fleet's current fuel is insufficient:

1. Try each lower warp from `requested_warp − 1` down to `2`, stopping at the first speed the current fuel can cover for the full leg distance.
2. If even Warp 2 is unaffordable, the fleet travels at Warp 1 for free (no fuel deducted).
3. Movement proceeds at the highest affordable warp.

The player receives a `fleet.fuel_warning` event noting the fleet slowed and the warp it actually traveled at.

### Auto-Refuelling

When a fleet arrives at a waypoint whose coordinates match a planet that:
- is owned by the same player, **and**
- has a starbase with `can_build_ships: true`

...the fleet's fuel is topped up to `fleet_fuel_capacity` after waypoint task resolution (transport, colonise, etc.) in the same step. No explicit command is required.

Newly built fleets depart at full fuel. Turn 0 fleets also start at full fuel.

## Movement Algorithm

Fleet movement uses **integer arithmetic only** — no floating-point at any step.

Given:
- Fleet position `(fx, fy)` in coordinate units
- First waypoint `(wx, wy)` in coordinate units
- Warp factor `W` for this leg (`waypoint.warp`, or computed optimum; reduced if fuel is insufficient)
- Scale factor `K = 2^29` (coordinate units per parsec)

```
0. Determine effective warp:
     W = waypoint.warp ?? optimum_warp(fleet, leg_distance)
     W = reduce_for_fuel(fleet, W, leg_distance)   ← see Insufficient Fuel

1. Compute displacement:
     dx = wx - fx
     dy = wy - fy

2. Compute squared distance:
     dist_sq = dx² + dy²

3. Compute movement budget in coordinate units:
     budget = W² × K

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

These are documented here for context but are **out of scope** for the current implementation:

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

## Schema Changes

### `EngineStats` (component catalogue)

Add two fields:

```python
class EngineStats(BaseModel):
    is_ramscoop: bool = False
    fuel_usage: list[int] = Field(min_length=10, max_length=10)
    # fuel usage at warp 1..10 (index 0 = warp 1, index 9 = warp 10)
    # 0 = free travel at that speed; free warp is implicit from the first non-zero entry
```

Engine YAML entries add `fuel_usage`. Example for the Ion Drive (Long Hump 6 class, from the original Stars! technology table):

```yaml
engine:
  is_ramscoop: false
  fuel_usage: [0, 20, 60, 100, 100, 105, 450, 750, 900, 1080]
```

And for the Trans-Galactic Drive:

```yaml
engine:
  is_ramscoop: false
  fuel_usage: [0, 15, 35, 45, 55, 70, 80, 90, 100, 120]
```

### `Design` (global state / design registry)

`Design` stores derived values, not component references. Replace `speed: int` with derived fuel fields:

```python
class Design(BaseModel):
    id: str
    owner: str
    name: str
    hull: str
    fuel_usage: list[int]  # 10 entries, warp 1..10 — copied from engine at design creation
    fuel_capacity: int     # mg per ship — from hull definition at design creation
    scanner: Scanner
    cargo_capacity: int = 0
    cost: DesignCost
```

`engine_id` belongs to the full `ShipDesign` component list (PRD 18) and is not stored here.


### `Fleet` (global state)

Add fuel pool:

```python
class Fleet(BaseModel):
    ...
    fuel: int = 0         # NEW — current fuel in mg (shared across all ships in fleet)
```

`fleet_fuel_capacity` is derived at runtime: `sum(design.fuel_capacity * entry.count for ...)`.

### `Waypoint` (global state)

Add per-leg warp selection:

```python
class Waypoint(BaseModel):
    x: int
    y: int
    warp: int | None = None   # NEW — desired warp for this leg; null = auto-optimum
    task: WaypointTask | None = None
```

### `PlayerFleet` (player state)

Expose fuel to the owning player:

```python
class PlayerFleet(BaseModel):
    ...
    fuel: int | None = None               # NEW — owner only
    fuel_capacity: int | None = None      # NEW — owner only; total mg across all ships
```

## Relationship to Other PRDs

- **PRD 02** — Coordinate system and galaxy bounds
- **PRD 04** — Determinism requirements, integer arithmetic rules
- **PRD 05** — Fleet schema in global state (position, waypoints, composition)
- **PRD 07** — Turn resolution pipeline (when movement happens in the resolution order)
- **PRD 11** — Scanner ranges determine what players can see after movement
- **PRD 15** — Freight transport; cargo mass contributes to fuel consumption
- **PRD 17** — Starbases; `can_build_ships` gates auto-refuelling
- **PRD 20** — Component catalogue; `EngineStats` fuel tables live there
