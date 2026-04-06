# PRD 13 — Production

## Overview

This document defines the first production system for OpenStars!: a **simple per-planet production queue**. Each owned planet has one ordered queue. The server resolves that queue during turn processing using the planet's available resources and minerals.

This PRD is intentionally narrow. It gives us enough design to build and test production without dragging in the full Stars! feature set.

## Scope

### In Scope

- One production queue per owned planet
- Ordered queue items processed from top to bottom
- Basic queue editing: add, remove, move, clear
- Partial progress on normal queue items across turns
- Mineral and resource spending during production
- Initial supported items: **Mines**, **Factories**, and **Ships**
- Owner-visible queue state in player state

### Explicitly Out of Scope

- Production templates
- Default production templates for new colonies
- Auto-build items
- Terraforming tasks in the production queue
- Starbase construction and upgrades
- Defences
- Research spending controls
- Tech-based cost reductions
- Ship scrapping
- Ship design editor

Those deferred features remain backlog items and should not be implied by this PRD.

## Design Principles

- **Server authoritative**: clients edit intent; the engine resolves outcomes.
- **Per-planet independence**: each planet consumes only its own resources and minerals.
- **Ordered blocking queue**: normal items block later items until they complete, are moved, or are removed.
- **Persistent progress**: partial work remains on the current queue item from turn to turn.
- **Deterministic resolution**: planets and queue items are processed in a fixed order.

## Queue Model

Each owned planet has a single production queue:

- Items are resolved from **top to bottom**
- A planet may have an empty queue
- Unowned planets always have an empty queue
- Queue state lives in the authoritative global state

### Supported Queue Items

| Item Type | Result on Completion | Cost Source |
|-----------|----------------------|-------------|
| `mine` | `planet.mines += 1` | PRD 12 |
| `factory` | `planet.factories += 1` | PRD 12 |
| `ship` | New ship added to fleet at planet | Design cost snapshot |

Fixed costs for `mine` and `factory`, inherited from [PRD 12 — Economy & Resources](12-economy-and-resources.md):

| Item Type | Resources | Ironium | Boranium | Germanium |
|-----------|-----------|---------|----------|-----------|
| `mine` | 5 | 0 | 0 | 0 |
| `factory` | 10 | 0 | 0 | 4 |

Ship costs are design-dependent. See [Ship Designs](#ship-designs) below.

## Queue Entry Schema

### Global State — `ProductionQueueItem`

```python
class Minerals(BaseModel):
    ironium: int = 0
    boranium: int = 0
    germanium: int = 0

class ProductionProgress(BaseModel):
    resources_spent: int = 0
    minerals_spent: Minerals = Minerals()

class ProductionQueueItem(BaseModel):
    id: str
    item_type: Literal["mine", "factory", "ship"]
    quantity: int
    progress: ProductionProgress = ProductionProgress()
    # Required when item_type == "ship"; absent otherwise
    design_id: str | None = None
```

Semantics:

- `quantity` is the number of units still remaining to build for this queue entry
- `progress` applies to the **next unit currently under construction**
- When one unit completes:
  - the planet receives the completed structure immediately
  - `quantity -= 1`
  - `progress` resets to zero
- When `quantity` reaches `0`, the queue entry is removed automatically

### Global State — `PlanetState`

`PlanetState` is extended with:

```python
class PlanetState(BaseModel):
    # ... existing fields ...
    production_queue: list[ProductionQueueItem] = []
```

## Ship Designs

A ship design represents a player-authored ship configuration with a known cost. The design editor that lets players compose designs from hulls and components is a future PRD. For production purposes, a design has a fixed cost snapshot that the engine uses directly.

### Global State — `ShipDesign`

```python
class ShipDesignCost(BaseModel):
    resources: int
    ironium: int = 0
    boranium: int = 0
    germanium: int = 0

class ShipDesign(BaseModel):
    id: str
    owner: str  # player ID
    name: str
    cost: ShipDesignCost
```

Ship designs live in global state alongside fleets and planets.

### Immutability

Ship designs are immutable once created. Because a design's cost never changes, the engine reads it directly from the design at production resolution time — no cost snapshot is stored on the queue item.

### Designs API

Ship designs are managed outside the normal turn lifecycle. They are not submitted as turn commands and are not affected by turn resolution. A dedicated endpoint exposes current designs:

- `GET /games/{game_id}/designs` — returns all designs owned by the authenticated player

A future endpoint will allow creating new designs once a design editor exists.

### Preconditions for Ship Production

A planet may build ships only if:

- `planet.starbase` is not `null`
- `planet.starbase.can_build_ships == true`

See [PRD 17 — Starbases](17-starbases.md) for the starbase model.

## Command Model

Production uses explicit queue-edit commands rather than whole-queue replacement. This keeps queue item identities stable and avoids ambiguity around preserving partial progress.

### New Command Types

#### `add_production_item`

Add a new item anywhere in a planet's queue.

Mine or factory:

```json
{
  "type": "add_production_item",
  "planet_id": "PLk8m3x2",
  "item_type": "factory",
  "quantity": 5,
  "insert_after_item_id": null
}
```

Ship:

```json
{
  "type": "add_production_item",
  "planet_id": "PLk8m3x2",
  "item_type": "ship",
  "design_id": "SD7f2c1a",
  "quantity": 3,
  "insert_after_item_id": null
}
```

Rules:

- `insert_after_item_id = null` means insert at the top
- Otherwise insert immediately after the referenced queue item
- New queue items receive a server-generated queue item ID
- For `item_type = "ship"`, `design_id` is required and must reference an existing design owned by the player

#### `move_production_item`

Move an existing item to a new position.

```json
{
  "type": "move_production_item",
  "planet_id": "PLk8m3x2",
  "item_id": "PQ91ab3d",
  "insert_after_item_id": null
}
```

Rules:

- `insert_after_item_id = null` means move to the top
- Moving an item preserves its partial progress

#### `remove_production_item`

Remove units from a queue entry.

```json
{
  "type": "remove_production_item",
  "planet_id": "PLk8m3x2",
  "item_id": "PQ91ab3d",
  "quantity": 1
}
```

Rules:

- Removing fewer than the full quantity decrements `quantity`
- Removing the final remaining unit removes the queue entry entirely
- If the removed portion includes the partially completed unit, all progress on that unit is lost
- Spent resources and minerals are **not refunded**

#### `clear_production_queue`

Remove all items from a planet's queue.

```json
{
  "type": "clear_production_queue",
  "planet_id": "PLk8m3x2"
}
```

Rules:

- All partial progress on that planet is lost
- Spent resources and minerals are **not refunded**

### Command Validation

The server validates production commands before resolution:

- `planet_id` must reference a planet owned by the commanding player
- `item_type` must be a currently supported production type
- `quantity` must be a positive integer
- `item_id` and `insert_after_item_id` must reference queue items on that same planet
- Unowned planets cannot receive production commands
- Unknown production item types are rejected
- For `item_type = "ship"`:
  - `design_id` is required and must reference a design owned by the commanding player
  - The planet must have a starbase with `can_build_ships = true`

## Resolution Pipeline Changes

This PRD extends the turn pipeline described in [PRD 07 — Turn Mechanics](07-turn-mechanics.md) and [PRD 12 — Economy & Resources](12-economy-and-resources.md):

```text
Step 1: Apply commands
Step 2: Move fleets
Step 3: Mining
Step 4: Calculate resources
NEW -> Step 5: Production
Step 6: Increment turn counter
```

## Step 5: Production

Production runs once per owned planet, in **planet ID lexicographic order**.

For each planet:

1. Start with that turn's `available_resources` from PRD 12.
2. Process queue items from top to bottom.
3. Resolve as many units as possible on the current item before moving to the next item.
4. Stop when the queue is exhausted, or when the current item blocks further work.

### Blocking Rules

Queue items in this PRD are all **normal blocking items**:

- If the current item cannot make further progress because the planet lacks required minerals, production halts for the rest of the queue this turn.
- If the planet runs out of resources for the turn, production halts for the rest of the queue this turn.
- Later items are not considered once a blocking item halts production.

This matches the Stars! behaviour for ordinary queue items, without introducing auto-build skipping.

## Partial Progress

Normal production items may complete over multiple turns.

### Progress Representation

For the current unit of a queue entry, the engine tracks:

- `resources_spent`
- `minerals_spent` by type

These values persist in global state.

### Progress Rules

- Progress is attached to the queue entry, not the queue position
- Moving a partially completed item preserves its progress
- Inserting another item ahead of a partially completed item pauses work on the original item until it returns to the front
- Removing a partially completed item destroys all accumulated progress on that unit

## Spending Rules

Production spending must be deterministic and lossless with respect to totals.

### Per-Unit Cost

Each unit has:

- a resource cost
- zero or more mineral costs

Example:

- one `mine` unit costs `5` resources
- one `factory` unit costs `10` resources and `4` germanium

### How Work Advances

For the current unit of the current queue item:

1. Production advances in integer resource-work steps.
2. Mineral spend for that same unit is derived from total resource progress using the algorithm below.
3. The engine must never spend more than the full unit cost.
4. When the unit's full cost is paid, the unit completes immediately.

### Proportional Mineral Spend Algorithm

For each mineral type on the current unit:

```python
target_mineral_spent =
    floor(resources_spent * mineral_cost / resource_cost)
```

Where:

- `resources_spent` is the total resource progress already committed to the current unit, after applying the current increment
- `mineral_cost` is that unit's full cost for the mineral type
- `resource_cost` is that unit's full resource cost

The amount of that mineral to spend for the current increment is:

```python
mineral_delta =
    target_mineral_spent - minerals_spent_so_far
```

This is calculated independently for `ironium`, `boranium`, and `germanium`.

### Resolution Procedure Per Increment

For the current unit:

1. Let `remaining_resources = resource_cost - resources_spent`.
2. Let `resource_increment = min(available_resources, remaining_resources)`.
3. Compute the post-increment target mineral spend for each mineral type using:

```python
target[type] =
    floor((resources_spent + resource_increment) * mineral_cost[type] / resource_cost)
```

4. Compute the mineral deltas:

```python
delta[type] = target[type] - minerals_spent[type]
```

5. If the planet lacks any required `delta[type]`, reduce `resource_increment` until all mineral deltas are payable.
6. If no positive `resource_increment` is payable, the item is blocked and the rest of the queue does not run this turn.
7. Otherwise:
   - subtract `resource_increment` from `available_resources`
   - add `resource_increment` to `resources_spent`
   - subtract each `delta[type]` from `planet.minerals[type]`
   - add each `delta[type]` to `minerals_spent[type]`
8. If `resources_spent == resource_cost`, the unit completes.

### Choosing the Payable Increment

The engine should attempt to spend the **largest payable resource increment** for the current unit, up to the remaining resources available on the planet for that turn.

Reference implementation:

```python
resource_increment = min(available_resources, remaining_resources)

while resource_increment > 0:
    payable = True

    for each mineral type:
        target = floor((resources_spent + resource_increment) * mineral_cost[type] / resource_cost)
        delta = target - minerals_spent[type]
        if delta > planet.minerals[type]:
            payable = False
            break

    if payable:
        break

    resource_increment -= 1
```

This loop is deterministic, integer-only, and simple to test. It is acceptable here because initial production items are cheap and queue sizes are small.

### Invariants

This algorithm guarantees:

- `0 <= resources_spent <= resource_cost`
- `0 <= minerals_spent[type] <= mineral_cost[type]`
- `minerals_spent[type] == floor(resources_spent * mineral_cost[type] / resource_cost)` after every successful increment
- when `resources_spent == resource_cost`, then `minerals_spent[type] == mineral_cost[type]`
- mineral spend is monotonic and never refunded unless the item is removed, in which case progress is lost entirely

### Examples

#### Example 1: Factory with Full Minerals Available

Factory cost:

- `10` resources
- `4` germanium

Progress by resource spent:

| Resources Spent | Germanium Target |
|-----------------|------------------|
| 0 | 0 |
| 1 | 0 |
| 2 | 0 |
| 3 | 1 |
| 4 | 1 |
| 5 | 2 |
| 6 | 2 |
| 7 | 2 |
| 8 | 3 |
| 9 | 3 |
| 10 | 4 |

So if a planet spends `6` resources on a factory in one turn, the stored partial progress must be:

- `resources_spent = 6`
- `minerals_spent.germanium = 2`

#### Example 2: Factory Blocked by Germanium

Current unit progress:

- `resources_spent = 4`
- `minerals_spent.germanium = 1`

Planet has:

- `available_resources = 4`
- `available_germanium = 0`

Trying to spend all `4` resources would target:

```python
floor((4 + 4) * 4 / 10) = floor(3.2) = 3 germanium total
```

That would require `delta = 2` germanium, which is not payable.

Try smaller increments:

- increment `3` -> target `floor(7 * 4 / 10) = 2`, delta `1`, not payable
- increment `2` -> target `floor(6 * 4 / 10) = 2`, delta `1`, not payable
- increment `1` -> target `floor(5 * 4 / 10) = 2`, delta `1`, not payable

No positive increment is payable, so the queue blocks at this item for the turn.

Implementation requirements:

- The engine must use integer arithmetic only.
- The engine must compute mineral deltas from **total post-increment progress**, not from floating-point per-resource fractions.
- If the next increment of work would require minerals that are not available on the planet, production on that queue item stops immediately and the rest of the queue is blocked for the turn.

This keeps partial progress possible while still respecting mineral shortages.

## Completion Effects

When a unit completes during production resolution:

### Mine Completion

- `planet.mines += 1`

### Factory Completion

- `planet.factories += 1`

If the same queue entry still has remaining quantity after completion, production immediately continues onto the next unit of that same entry using any remaining resources for the turn.

### Ship Completion

When a ship unit completes, the engine adds it to a fleet at the planet:

1. Find all fleets currently located at the planet that are owned by the same player and contain at least one ship of the completed design.
2. If one or more such fleets exist, add the new ship to the one with the lexicographically smallest fleet ID.
3. If no such fleet exists, create a new fleet at the planet containing the single new ship.

If the same queue entry still has remaining quantity, production immediately continues onto the next unit using any remaining resources for the turn.

## Unused Resources

This PRD does **not** introduce research spending yet.

- Resources generated in Step 4 and not spent in Step 5 are discarded at end of turn
- The owner-visible player state may still show total resources for the planet that turn

Research allocation is a later PRD and should not be coupled to initial production implementation.

## Player State

Production queue details are owner-only information.

### Player State — `PlayerPlanet`

Add:

```python
class PlayerProductionQueueItem(BaseModel):
    id: str
    item_type: Literal["mine", "factory", "ship"]
    quantity: int
    progress: ProductionProgress
    design_id: str | None = None  # present when item_type == "ship"

class PlayerPlanet(BaseModel):
    # ... existing fields ...
    production_queue: list[PlayerProductionQueueItem] | None = None
```

Visibility:

- Owner: full production queue
- Non-owner: `production_queue = None`

## Events

Production uses the generic event envelope defined in [PRD 03](03-turn-lifecycle.md).

### Mine and factory completions — `production.completed`

`values`: `[planet_name, item_type, quantity]`

```json
{
  "owner": "tim",
  "source_id": "PLk8m3x2",
  "code": "production.completed",
  "values": ["Earth", "factory", 1]
}
```

### Ship completions — `production.ship_built`

`values`: `[planet_name, design_name, quantity]`

```json
{
  "owner": "tim",
  "source_id": "PLk8m3x2",
  "code": "production.ship_built",
  "values": ["Earth", "Scout", 1]
}
```

If multiple units of the same type complete on the same planet in the same turn, the engine may emit either:

- one event per completed unit, or
- one aggregated event with `quantity > 1`

The implementation should choose one form and keep it consistent.

## UI Notes

This PRD does not redefine layout from [PRD 08 — UI](08-ui.md), but it does constrain behaviour:

- The production panel should show one queue per selected planet
- Players must be able to add, remove, reorder, and clear queue items
- The UI should display partial progress on the currently building unit
- The UI should display whether the queue is blocked by resource shortage or mineral shortage
- Initial inventory for this phase needs `Mine`, `Factory`, and any ship designs owned by the player

## Future Extensions

Later PRDs may extend this system with:

- Ship design editor (hull selection and component fitting)
- Ship scrapping (mineral recovery)
- Starbases (see [PRD 17](17-starbases.md))
- Defences
- Terraforming tasks
- Auto-build items
- Production templates
- Default colony templates
- Tech-based production discounts
- Planetary contribution rules for research
