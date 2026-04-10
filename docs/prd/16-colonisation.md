# PRD 16 — Colonisation

## Overview

This document defines the colonisation mechanic for OpenStars! — how a fleet claims an uninhabited planet and establishes a new colony. Colonisation is the strategic engine of expansion: every new world captured opens up more population capacity, more mines, more factories, and more resources.

This PRD covers the **simulation layer** — the `colonize` waypoint task, the colonisation module hull component, the colony ship hull type, ship dismantling on arrival, colony establishment, and the events generated. UI layout is addressed separately in PRD 08.

Turn 0 colony ship seeding is already implemented separately; this PRD defines the mechanic and API contract the backend must satisfy.

---

## Design Philosophy

Colonisation faithfully reproduces the core Stars! model:

- **Colony ships are consumed** — colonist ships dismantle themselves on landing; their minerals partially seed the new colony's surface stockpile
- **Colonists must be aboard** — a fleet with no colonists in its cargo cannot colonise a planet
- **One-step claim** — a single `colonize` waypoint task claims ownership, deposits colonists, and dismantles the colony ship in one resolution step
- **Uninhabited only** — you cannot colonise a planet that already has an owner; that requires combat (future PRD)
- **Killer planets are claimable** — the engine does not block colonisation of hostile planets; colonists will die every turn (per PRD 14) — that is the player's strategic risk to take

---

## The Colonisation Module

A colonisation module is a hull component that enables the `colonize` waypoint task. A fleet can execute a colonise task only if at least one ship in the fleet has a colonisation module.

For this PRD, the colonisation module is an implicit property of the `colony_ship` hull type. The ship designer (future PRD) will model it as an explicit slot component. For now:

> A fleet can execute a `colonize` task if and only if it contains at least one ship of hull type `colony_ship`.

---

## Hull Types

This PRD adds one new pre-defined hull type:

| Hull | Engine | Fuel Capacity | Cargo Capacity | Has Colonisation Module |
|------|--------|---------------|----------------|------------------------|
| `colony_ship` | `ion_drive` | 200 mg | 25 kT | Yes |

The `colony_ship` has a modest cargo hold — enough for an initial wave of colonists. Larger colonist deliveries to established colonies use freighters with `transport` waypoint tasks (PRD 15).

---

## The `colonize` Waypoint Task

The `colonize` task is a new waypoint task type, alongside the existing `transport` and `transfer` tasks from PRD 15.

```json
{
  "x": 549755813888,
  "y": 549755867136,
  "task": {
    "type": "colonize"
  }
}
```

The task has no additional fields — all colonists currently in the fleet's cargo hold are landed.

### Preconditions (Validated at Resolution)

The following must all be true when the fleet arrives at the waypoint, or the task is skipped and a player event is issued:

1. A planet exists at the waypoint coordinates
2. The planet has no owner (`owner == null`)
3. The fleet contains at least one `colony_ship`
4. The fleet's cargo holds at least 1 colonist

If any precondition fails, the fleet continues to its next waypoint and a `colonisation.failed` event is emitted.

### Resolution Steps

When preconditions are met:

1. **Establish ownership** — set `planet.owner` to the fleet's owner
2. **Land colonists** — set `planet.population` to the total colonists in `fleet.cargo.colonists`; set `fleet.cargo.colonists` to 0
3. **Dismantle colony ships** — for each `colony_ship` in the fleet's composition:
   - Remove the ship from `fleet.composition`
   - Add the dismantled ship's mineral contribution to `planet.minerals` (see Dismantling below)
4. **Land remaining cargo** — any minerals remaining in `fleet.cargo` after dismantling are also deposited on the planet; set all mineral cargo fields to 0
5. **Dissolve fleet if empty** — if the fleet has no ships remaining after dismantling, it is removed from global state
6. **Emit** a `colonisation.colonised` event to the player

If the fleet contains other ship types alongside the colony ship(s), those ships remain in the fleet and continue to subsequent waypoints.

---

## Colony Ship Dismantling

When a colony ship is dismantled, a fraction of its construction minerals are recovered and added to the new colony's surface stockpile. This gives the fledgling colony a small mineral head-start.

The mineral recovery formula is:

```python
DISMANTLE_RECOVERY = 0.333   # 1/3 of construction cost is recovered

recovered_ironium   = floor(colony_ship_cost.ironium   * DISMANTLE_RECOVERY)
recovered_boranium  = floor(colony_ship_cost.boranium  * DISMANTLE_RECOVERY)
recovered_germanium = floor(colony_ship_cost.germanium * DISMANTLE_RECOVERY)
```

### Colony Ship Construction Cost

For the pre-defined `colony_ship` hull (used until the ship designer is implemented):

| Mineral    | Construction Cost | Recovered on Dismantle |
|------------|------------------|------------------------|
| Ironium    | 5 kT             | 1 kT                   |
| Boranium   | 5 kT             | 1 kT                   |
| Germanium  | 15 kT            | 5 kT                   |

These are applied **per colony ship** dismantled. If two colony ships are in the fleet, the recovered amounts are doubled.

---

## Schema Changes

### `DesignState` (global state)

No new fields. The `hull` field carries `"colony_ship"` as a valid value.

#### Example: Colony Ship Design

```json
{
  "id": "DEp3r1c9",
  "owner": "tim",
  "name": "Colony Ship",
  "hull": "colony_ship",
  "fuel_usage": [0, 20, 60, 100, 100, 105, 450, 750, 900, 1080],
  "fuel_capacity": 200,
  "cargo_capacity": 25
}
```

### `PlanetState` — no new fields

Colonisation uses only existing fields: `owner`, `population`, `minerals`.

### Player Commands

#### `set_waypoints` (extended)

The `colonize` task type is added to the `WaypointTask` schema. No new fields on the task itself.

```python
class WaypointTask(BaseModel):
    type: str            # "transport" | "transfer" | "colonize"  ← "colonize" added
    orders: list[CargoOrder] = []
    fleet_id: str | None = None
```

### Player State Events

Colonisation events use the generic event envelope from PRD 03 / PRD 50:

- `owner: string`
- `source_id: string | null`
- `code: string`
- `values: (string | number)[]`

#### `colonisation.colonised` (new)

```json
{
  "owner": "tim",
  "source_id": "PL4fn9v6",
  "code": "colonisation.colonised",
  "values": ["Colony Ship 1", "Proxima II", 2500, 1, 1, 5]
}
```

Ordered `values`:

1. `fleet_name`
2. `planet_name`
3. `colonists_landed`
4. `recovered_ironium`
5. `recovered_boranium`
6. `recovered_germanium`

#### `colonisation.failed` (new)

```json
{
  "owner": "tim",
  "source_id": "PL4fn9v6",
  "code": "colonisation.failed",
  "values": ["Colony Ship 1", "Proxima II", "planet_already_owned"]
}
```

Ordered `values`:

1. `fleet_name`
2. `planet_name`
3. `reason`

If no planet exists at the waypoint coordinates, `source_id` is `null` and `planet_name` is the literal string `"Unknown planet"`.

Valid `reason` values:

| Reason | Condition |
|--------|-----------|
| `"no_planet"` | No planet at waypoint coordinates |
| `"planet_already_owned"` | Planet has an owner |
| `"no_colony_ship"` | Fleet has no `colony_ship` hull |
| `"no_colonists"` | Fleet is carrying zero colonists |

---

## Turn 0 Generation Changes

Each player now starts with a colony ship in addition to their scout and small freighter:

1. Create one `colony_ship` design per player (hull `"colony_ship"`, `fuel_usage` from `ion_drive`, `fuel_capacity` 200, `cargo_capacity` 25)
2. Create one colony ship fleet per player, parked at the home planet, with empty cargo

Players must manually load colonists from their home planet before dispatching the colony ship.

This turn 0 setup is already implemented separately; this PRD documents the expected generated state for completeness.

---

## Resolution Pipeline

Colonisation executes in **Step 2 (Move Fleets)**, alongside other waypoint tasks, using the same fleet processing order (sorted by fleet ID, lexicographic).

```
Step 1: Apply commands
Step 2: Move fleets     ← colonize task executes on arrival (after transport/transfer)
Step 3: Mining
Step 4: Calculate resources
Step 5: Production
Step 6: Population growth / death
Step 7: Increment turn counter
```

### Within Step 2: Task Execution Order

When a fleet arrives at a waypoint, task types resolve in this order:

1. `"transport"` — load/unload cargo with the planet
2. `"transfer"` — load/unload cargo with another fleet
3. `"colonize"` — claim ownership and dismantle colony ship

This ordering means a single waypoint cannot combine a `colonize` task with a `transport` or `transfer` task — each waypoint has at most one task. The ordering is irrelevant in practice but is noted for completeness.

### Step 2: Colonize Task Resolution (Detail)

```python
def resolve_colonize(fleet, planet, turn):
    # Precondition checks
    if planet is None:
        emit colonisation.failed(fleet, None, "no_planet")
        return
    if planet.owner is not None:
        emit colonisation.failed(fleet, planet, "planet_already_owned")
        return
    colony_ships = [e for e in fleet.composition if design(e).hull == "colony_ship"]
    if not colony_ships:
        emit colonisation.failed(fleet, planet, "no_colony_ship")
        return
    if fleet.cargo.colonists == 0:
        emit colonisation.failed(fleet, planet, "no_colonists")
        return

    # Establish colony
    planet.owner = fleet.owner
    planet.population = fleet.cargo.colonists
    fleet.cargo.colonists = 0

    # Dismantle colony ships and recover minerals
    recovered = Minerals()
    for entry in colony_ships:
        cost = COLONY_SHIP_COST   # ironium=5, boranium=5, germanium=15
        recovered.ironium   += floor(cost.ironium   * DISMANTLE_RECOVERY) * entry.count
        recovered.boranium  += floor(cost.boranium  * DISMANTLE_RECOVERY) * entry.count
        recovered.germanium += floor(cost.germanium * DISMANTLE_RECOVERY) * entry.count
        fleet.composition.remove(entry)

    # Deposit recovered minerals and any remaining cargo
    planet.minerals.ironium   += recovered.ironium   + fleet.cargo.ironium
    planet.minerals.boranium  += recovered.boranium  + fleet.cargo.boranium
    planet.minerals.germanium += recovered.germanium + fleet.cargo.germanium
    fleet.cargo = Cargo()   # clear all cargo

    # Dissolve fleet if no ships remain
    if not fleet.composition:
        remove fleet from global state

    emit colonisation.colonised(fleet, planet, recovered)
```

---

## Interaction with Other Steps

**Step 3 (Mining):** A newly colonised planet has no mines yet. The owner may queue mine construction in Step 5 production, starting from the next turn.

**Step 6 (Population growth):** Colonists landed in Step 2 count toward that turn's population growth or death calculation. A colony landed on a hostile planet will begin losing colonists in the same turn it is established.

---

## UI Considerations

This PRD does not define UI layout (PRD 08), but notes for the frontend:

- **Colonize task button** — in the waypoint task editor, show `Colonize` as an option alongside `Transport` and `Transfer`; dim it if the fleet has no colony ship
- **Planet target indicator** — when a fleet is selected and a `colonize` waypoint is set, the destination planet should show a distinct "pending colonisation" marker
- **Colony ship panel** — the fleet detail panel should indicate that the colony ship will be dismantled on arrival; show the recovered minerals estimate
- **Event log** — `colonised` events are high-priority; surface them prominently (new world captured is a significant moment)
- **Habitability overlay** — use the colour-coded scanner view from PRD 14 to help players identify colonisation targets: green = positive hab, red = killer, yellow = terraformable (future)
