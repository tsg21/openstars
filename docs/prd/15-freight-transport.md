# PRD 15 — Freight Transport

## Overview

This document defines the freight transport system for OpenStars! — how ships carry minerals and colonists between planets and fleets. Cargo transport is the connective tissue of the economy: minerals must travel from mining planets to production planets, and colonists must reach new worlds before they can grow into productive colonies.

This PRD covers the **simulation layer** — cargo capacity on ship designs, fleet cargo state, waypoint transport tasks, load/unload resolution, fleet-to-fleet transfer, colonisation, and repeat routes. Mass drivers (mineral packet flinging) are deferred to Phase 7.

## Design Philosophy

Freight mechanics faithfully reproduce the core Stars! model:

- **Cargo is physical** — minerals and colonists occupy space in ship holds; they must be explicitly loaded and unloaded
- **Waypoint tasks** — transport orders are attached to waypoints, not issued as separate commands
- **Fleet capacity limits** — a fleet can carry no more than the sum of its ships' cargo holds
- **Colonists are cargo** — colonists occupy cargo space at 100 colonists per kT
- **Partial loads are allowed** — if a planet has less than the requested amount, the fleet takes what's available; no error is raised
- **Fleet order is deterministic** — cargo operations at shared waypoints execute in fleet ID order, so contention is predictable
- **Repeat routes** — a fleet can be set to loop its waypoints indefinitely, enabling automated supply runs without re-issuing orders each turn

---

## Cargo Types

Four cargo types exist. All are measured in kT except colonists, which are counted as individuals with a kT conversion for capacity:

| Type | Unit | Capacity Conversion |
|------|------|---------------------|
| Ironium | kT | 1 kT = 1 kT capacity |
| Boranium | kT | 1 kT = 1 kT capacity |
| Germanium | kT | 1 kT = 1 kT capacity |
| Colonists | individuals | 100 colonists = 1 kT capacity |

For capacity calculations:

```python
used_capacity = ironium + boranium + germanium + (colonists // 100)
```

Fractional colonist-kT are rounded up — 199 colonists uses 2 kT, not 1.

### Colonist-Specific Rules

- **Loading**: colonists are subtracted from the source planet's population; if loading from a planet the player doesn't own, the command is rejected at validation
- **Unloading onto an owned planet**: colonists are added to the planet's population
- **Unloading onto an unowned planet**: blocked - the planet has to be colonised first
- **Unloading onto an enemy planet**: blocked — attempted unloading of colonists onto another player's planet is an invasion, handled by the future combat PRD; the colonists stay in the hold

---

## Cargo Holds

### Capacity

Cargo capacity is a per-design property, measured in kT. A fleet's total capacity is:

```python
fleet_cargo_capacity = sum(design.cargo_capacity * entry.count
                           for entry in fleet.composition)
```

Total cargo loaded across all types must not exceed `fleet_cargo_capacity`. Loading is capped at capacity — excess is left at the source.

Hull and design definitions — including `cargo_capacity` and `fuel_capacity` per design — are owned by [PRD 18 — Ship Design](18-ship-design.md) and [PRD 19 — Hull Slot Definitions](19-hull-slot-definitions.md).

---

## Waypoint Tasks

Waypoints are extended from plain `{x, y}` coordinates to optionally include a task. When a fleet arrives at a waypoint with a task, the task executes before the waypoint is consumed and the fleet continues.

### Task Types

| Task Type | Description |
|-----------|-------------|
| `"transport"` | Load or unload cargo at a planet |
| `"transfer"` | Load or unload cargo with another fleet at the same location (same owner only) |

A waypoint with no task is movement-only — the fleet passes through and continues.

### Transport Actions

Used in `"transport"` and `"transfer"` tasks. Each order targets one cargo type:

| Action | Amount Required | Behaviour |
|--------|----------------|-----------|
| `"load_all"` | No | Load all available of this type |
| `"load_amount"` | Yes | Load exactly N kT/colonists (partial if unavailable) |
| `"load_up_to"` | Yes | Load until the fleet holds N kT/colonists total |
| `"unload_all"` | No | Unload everything of this type |
| `"unload_amount"` | Yes | Unload exactly N kT/colonists (partial if fleet holds less) |
| `"unload_but"` | Yes | Unload all, keeping N kT/colonists in the hold |

For `amount`-based actions, the unit matches the cargo type: kT for minerals, individuals for colonists.

### `"transport"` Task

Load or unload cargo between the fleet and a planet. The planet is identified by matching the waypoint coordinates to a planet in `galaxy.json`.

If no planet exists at the waypoint coordinates, the task is silently skipped — the fleet continues.

```json
{
  "x": 549755813888,
  "y": 549755867136,
  "task": {
    "type": "transport",
    "orders": [
      { "cargo_type": "ironium", "action": "load_all" },
      { "cargo_type": "germanium", "action": "load_up_to", "amount": 50 }
    ]
  }
}
```

Orders are executed in list order. Capacity is checked after each order — subsequent orders will have less capacity available if earlier orders partially filled the hold.

### `"transfer"` Task

Load or unload cargo with a specific fleet at the same location. Both fleets must share the same `position` at resolution time and must be owned by the same player.

```json
{
  "x": 549755813888,
  "y": 549755867136,
  "task": {
    "type": "transfer",
    "fleet_id": "FLp4h8e2",
    "orders": [
      { "cargo_type": "ironium", "action": "load_all" }
    ]
  }
}
```

`"load"` actions draw from the target fleet; `"unload"` actions push to the target fleet. Capacity constraints apply to both fleets — the receiving fleet cannot accept more than its remaining capacity.

If the target fleet is not at the same coordinates at resolution time, the task is skipped and an event notifying the player is issued.

Cross-player transfers (diplomacy/trade) are deferred to the diplomacy PRD.

---

## Repeat Routes

A fleet can be set to repeat its waypoints indefinitely. When `repeat` is enabled, each waypoint is moved to the **end** of the waypoints list after execution rather than being discarded. The fleet cycles through its route until `repeat` is turned off.

To stop a repeating fleet, issue a `set_waypoints` command with `repeat: false` and the new (or empty) waypoint list.

---

## Jettison

A fleet can discard cargo using the `jettison_cargo` command. Jettisoned cargo is destroyed — it cannot be recovered.

The fleet must be in deep space (not at a planet's coordinates) when the command is applied in Step 1. Jettison amounts must not exceed current holdings; partial jettison is allowed.

---

## Schema

### `FleetState` (global state)

```python
class Cargo(BaseModel):
    ironium: int = 0      # kT
    boranium: int = 0     # kT
    germanium: int = 0    # kT
    colonists: int = 0    # individuals (100 per kT of capacity, rounded up)

class FleetState(BaseModel):
    id: str
    owner: str
    position: Position
    composition: list[CompositionEntry]
    waypoints: list[Waypoint]
    repeat: bool = False
    cargo: Cargo = Cargo()
```

### `Waypoint` (global state)

Waypoints gain an optional `task` field. Plain `{x, y}` waypoints remain valid — the `task` field defaults to `null`.

```python
class CargoOrder(BaseModel):
    cargo_type: str          # "ironium" | "boranium" | "germanium" | "colonists"
    action: str              # see Transport Actions table above
    amount: int | None = None

class WaypointTask(BaseModel):
    type: str                          # "transport" | "transfer"
    orders: list[CargoOrder] = []      # transport and transfer tasks
    fleet_id: str | None = None        # transfer tasks only

class Waypoint(BaseModel):
    x: int
    y: int
    task: WaypointTask | None = None
```

#### Example: Waypoint list for a mining run

```json
[
  {
    "x": 549755813888,
    "y": 549755867136,
    "task": {
      "type": "transport",
      "orders": [
        { "cargo_type": "ironium", "action": "load_all" },
        { "cargo_type": "boranium", "action": "load_all" },
        { "cargo_type": "germanium", "action": "load_all" }
      ]
    }
  },
  {
    "x": 550148141952,
    "y": 549755813888,
    "task": {
      "type": "transport",
      "orders": [
        { "cargo_type": "ironium", "action": "unload_all" },
        { "cargo_type": "boranium", "action": "unload_all" },
        { "cargo_type": "germanium", "action": "unload_all" }
      ]
    }
  }
]
```

With `repeat: true` on the fleet, this becomes an automated mineral ferry requiring no further orders.

### `PlayerFleet` (player state)

```python
class PlayerFleet(BaseModel):
    # ... existing fields ...
    cargo: Cargo | None = None           # owner only
    cargo_capacity: int | None = None    # owner only; total kT across all ships
```

Cargo is owner-only: other players cannot see what a fleet is carrying.

### Player Commands

#### `set_waypoints` (extended)

Backwards-compatible — plain `{x, y}` waypoints remain valid. New fields:

| Field | Type | Description |
|-------|------|-------------|
| `fleet_id` | string | Fleet to command (unchanged) |
| `waypoints` | list | Extended `Waypoint` objects with optional `task` |
| `repeat` | bool | Optional; sets/clears the fleet's repeat flag |

#### `jettison_cargo` (new)

```json
{
  "type": "jettison_cargo",
  "fleet_id": "FL9qb7w1",
  "cargo": {
    "ironium": 50,
    "boranium": 0,
    "germanium": 0,
    "colonists": 0
  }
}
```

Validation:
- Fleet must be owned by the commanding player
- Fleet must not be at a planet's coordinates
- Amounts must not exceed current holdings

### Player State Events

```json
{
  "type": "cargo_loaded",
  "turn": 3,
  "fleet_id": "FL9qb7w1",
  "fleet_name": "Freighter 1",
  "source_planet_id": "PLk8m3x2",
  "source_planet_name": "Earth",
  "ironium": 50,
  "boranium": 0,
  "germanium": 25,
  "colonists": 0
}
```

```json
{
  "type": "cargo_unloaded",
  "turn": 3,
  "fleet_id": "FL9qb7w1",
  "fleet_name": "Freighter 1",
  "dest_planet_id": "PL4fn9v6",
  "dest_planet_name": "Proxima",
  "ironium": 50,
  "boranium": 0,
  "germanium": 25,
  "colonists": 0
}
```

---

## Turn 0 Generation Changes

Each player now starts with a small freighter in addition to their scout:

1. Create one `small_freighter` design per player (hull `"small_freighter"`, `engine_id` `"ion_drive"`, `fuel_capacity` 130, `cargo_capacity` 70)
2. Create one small freighter fleet per player, parked at the home planet, with empty cargo and `fuel` equal to `fuel_capacity` (full tanks — home starbase auto-refuels on arrival)

Starting population and minerals on the home planet remain unchanged.

---

## Resolution Pipeline Changes

Cargo operations execute during Step 2 (Move Fleets), when a fleet arrives at a waypoint. After position is set to the waypoint, the task executes, then the waypoint is consumed (or recycled if `repeat` is true).

The `jettison_cargo` command is applied during Step 1 alongside `set_waypoints`.

```
Step 1: Apply commands  ← jettison_cargo applied here
Step 2: Move fleets     ← waypoint task execution on arrival
Step 3: Mining
Step 4: Calculate resources
Step 5: Production
Step 6: Population growth / death
Step 7: Increment turn counter
```

### Step 1: Apply Commands (Extended)

For each `jettison_cargo` command (after validating ownership, deep-space location, and amounts):
1. Subtract the specified amounts from `fleet.cargo`

For each `set_waypoints` command:
1. Replace the fleet's waypoints (unchanged)
2. If `repeat` field is present, update `fleet.repeat`

Command application order: alphabetical by player username, then file order within a player's commands.

### Step 2: Move Fleets (Extended)

When a fleet arrives at a waypoint (after setting position):

1. If `waypoint.task` is not null, execute the task:
   - `"transport"`: resolve each order against the planet at `(x, y)`, if any
   - `"transfer"`: resolve each order against the target fleet, if present at same position
2. Consume the waypoint:
   - If `fleet.repeat` is true: move the waypoint to the **end** of the waypoints list
   - If `fleet.repeat` is false: remove the waypoint

Fleet processing order: sorted by fleet ID (lexicographic). This applies to both movement and task execution — if two fleets arrive at the same planet on the same turn with `"load_all"` orders, the fleet with the lexicographically smaller ID loads first.

#### Transport Task Resolution

For each order in the task, in list order:

**Load actions:**

```python
available = planet.minerals[cargo_type]   # or planet.population for colonists

if action == "load_all":
    amount = available

elif action == "load_amount":
    amount = min(order.amount, available)

elif action == "load_up_to":
    current = fleet.cargo[cargo_type]
    amount = min(order.amount - current, available)
    amount = max(amount, 0)

# Clamp to remaining fleet capacity
remaining_capacity = fleet_cargo_capacity - used_capacity(fleet.cargo)
if cargo_type == "colonists":
    kT_needed = amount // 100
else:
    kT_needed = amount
amount_loaded = amount if kT_needed <= remaining_capacity else remaining_capacity * (100 if cargo_type == "colonists" else 1)

fleet.cargo[cargo_type] += amount_loaded
planet.minerals[cargo_type] -= amount_loaded   # or planet.population -= amount_loaded for colonists
```

**Unload actions:**

```python
held = fleet.cargo[cargo_type]

if action == "unload_all":
    amount = held

elif action == "unload_amount":
    amount = min(order.amount, held)

elif action == "unload_but":
    amount = max(held - order.amount, 0)

fleet.cargo[cargo_type] -= amount
planet.minerals[cargo_type] += amount   # or planet.population += amount for colonists
```

---

## Interaction with Other Steps

**Step 3 (Mining):** Minerals mined this turn are added to planets **after** fleet cargo operations in Step 2. A freighter cannot load minerals that are mined in the same turn — they are available from the next turn onward.

**Step 5 (Production):** Minerals unloaded by freighters in Step 2 are available for production in Step 5 of the same turn. A fleet delivering germanium to a factory-starved colony contributes to that colony's production output immediately.

---

## UI Considerations

This PRD does not define UI layout (PRD 08), but notes for the frontend:

- **Fleet panel**: show cargo as a compact bar — `[████░░░] 48/70 kT` with a breakdown of ironium / boranium / germanium on hover
- **Waypoint task display**: in the fleet waypoints list, each waypoint should show its task type icon (load arrow, unload arrow) and a summary of cargo orders; clicking opens an order editor
- **Repeat mode indicator**: show a cycle icon on the fleet when `repeat: true`; make it easy to toggle
- **Planet panel**: show surface minerals as both the quantity and the "how many turns of production does this represent" annotation where relevant
- **Load shortfalls**: if a transport task loaded less than requested (partial load due to planet having insufficient minerals), include this in the per-turn event messages so players know their route is running dry
