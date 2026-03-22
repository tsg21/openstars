# PRD 07 — Turn Mechanics

## Overview

This document defines the Phase 1 turn resolution pipeline: what happens when the server processes a turn, in what order, and how fleet movement works. It also establishes the player command schema — what orders players can issue — and includes the full Stars! resolution order as a long-term reference.

Phase 1 mechanics are deliberately minimal: fleets move toward waypoints, and that's it. No combat, no economy, no fuel. Later phases layer complexity onto this foundation.

## Distance Units

The coordinate space from PRD 02 uses large unsigned integers (40-bit for a small galaxy = ~1 trillion per axis). Game mechanics — speed, scanner range, movement — need a human-friendly distance unit rather than raw coordinate values.

### The Parsec

All game distances and speeds are expressed in **parsecs (pc)** — an abstract distance unit mapped to the coordinate space by a scale factor.

| Galaxy Size | Bits | Scale (coordinate units per parsec) |
|-------------|------|-------------------------------------|
| Small       | 40   | 2^29 (536,870,912)                  |
| Medium      | 42   | 2^30 (1,073,741,824)               |
| Large       | 44   | 2^31 (2,147,483,648)               |
| Huge        | 46   | 2^32 (4,294,967,296)               |

The scale doubles with each size step (+1 bit), matching the 2× per-axis growth from PRD 02. This means a galaxy is roughly the same "size in parsecs" regardless of the coordinate bit range — approximately **2,048 pc** across the full axis, or **~1,024 pc** across the placement region (middle 50%).

With 50 planets in a small galaxy's placement region (~1,024 × 1,024 pc), the average nearest-neighbour distance is roughly **70–100 pc**.

### Why Powers of Two?

The scale factor is a power of two so that coordinate ↔ parsec conversion uses bit shifts rather than division. This keeps all arithmetic fast and exact with integers — no rounding errors from division.

### Parsec Values in Game State

Speed and scanner range in the global state (PRD 05) are expressed in **parsecs**:

```yaml
designs:
  - id: DEa3f0p5
    owner: tim
    name: Long Range Scout
    hull: scout
    speed: 6           # parsecs per turn
    scanner_range: 150  # parsecs
```

The engine converts parsecs to coordinate units internally when computing movement and distances.

## Fleet Movement

### Warp Speed

In Phase 1, fleet speed is simple: a fleet moves up to `speed` parsecs per turn toward its first waypoint. Multi-ship fleets move at the speed of their slowest design.

Future phases may introduce the Stars!-style warp factor system (where warp N = N² distance per turn, with fuel costs scaling by warp cubed). For Phase 1, speed is linear — `speed: 6` means 6 parsecs per turn.

### Movement Algorithm

Fleet movement is computed using **integer arithmetic only** — no floating-point at any step.

Given:
- Fleet position `(fx, fy)` in coordinate units
- First waypoint `(wx, wy)` in coordinate units
- Fleet speed `S` in parsecs
- Scale factor `K` (coordinate units per parsec)

```
1. Compute displacement:
     dx = wx - fx
     dy = wy - fy

2. Compute squared distance:
     dist_sq = dx² + dy²

3. Compute movement budget in coordinate units:
     budget = S × K

4. If dist_sq <= budget²:
     → Fleet arrives at waypoint. Set position to (wx, wy).
       Remove this waypoint from the list.
       Remaining movement = budget - isqrt(dist_sq).
       If waypoints remain and remaining > 0, repeat from step 1
       with the next waypoint and the remaining movement as the new budget.

5. Otherwise (fleet doesn't reach waypoint):
     → Move along the vector toward the waypoint:
       new_x = fx + (dx × budget) / isqrt(dist_sq)
       new_y = fy + (dy × budget) / isqrt(dist_sq)
       (integer division, truncating toward zero)
       Set position to (new_x, new_y).
```

#### Integer Square Root (`isqrt`)

`isqrt(n)` returns the largest integer `r` such that `r² ≤ n`. Implemented via Newton's method on integers — deterministic, exact, and platform-independent.

This is the only "tricky" piece of math in the movement system. It must be implemented identically across all platforms (the engine defines its own `isqrt`, not a platform library).

#### Rounding and Precision

Integer division truncates. This means fleets may move very slightly less than their full speed budget on each turn. Over many turns, this could accumulate — but given the coordinate space is 40+ bits and movements are at the parsec scale (2^29 coordinate units), the truncation error is negligible relative to the grid resolution.

The key property: movement is **deterministic**. The same inputs always produce the same position, because every operation is integer arithmetic with defined rounding.

### Stationary Fleets

A fleet with an empty waypoint list does not move. It stays at its current position.

### Waypoint Consumption

When a fleet arrives at a waypoint (distance ≤ budget), the waypoint is removed from the front of the list. If the fleet has remaining movement and more waypoints exist, it continues toward the next waypoint in the same turn.

A fleet can pass through multiple waypoints in a single turn if its speed is sufficient.

## Player Commands

### Command File Schema

Each player submits one command file per turn:

```yaml
# player-command-{username}-T{N}.yaml
commands:
  - type: set_waypoints
    fleet_id: FL9qb7w1
    waypoints:
      - x: 550148141952
        y: 549755867136
      - x: 549311406080
        y: 549956141056
```

### Phase 1 Command Types

#### `set_waypoints`

Replace a fleet's waypoint list.

| Field | Type | Description |
|-------|------|-------------|
| `fleet_id` | string | ID of the fleet to command. Must be owned by the player. |
| `waypoints` | list | Ordered list of `{x, y}` destinations in coordinate units. Empty list = stop and hold position. |

This is the only command type in Phase 1. Future phases add: `set_production`, `set_research`, `create_design`, `split_fleet`, `merge_fleets`, `set_battle_plan`, etc.

### Command Validation

The server validates commands before resolution:

- `fleet_id` must reference a fleet owned by the commanding player
- Waypoint coordinates must be within the galaxy bounds
- Unknown command types are rejected
- Commands referencing entities the player doesn't own are rejected
- If a player submits no commands (empty file or no file), their fleets continue on their existing waypoints

### Command vs State

Commands express **intent changes**, not the full desired state. A `set_waypoints` command replaces the fleet's waypoint list. If a player doesn't issue a command for a fleet, its existing waypoints carry over unchanged.

This means a player only needs to submit commands for things they want to **change**. A fleet on a multi-waypoint route continues automatically unless the player redirects it.

## Phase 1 Resolution Pipeline

When all players have submitted commands (or the server triggers resolution), the turn resolves in this order:

```
resolve(global-state-T{N}, all-player-commands) → global-state-T{N+1}
```

### Step 1: Apply Commands

Process all player commands against the current state:

1. For each `set_waypoints` command: replace the target fleet's waypoint list

Commands are applied in player order (alphabetical by username, for determinism). Within a player's commands, they are applied in file order.

### Step 2: Move Fleets

For each fleet with a non-empty waypoint list, execute the movement algorithm (see Fleet Movement above).

Fleet processing order: sorted by fleet ID (lexicographic). This ensures deterministic results when multiple fleets might interact (relevant in future phases with combat; in Phase 1 fleets don't interact).

### Step 3: Increment Turn Counter

Update the `turn` field in the game state.

### Output

The resolution produces `global-state-T{N+1}.yaml` with:
- Updated fleet positions and waypoint lists
- Incremented turn number
- Everything else unchanged (planets, designs, players, seed, next_id)

That's it for Phase 1. No combat, no economy, no production, no fuel. Fleets move, and the world ticks forward.

## Stars! Resolution Order (Reference)

The original Stars! game resolves turns in this fixed order. This is the long-term target for OpenStars! as mechanics are added in later phases.

Source: [Stars! Order of Events](http://www.starsfaq.com/advfaq/order-of-events.htm)

1. **Fleet scrapping** — fleets ordered to scrap are dismantled, minerals recovered
2. **Waypoint 0 tasks** — load/unload cargo, colonise, remote mining
3. **Mineral packet movement and impact** — packets launched by mass drivers travel toward destinations
4. **Fleet movement** — fuel consumption, minefield hits, stargate/wormhole travel
5. **Inner Strength population growth** — population growth in fleets (IS racial trait)
6. **Space Demolition minefield detonation** — SD minefields detonate
7. **Mining** — planets extract minerals
8. **Production** — research, construction, packet launches, terraforming orders
9. **Population growth/death** — population changes on planets (growth, overcrowding, max pop)
10. **Fleet combat** — battles resolved at each location where hostile fleets meet
11. **Bombing** — fleets bomb enemy planets
12. **Waypoint 1 tasks** — second round of waypoint tasks after movement
13. **Mine laying** — fleets lay minefields
14. **Mine sweeping** — fleets sweep enemy minefields
15. **Repair** — damaged ships repair
16. **Terraforming** — planets are terraformed toward ideal conditions

Phase 1 implements only **step 4** (movement, without fuel/minefields/stargates). The pipeline will expand as phases add mechanics, always preserving this ordering.

## What's Out of Scope

- **Fog of war / scanner rules** — defined separately (PRD 08). The turn resolution pipeline produces the next global state; player state derivation (filtering by scanners) is a separate step.
- **Fuel consumption** — future phase. Phase 1 fleets have unlimited range.
- **Combat** — Phase 4.
- **Economy / production** — Phase 3.
- **Waypoint tasks** (load, unload, colonise) — future phase. Phase 1 waypoints are movement-only.
- **Specific speed/scanner values for game balance** — the defaults in this PRD and PRD 05 are starting points. Playtesting will refine them.
