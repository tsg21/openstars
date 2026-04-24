# PRD 21 — Research & Technology

## Overview

This document defines the research system for OpenStars! — the mechanism by which players progress along six fields of technology, unlock new components and hulls, and reduce the cost of items they already know how to build.

The model follows the original Stars! game closely:

- Six independent fields of study.
- Each field has discrete integer levels from `0` to `26`.
- Each planet contributes resources to research every turn, either as a fixed allocation or as leftovers from the production queue.
- Reaching new levels unlocks components/hulls and discounts existing ones (miniaturisation).

This PRD owns the research simulation layer: per-player tech state, the cost formula, the resolution step, how resources flow into research, and how the component catalogue expresses tech prerequisites.

---

## Design Philosophy

- **Faithful mechanics**: the model reproduces the central Stars! loop of "choose a field, spend resources, unlock tech, miniaturise existing tech" without simplifying it away.
- **Server authoritative**: the engine computes all tech progression and unlock decisions. Clients only edit research intent.
- **Deterministic**: given the same state and commands, research resolves identically every time. No RNG in the MVP.
- **Unlocks expressed in data**: tech prerequisites live in the component catalogue (PRD 20), not in code. Adding new components does not require engine changes.
- **Race-neutral MVP**: without races, every player uses a single standard cost profile. The schema reserves a seat for per-field cost multipliers so races can slot in later.

---

## Scope

### In Scope

- Six-field tech model (`energy`, `weapons`, `propulsion`, `construction`, `electronics`, `biotechnology`).
- Integer tech levels `0..26`, per player, per field.
- Persistent partial progress (stored resource points) within a field.
- Per-player research allocation: the current field, a `next field` that fires on level-up, and a global percentage of planetary resources diverted to research.
- Per-planet `contribute_only_leftover_to_research` toggle, matching the original game.
- A single deterministic research cost formula (Fibonacci base + total-levels penalty).
- Tech prerequisites on components via added fields in the PRD 20 catalogue.
- Miniaturisation — per-level discount applied when a player exceeds every required level of a component/hull.
- Research events (`research.level_up`).
- Commands: `set_research`, `set_planet_production_mode`.
- New resolution step: Research (after Production).

### Explicitly Out of Scope

- Race-trait modifiers for research (cheap/expensive fields, `Generalized Research`, `Bleeding Edge`, JOAT scanner auto-upgrade).
- Tech trading with allied players.
- Tech stealing from destroyed ships, scrapped givers, or captured planets.
- Espionage (`SS` racial).
- Mystery Trader tech gifts.
- Artifact planet bonuses.
- Auto-selection of the least-researched field when the player forgets a next-field.
- Automatic upgrade of deployed components/hulls in existing fleets when tech advances (designs remain immutable — PRD 18).
- Hull-level tech prerequisites beyond `construction` (deferred until hull catalogue is populated with non-zero prereqs).
- UI layout for the research dialog.

Those features remain backlog items and should not be implied by this PRD.

---

## The Six Fields

| Field | ID | Typical Unlocks |
|-------|-----|-----------------|
| Energy | `energy` | Shields, planetary shields, energy capacitors, jammers |
| Weapons | `weapons` | Beams, torpedoes, missiles, bombs |
| Propulsion | `propulsion` | Engines, maneuvering jets, overthrusters |
| Construction | `construction` | Hulls (ships and starbases), armour, cargo pods, fuel tanks, mine layers |
| Electronics | `electronics` | Scanners, cloaks, battle computers, planetary scanner tiers |
| Biotechnology | `biotechnology` | Terraforming modules, bio-scanners, smart bombs, organic armour |

Each field has **27 discrete levels** — `0` through `26` inclusive. Level `0` is the starting value; `26` is the maximum.

A player may research only one field at a time.

---

## Player Tech State

Each player gains a per-player `research_state` record:

| Field | Type | Description |
|-------|------|-------------|
| `levels` | object | Current integer level for each of the six fields. Range `0..26`. |
| `progress` | object | Accumulated research points towards the next level in each field. Keyed by field ID; each value is a non-negative integer. Progress is retained per field — switching fields does not discard it. |
| `current_field` | string | The field currently being researched. One of the six field IDs. |
| `next_field` | string \| null | Optional field to switch to when `current_field` levels up. When the current field levels up, any leftover research points from that level-up are applied to `next_field`'s progress (see "Research Resolution"). `null` means "stay on the same field after level-up". |
| `allocation_percent` | integer | `0..100`. Percentage of each planet's total resources routed to research by default. |

Example:

```json
{
  "research_state": {
    "levels": {
      "energy": 0,
      "weapons": 0,
      "propulsion": 0,
      "construction": 0,
      "electronics": 0,
      "biotechnology": 0
    },
    "progress": {
      "energy": 0,
      "weapons": 0,
      "propulsion": 0,
      "construction": 0,
      "electronics": 0,
      "biotechnology": 0
    },
    "current_field": "propulsion",
    "next_field": "electronics",
    "allocation_percent": 15
  }
}
```

`progress` is always measured in whole integer resource points. Each field's progress is retained independently — switching `current_field` through a `set_research` command does **not** discard progress in either the old or new field. A field's progress is reset to `0` only when that field levels up.

All field IDs use the canonical strings listed in "The Six Fields".

---

## Per-Planet Research Mode

Each owned planet carries a small research-related toggle (added to `PlanetState`):

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `contribute_only_leftover_to_research` | boolean | `false` | When `true`, the planet does not send the default `allocation_percent` share to research. Only resources left unspent after production flow to research. |

This mirrors the `Contribute Only Leftover Resources to Research` checkbox in the original Stars! production dialog.

Semantics per planet per turn:

- If `contribute_only_leftover_to_research == false`:
  - `research_contribution = floor(total_resources * allocation_percent / 100)` is **reserved** for research and unavailable to production.
  - `production_budget = total_resources - research_contribution`.
  - Any resources left after the production queue halts are also contributed to research.
- If `contribute_only_leftover_to_research == true`:
  - `research_contribution` starts at `0`.
  - The full `total_resources` is available to the production queue.
  - Whatever the queue leaves unspent at end of turn is contributed to research.

In both cases, the planet's contribution to research is the sum of the reserved allocation (if any) plus any end-of-turn production leftovers.

---

## Research Cost Formula

The cost to advance `current_field` from level `L` to `L+1` is:

```
cost(L, total_levels) = base_cost(L) + 10 * total_levels
```

Where:

- `L` is the player's current integer level in `current_field` (value before levelling up).
- `total_levels` is the sum of the player's levels across all six fields **before** this level-up, i.e. `sum(research_state.levels.values())`.
- `base_cost(L)` is defined from the table below.

### Base Cost Table (Standard Profile)

| `L` (current) | `base_cost(L → L+1)` |
|----|----------|
| 0 | 50 |
| 1 | 80 |
| 2 | 130 |
| 3 | 210 |
| 4 | 340 |
| 5 | 550 |
| 6 | 890 |
| 7 | 1,440 |
| 8 | 2,330 |
| 9 | 3,770 |
| 10 | 6,100 |
| 11 | 9,870 |
| 12 | 15,970 |
| 13 | 25,840 |
| 14 | 41,810 |
| 15 | 67,650 |
| 16 | 109,460 |
| 17 | 177,110 |
| 18 | 286,570 |
| 19 | 463,680 |
| 20 | 750,250 |
| 21 | 1,213,930 |
| 22 | 1,964,180 |
| 23 | 3,178,110 |
| 24 | 5,142,290 |
| 25 | 8,320,400 |

`base_cost(L)` follows a Fibonacci-shaped progression consistent with the Stars! manual:

```
base_cost(0) = 50
base_cost(1) = 80
base_cost(L) = base_cost(L-1) + base_cost(L-2)   for L >= 2
```

Level `26` is the cap — once a player reaches level `26` in a field, no further progress or cost applies in that field.

### Why This Formula

- The Fibonacci base replicates the steep super-linear progression described in the manual ("increasing in a Fibonacci-type series").
- The `+10 * total_levels` penalty encodes the manual's rule that each already-achieved level adds `10` resources to the next level-up cost in every field, pushing players to specialise rather than research everything.
- The table is the authoritative source of truth — stored as a constant in the engine. Future race-trait work will introduce per-field cost multipliers layered on top of this.

---

## Resolution Pipeline

This PRD extends the turn pipeline defined in [PRD 07 — Turn Mechanics](07-turn-mechanics.md), [PRD 12 — Economy & Resources](12-economy-and-resources.md), and [PRD 13 — Production](13-production.md).

```text
Step 1: Apply commands
Step 2: Move fleets
Step 3: Mining
Step 4: Calculate resources
Step 5: Production
NEW -> Step 6: Research
Step 7: Combat
Step 8: Increment turn counter
```

Research runs after production so the manual's "leftover resources" rule can sweep up resources that production could not spend.

### Step 6: Research

For each player, in **alphabetical username order** (for determinism):

1. Initialise `research_points = 0` for the player.
2. For each planet owned by that player, in **planet ID lexicographic order**:
   a. Let `reserved = planet.research_reserved_this_turn` (calculated in Step 4 and pre-subtracted from the production budget).
   b. Let `leftover = planet.available_resources_after_production` (resources that production did not spend this turn).
   c. `research_points += reserved + leftover`.
3. Apply `research_points` to the player's current field using the "Research Resolution" procedure below.
4. Emit any `research.level_up` events that fire during this application.

Processing a given player does not affect other players' research, since each player's planets are disjoint.

### Research Resolution Procedure

Given a player with `current_field`, `progress` (per-field), `levels`, and an incoming `research_points` value:

1. If `levels[current_field] == 26`:
   - If `next_field` is set and `next_field != current_field` and `levels[next_field] < 26`:
     - Switch: `current_field = next_field`, `next_field = null`. Retained progress on the newly selected field (if any) is preserved.
   - Else: the player is at the cap with nowhere to go. All incoming `research_points` are discarded for the turn.
2. Otherwise, repeat until `research_points == 0` or the player is fully capped:
   a. Let `L = levels[current_field]`.
   b. Let `total = sum(levels.values())`.
   c. Let `cost = base_cost(L) + 10 * total`.
   d. Let `needed = cost - progress[current_field]`.
   e. If `research_points < needed`:
      - `progress[current_field] += research_points`
      - `research_points = 0`
      - stop.
   f. Else:
      - `research_points -= needed`
      - `levels[current_field] = L + 1`
      - `progress[current_field] = 0`
      - Emit `research.level_up` for the owner with the new level.
      - If `next_field` is set and `next_field != current_field`:
        - `current_field = next_field`
        - `next_field = null`
        - Any remaining `research_points` now feed into `current_field`'s existing `progress[current_field]`.
      - If `levels[current_field] == 26` and no viable next field is set, discard any remaining `research_points` and stop.

This loop handles the Stars! case where a single planet-rich turn levels a field up multiple times.

### Switching Fields Mid-Turn

If a `set_research` command changes `current_field` during Step 1 (command application):

- The outgoing field retains its own `progress[field]` value.
- The incoming field resumes from whatever `progress[field]` it already holds (typically `0` if never researched, or a non-zero value if the player had partially researched it before).
- No progress is transferred between fields. This matches the manual ("Stars! keeps track of how much progress you have made in a field, allowing you to return to a partially researched field later without losing progress") directly — each field's partial progress is held in place until that field itself levels up.

---

## Component Catalogue Changes (PRD 20 extension)

Each component entry in the YAML catalogue gains an optional `tech` block:

```yaml
- id: scoper_150
  name: Scoper 150
  component_type: scanner
  slot_type: scanner
  cost:
    resources: 100
    ironium: 10
    boranium: 10
    germanium: 70
  mass: 2
  tech:
    energy: 0
    weapons: 0
    propulsion: 0
    construction: 0
    electronics: 3
    biotechnology: 0
  scanner:
    normal: 150
    penetrating: 0
```

### Rules

- `tech` is a **dictionary of field id → required integer level**. Any omitted field defaults to `0`.
- A player may reference a `component_id` in a ship design only if `player.research_state.levels[f] >= tech[f]` for every field `f`.
- Hulls get the same treatment — [PRD 19 — Hull Slot Definitions](19-hull-slot-definitions.md) is extended with an optional `tech` block per hull entry using the same structure.
- Backend loads the catalogue eagerly on startup (PRD 20). Validation rejects any non-integer value or any value outside `0..26`.

### Availability in the Designer

`POST /api/v1/games/{game_id}/designs` validates tech prerequisites before creating a design:

- The server rejects the design with `400` if any assigned component or the chosen hull requires a level the player has not reached.
- The error code is `TECH_LOCKED`; the error `message` names the specific component/hull and the first unmet field.

### Availability in the Production Queue

A planet may queue a ship that references a design whose components/hull require tech levels the player has not yet reached — the design itself was created at a point when the player had those levels. Designs are immutable (PRD 18), so production consults only the cost recorded on the design at creation time.

The player cannot newly **create** a design they haven't yet researched, but any design already owned continues to be buildable.

---

## Miniaturisation

When a player exceeds every required tech level of a component or hull, the cost of producing that item is reduced.

### Formula

For a catalogue entry with `tech` prerequisites `tech_req`, and a player with `levels`:

```
excess = min(
  26 - max(tech_req.values(), default=0),
  min(levels[f] - tech_req[f] for f in FIELDS)
)
```

Translation:

- For each field, compute the player's surplus levels over the requirement.
- The item's effective miniaturisation level is the **minimum** of those surpluses (the component is only as miniaturised as its tightest unmet margin allows).
- A component with no prerequisites has `tech_req[f] = 0` for every field, so its miniaturisation equals the player's **lowest** tech level across all six fields — matching the manual's Space Station example.

Then:

```
discount = min(excess, 19) * 0.04
```

- Discount is capped at `19 * 0.04 = 0.76`, which rounds to the classic `75%` cap.
- Minimum discounted cost is `25%` of original.
- Discount applies uniformly to `resources`, `ironium`, `boranium`, and `germanium`.

Rounding: compute the raw discounted cost as a float, then `round half to even` to the nearest integer per cost field, then clamp to `>= 1` for any non-zero original cost field (so miniaturisation never drives a non-zero cost to `0`).

### When Miniaturisation Is Evaluated

- **At design creation**: `POST /api/v1/games/{game_id}/designs` computes the miniaturised cost using the player's tech state at the moment of design creation. The resulting cost is stored on the immutable design (PRD 18) and never recomputed.
- **At planetary installation cost**: the planetary scanner cost in PRD 13 is constant regardless of tech and is **not** subject to miniaturisation (the manual notes the planetary scanner auto-upgrades to the best available type with no additional cost).
- **Starbase construction cost**: not subject to miniaturisation in the MVP — the starbase model in PRD 17 uses type-level costs rather than a catalogue-driven design. Miniaturisation will apply to starbases once the starbase design editor lands.

### Rationale

This PRD uses the non-BET standard rule (`4%` per level, `75%` cap). The Bleeding Edge Technology trait (`5%` per level, `80%` cap) is not in scope until races land.

---

## Commands

### `set_research`

Update the player's research allocation.

```json
{
  "type": "set_research",
  "current_field": "propulsion",
  "next_field": "electronics",
  "allocation_percent": 15
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `current_field` | string | no | Field to research now. If omitted, `current_field` is unchanged. |
| `next_field` | string \| null | no | Field to switch to on level-up. `null` clears the setting. If the key is absent from the payload, `next_field` is unchanged. |
| `allocation_percent` | integer | no | `0..100`. If omitted, unchanged. |

Validation:

- Any provided field must be one of the six canonical field IDs.
- `allocation_percent` must be `0..100`.
- `current_field` and `next_field` may be different or equal. If equal, the next-field queue is effectively empty and is reset to `null` at apply time.
- A player may submit multiple `set_research` commands per turn; later commands overwrite earlier values in that turn's file, consistent with the general command-application model (PRD 07).

### `set_planet_production_mode`

Toggle whether a planet uses the "leftover only" contribution rule.

```json
{
  "type": "set_planet_production_mode",
  "planet_id": "PLk8m3x2",
  "contribute_only_leftover_to_research": true
}
```

Validation:

- `planet_id` must reference a planet owned by the commanding player.
- Unknown planets are rejected.

### Command Validation Summary

Standard validation rules (PRD 07) apply. Command-specific rejections return `400` with a descriptive error code — `RESEARCH_FIELD_UNKNOWN`, `RESEARCH_ALLOCATION_OUT_OF_RANGE`, `PLANET_NOT_OWNED`, etc.

---

## Player State

`PlayerState` gains the player's research view:

```json
{
  "research": {
    "levels": {
      "energy": 2,
      "weapons": 0,
      "propulsion": 4,
      "construction": 1,
      "electronics": 3,
      "biotechnology": 0
    },
    "progress": {
      "energy": 40,
      "weapons": 0,
      "propulsion": 210,
      "construction": 0,
      "electronics": 95,
      "biotechnology": 0
    },
    "current_field": "propulsion",
    "next_field": "electronics",
    "allocation_percent": 15,
    "cost_to_next_level": 2050,
    "estimated_resources_this_turn": 412
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `levels` | object | Current integer level in each field. |
| `progress` | object | Points towards the next level in each field, keyed by field ID. Each value is a non-negative integer. |
| `current_field` | string | Actively researched field. |
| `next_field` | string \| null | Queued next field, if any. |
| `allocation_percent` | integer | Player's global research allocation. |
| `cost_to_next_level` | integer | Convenience field: `base_cost(level) + 10 * sum(levels)` for the current field. |
| `estimated_resources_this_turn` | integer | Convenience field: projected research contribution across all owned planets this turn, computed from last turn's `total_resources` on each planet and the current allocation settings. Purely a UI aid. |

### Own Planets

Each `PlayerPlanet` for an owned planet exposes:

- `contribute_only_leftover_to_research: bool` — the current per-planet toggle.

Non-owners never see this field.

### Visibility

- `research` is always present on a `PlayerState` and reflects the viewing player's own tech state only. Other players' research is not disclosed.
- The list of components/hulls available to a player is derivable from `levels` + the public catalogue, so the API does not duplicate an "unlocked components" list in `PlayerState`. The frontend filters the catalogue using the player's tech levels.

---

## Events

### `research.level_up`

Emitted each time a player levels a field during Step 6.

| Field | Value |
|-------|-------|
| `source_id` | `null` |
| `values[0]` | `field_id` (one of the six canonical IDs) |
| `values[1]` | `new_level` (integer) |

```json
{
  "owner": "tim",
  "source_id": null,
  "code": "research.level_up",
  "values": ["propulsion", 5]
}
```

Multiple level-ups in a single turn emit multiple events in the order they occur.

### Event Registry

PRD 51 — Event Codes is extended with the entry above. No other existing event codes change.

---

## Turn 0 Generation

When a new game is created (PRD 05 Turn 0 generation), each player gets a default research state:

- `levels`: all six fields at `0`.
- `progress`: all six fields at `0`.
- `current_field`: `"energy"` (canonical default; deterministic and irrelevant when all fields are at `0`).
- `next_field`: `null`.
- `allocation_percent`: `15` (a reasonable starting value — mirrors the initial slider position from the original game's "balanced" tutorial setup).

Each owned planet at turn 0 has `contribute_only_leftover_to_research = false`.

---

## Schema Changes Summary

### Global State

- `Player` gains `research_state: PlayerResearchState` with fields listed in "Player Tech State".
- `PlanetState` gains `contribute_only_leftover_to_research: bool` (default `false`).

### Player State

- `PlayerState` gains `research: PlayerStateResearch` (fields listed in "Player State").
- `PlayerPlanet` for own planets gains `contribute_only_leftover_to_research: bool`.

### Commands

- New command types: `set_research`, `set_planet_production_mode`.

### Component / Hull Catalogues

- PRD 19 hull entries gain an optional `tech` field.
- PRD 20 component entries gain an optional `tech` field.

### Events

- New event code: `research.level_up`.

---

## Migration Notes

State files at `state_version: 1` predate this PRD. When loading an older global-state blob:

- Missing `research_state` on a player is filled with the turn-0 defaults above.
- Missing `contribute_only_leftover_to_research` on a planet is treated as `false`.

These defaults keep old games loadable without a schema bump; a formal `state_version: 2` bump is not required for this change alone but would be a natural batch moment.

---

## Deferred Follow-ups

- Race-trait cost multipliers per field (`0.5`, `1.0`, `1.75`).
- `Generalized Research` racial (50% to current, 15% to each other).
- `Bleeding Edge Technology` miniaturisation profile (`5%` per level, `80%` cap).
- Auto-selection of the least-researched field when `next_field` is not set and the current field caps.
- Tech trading with allies via diplomacy messages.
- Tech acquisition from destroyed enemy ships, scrapped givers, captured planets.
- `SS` espionage (receive fraction of rivals' research each turn).
- Mystery Trader and Artifact planet tech bonuses.
- Miniaturisation for starbase types (once the starbase design editor lands).
- UI layout for the Research dialog, cost breakdown, and Technology Browser.
- Planetary-scanner auto-upgrade visibility signalling in the UI (the mechanic already exists in PRD 11; this PRD does not change it).

---

## Reference Notes

Primary sources used for this PRD:

- `docs/references/manual/chapters/08-research.md` — fields, Fibonacci cost shape, leftover-only toggle, next field dropdown, miniaturisation ceiling.
- `docs/references/manual/chapters/appendix-b-technology-tables.md` — per-component/hull tech prerequisites, used to guide the catalogue extension shape.
- `docs/references/manual/chapters/appendix-d-frequently-asked-questions.md` — Fibonacci definition.
- `docs/references/elite-games-ru-en/translated-markdown/science.md` — miniaturisation worked examples (Battleship, Jihad missile, Space Station).
- `docs/references/elite-games-ru-en/translated-markdown/race/science.md` — cost-profile semantics reserved for future race work.
- `docs/references/stars-resolution-order.md` / `original-order-of-events.md` — placement of research inside the production step, confirming "Step 6" positioning after mining/production.
