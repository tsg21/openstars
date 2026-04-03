# PRD 07 — Turn Mechanics

## Overview

This document defines the Phase 1 turn resolution pipeline: what happens when the server processes a turn, in what order, and how fleet movement works. It also establishes the player command schema — what orders players can issue — and includes the full Stars! resolution order as a long-term reference.

Phase 1 mechanics are deliberately minimal: fleets move toward waypoints, and that's it. No combat, no economy, no fuel. Later phases layer complexity onto this foundation.

## Distance Units and Fleet Movement

Distance units (parsecs), the movement algorithm, warp speed, waypoint consumption, and all fleet movement rules are defined in **[PRD 10 — Fleet Movement](10-fleet-movement.md)**. This PRD previously contained these sections; they were extracted to keep movement mechanics in a single authoritative location.

The key facts for resolution context:
- 1 parsec = 2^29 coordinate units
- Phase 1: fleets move at `speed` parsecs per turn (linear, no fuel)
- Movement uses integer arithmetic only — deterministic and exact
- Fleets are processed in sorted order by fleet ID

## Player Commands

### Command File Schema

Each player submits one command file per turn:

```json
{
  "commands": [
    {
      "type": "set_waypoints",
      "fleet_id": "FL9qb7w1",
      "waypoints": [
        { "x": 550148141952, "y": 549755867136 },
        { "x": 549311406080, "y": 549956141056 }
      ]
    }
  ]
}
```

### Phase 1 Command Types

#### `set_waypoints`

Replace a fleet's waypoint list.

| Field | Type | Description |
|-------|------|-------------|
| `fleet_id` | string | ID of the fleet to command. Must be owned by the player. |
| `waypoints` | list | Ordered list of `{x, y}` destinations in coordinate units. Empty list = stop and hold position. |

#### `rename_fleet`

Give a fleet a new display name.

| Field | Type | Description |
|-------|------|-------------|
| `fleet_id` | string | ID of the fleet to rename. Must be owned by the player. |
| `name` | string | New display name. Must be non-empty and at most 64 characters. |

The rename takes effect immediately during command application (Step 1 of resolution). The new name persists in global state and is visible to the renaming player in their next player state.

Phase 1 command types are `set_waypoints` and `rename_fleet`. Future phases add: `set_production`, `set_research`, `create_design`, `split_fleet`, `merge_fleets`, `set_battle_plan`, etc.

### Command Validation

The server validates commands before resolution:

- `fleet_id` must reference a fleet owned by the commanding player
- Waypoint coordinates must be within the galaxy bounds
- `rename_fleet` name must be non-empty and at most 64 characters
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
2. For each `rename_fleet` command: update the target fleet's `name` field

Commands are applied in player order (alphabetical by username, for determinism). Within a player's commands, they are applied in file order.

### Step 2: Move Fleets

For each fleet with a non-empty waypoint list, execute the movement algorithm (see Fleet Movement above).

Fleet processing order: sorted by fleet ID (lexicographic). This ensures deterministic results when multiple fleets might interact (relevant in future phases with combat; in Phase 1 fleets don't interact).

### Step 3: Increment Turn Counter

Update the `turn` field in the game state.

### Output

The resolution produces `global-state-T{N+1}.json` with:
- Updated fleet positions and waypoint lists
- Incremented turn number
- Everything else unchanged (planets, designs, players, seed, next_id)

That's it for Phase 1. No combat, no economy, no production, no fuel. Fleets move, and the world ticks forward.

## Stars! Resolution Order (Reference)

The original Stars! turn resolution order — the long-term target for OpenStars! — is documented in [`docs/references/stars-resolution-order.md`](../references/stars-resolution-order.md).

Phase 1 implements only **step 4** (movement, without fuel/minefields/stargates). The pipeline will expand as phases add mechanics, always preserving this ordering.

## What's Out of Scope

- **Fog of war / scanner rules** — defined in PRD 11 (Scanners & Fog of War). The turn resolution pipeline produces the next global state; player state derivation (filtering by scanners) is a separate step.
- **Fuel consumption** — future phase. Phase 1 fleets have unlimited range.
- **Combat** — Phase 4.
- **Economy / production** — Phase 3.
- **Waypoint tasks** (load, unload, colonise) — future phase. Phase 1 waypoints are movement-only.
- **Specific speed/scanner values for game balance** — the defaults in this PRD and PRD 05 are starting points. Playtesting will refine them.
