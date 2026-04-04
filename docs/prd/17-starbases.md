# PRD 17 — Starbases

## Overview

This document defines the first starbase system for OpenStars!. A starbase is an orbital installation attached to a colonised planet. It gates ship production, blocks bombing and invasion while it survives, and acts as the anchor point for later orbital systems such as stargates, mass drivers, scanners, and cloaks.

This PRD is intentionally narrow. It introduces:

- persistent starbase state on planets
- starbase construction and upgrade via the production queue
- explicit shipbuilding gating on colonised planets
- basic owner-visible and scanner-visible starbase data in player state

It does not yet introduce a starbase design editor, orbital component fitting, stargates, mass drivers, orbital scanners, cloaks, starbase combat load-outs, or fuel/refuelling behaviour.

---

## Design Philosophy

- **Planet-attached state**: a starbase belongs to exactly one planet and cannot exist independently.
- **Server authoritative**: clients choose what to build; the engine resolves construction and upgrades.
- **Faithful gating**: planets cannot build ships unless they have a starbase with shipbuilding capability.
- **Narrow first phase**: until a design editor exists, starbases are represented by a small server-defined set of buildable starbase types rather than player-authored designs.
- **Future-compatible**: the schema should grow cleanly into orbital modules, combat stats, cloaking, stargates, and mass drivers without a rewrite.

---

## Scope

### In Scope

- Starbase presence on owned planets
- One-starbase-per-planet rule
- Home-world starbase seeding at turn 0
- A small server-defined set of buildable starbase types
- Building a new starbase through the production queue
- Upgrading an existing starbase to another supported starbase type
- Basic owner-visible and scanner-visible starbase data in player state

### Explicitly Out of Scope

- Starbase design editor UI
- Custom starbase design creation or editing
- Orbital-slot components: stargates, mass drivers, orbital scanners, cloaks
- Fuel and automatic refuelling
- Starbase-vs-fleet combat behaviour and weapon statistics
- Bombing and invasion resolution details
- Alternate Reality population-on-starbase rules
- Race-trait-specific availability rules beyond reserving schema hooks
- Packet targeting and mass-driver routing
- Starbase repair numbers and combat damage modelling

Those features should be added by later PRDs rather than implied here.

---

## Core Rules

### What a Starbase Does

A starbase can provide up to five major functions in Stars!:

- shipyard
- fuel depot
- defensive station
- stargate platform
- mass-driver platform

This PRD implements only the first directly, while reserving room for the others later.

### One Starbase Per Planet

- A planet may have `0` or `1` starbase
- Uncolonised planets may not have a starbase
- If a planet is abandoned, its starbase is destroyed automatically
- A planet without a starbase cannot build ships

### Shipbuilding Requirement

A planet may add ship production items to its queue only if its current starbase type has shipbuilding capability.

For this phase, shipbuilding capability is a boolean on the starbase state rather than a full hull/design model.

---

## Supported Starbase Types

The full Stars! rules distinguish multiple starbase hull classes, but OpenStars does not yet have a starbase design editor. This PRD therefore uses a minimal server-defined type system.

### Phase 1 Buildable Types

| Type | Can Build Ships? | Intended Role |
|------|------------------|---------------|
| `orbital_fort` | No | Cheap defensive foothold |
| `space_station` | Yes | General-purpose shipyard |

These identifiers are chosen to stay close to the original game and leave room for later additions such as `space_dock`, `ultra_station`, and `death_star`.

### Future Expansion

When race traits and starbase design are implemented, later PRDs may add:

- `space_dock`
- `ultra_station`
- `death_star`

This PRD does not define player-facing rules for those types.

---

## Planet Starbase State

Each colonised planet gains optional starbase state:

```python
class PlanetStarbaseState(BaseModel):
    type: Literal["orbital_fort", "space_station"]
    can_build_ships: bool

class PlanetState(BaseModel):
    # ... existing fields ...
    starbase: PlanetStarbaseState | None = None
```

Semantics:

- `starbase = null` means the planet has no starbase
- `type` identifies the current server-defined starbase type
- `can_build_ships` determines whether ship production items may be queued on that planet

The explicit `can_build_ships` field is slightly redundant with `type`, but it keeps downstream resolution and player-state checks simple.

---

## Turn 0 Generation

Stars! home worlds begin with a shipbuilding starbase. OpenStars should now seed that explicitly.

### Turn 0 Rules

For each player:

1. Attach a `space_station` starbase to that player's home world
2. Set `can_build_ships = true`
3. Do not place starbases on any non-home planet at turn 0

This replaces any previous implicit assumption that a home world simply "can build ships" without a starbase object existing in state.

---

## Production Integration

This PRD extends [PRD 13 — Production](13-production.md).

### New Supported Production Item Type

Production gains a new normal blocking item type:

| Item Type | Completion Result |
|-----------|-------------------|
| `starbase` | Construct or upgrade the planet's starbase to the requested supported type |

Each `starbase` queue item references a target type:

```json
{
  "id": "PQ91ab3d",
  "item_type": "starbase",
  "target_type": "space_station",
  "quantity": 1,
  "progress": {
    "resources_spent": 0,
    "minerals_spent": { "ironium": 0, "boranium": 0, "germanium": 0 }
  }
}
```

Rules:

- `quantity` is always `1` for `starbase` items
- only one starbase item for a given planet may be active in the queue at a time
- the queue item is resolved as a normal blocking item with persistent partial progress

### Constructing a New Starbase

If `planet.starbase is null`, completing the queue item installs the requested starbase type as the planet's new starbase.

### Upgrading an Existing Starbase

If `planet.starbase` already exists and the target type differs, the queue item represents an upgrade.

Faithfulness rules carried over from the manual:

- a planet can have only one starbase at a time
- upgrading does not destroy and recreate the starbase as two separate entities
- upgrading pays only the applicable difference, not the full price of the target
- if the base type changes, the old base contributes only partial credit rather than full value

### Upgrade-Cost Rule

The original game has slot-by-slot upgrade accounting. OpenStars is not modelling starbase components yet, so this PRD adopts a simpler type-level rule that preserves the important strategic shape:

- upgrading to the same type is invalid and should be rejected
- changing from one supported type to another pays:
  - `target_cost - source_credit`
- `source_credit` is `50%` of the old starbase's total mineral/resource value

When a design editor and component fitting arrive, this rule should be replaced with proper slot-diff costing.

### Production Preconditions

The server rejects a `starbase` production item if any of the following is true:

- the planet is not owned by the commanding player
- the target type is not a supported starbase type
- the queue already contains another unfinished `starbase` item for that planet

---

## Visibility and Player State

This PRD extends [PRD 11 — Scanners](11-scanners.md) and the player-state response described in [PRD 50 — API](50-api.md).

### Own Planets

If the player owns the planet, `planet.starbase` is always fully visible.

### Scanned Enemy Planets

For non-owned planets:

- basic scan level may reveal only whether a starbase is present
- detailed scan level may reveal:
  - starbase presence
  - starbase type
  - whether it can build ships
  - whether a stargate or mass driver is present once those systems exist

### Player-State Shape

Example own planet:

```json
{
  "id": "PLk8m3x2",
  "name": "Sol",
  "owner": "tim",
  "starbase": {
    "type": "space_station",
    "can_build_ships": true
  }
}
```

Example scanned enemy planet:

```json
{
  "id": "PL4fn9v6",
  "name": "Rigel II",
  "owner": "matt",
  "scan_level": "detailed",
  "starbase": {
    "type": "orbital_fort",
    "can_build_ships": false
  }
}
```

### Report/UI Semantics

The frontend should preserve the original Stars! distinction:

- shipbuilding-capable starbase: yellow indicator
- non-shipbuilding starbase: blue indicator

Green and purple overlays for stargates and mass drivers remain future work.

---

## Events

Starbase actions should emit owner-visible events using the existing generic event envelope.

### `starbase.constructed`

Emitted when a planet completes construction of its first starbase.

Ordered `values`:

1. `planet_name`
2. `starbase_type`

### `starbase.upgraded`

Emitted when a planet completes an upgrade to a different starbase type.

Ordered `values`:

1. `planet_name`
2. `old_starbase_type`
3. `new_starbase_type`

These events are separate from the generic production event because they are strategically important and likely deserve dedicated UI treatment.

---

## Schema Changes Summary

### Global State

Add:

- `PlanetState.starbase: PlanetStarbaseState | None`

### Production Queue

Extend `ProductionQueueItem` with:

- `item_type: "starbase"` as a valid production type
- `target_type` for starbase items

### Player State

Expose starbase summary on planets according to ownership and scan level.

### Turn 0

Seed one shipbuilding starbase on each home world.

---

## Deferred Follow-Ups

- Starbase design editor
- Orbital components: stargates, mass drivers, orbital scanners, cloaks
- Exact slot-based upgrade costing
- Fuel and refuelling
- Starbase combat load-outs and damage
- Bombing/invasion blocking rules in combat resolution
- Alternate Reality population capacity and `Death Star` gameplay
- `Improved Starbases` trait effects

---

## Reference Notes

This PRD is based primarily on the extracted Stars! manual in:

- `docs/references/manual/chapters/06-planets.md`
- `docs/references/manual/chapters/09-ship-and-starbase-design.md`
- `docs/references/manual/chapters/17-scanning-and-cloaking.md`
- `docs/references/manual/chapters/20-designing-custom-races.md`
- `docs/references/manual/chapters/22-alternate-reality-races.md`
- `docs/references/original-order-of-events.md`

External cross-check:

- the Stars! Strategy Guide's discussion of `Improved Starbases`, used only as future context rather than current scope
