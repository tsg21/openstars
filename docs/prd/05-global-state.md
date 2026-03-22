# PRD 05 — Global State Schema

## Overview

This document defines the schema for `global-state-T{N}.yaml` — the server's authoritative representation of the entire game at a given turn. PRD 03 established the role of this file in the turn lifecycle; this PRD specifies what's in it.

The schema here covers **Phase 1** — the minimum needed to support galaxy generation, fleet movement, fog of war, and turn resolution. Sections will be extended as mechanics are added in later phases.

## Top-Level Structure

```yaml
# global-state-T{N}.yaml

game:
  seed: 987654321
  turn: 0
  next_id: 54

players:
  - username: tim
    name: The Gage Empire

designs:
  - id: DEa3f0p5
    owner: tim
    name: Long Range Scout
    hull: scout
    speed: 6
    scanner_range: 800

planets:
  - id: PLk8m3x2
    owner: null
    population: 0

fleets:
  - id: FL9qb7w1
    owner: tim
    position:
      x: 549755813888
      y: 549755813888
    composition:
      - design_id: DEa3f0p5
        count: 1
    waypoints:
      - x: 550148141952
        y: 549755867136
```

## Sections

### `game`

Top-level game metadata.

| Field     | Type    | Description |
|-----------|---------|-------------|
| `seed`    | integer | Game seed for deterministic RNG (PRD 04). Secret — never included in player state. |
| `turn`    | integer | Current turn number, zero-indexed. |
| `next_id` | integer | Next value for the entity ID counter (PRD 04). Used to allocate base36 IDs for new entities. |

Galaxy-level metadata (size, galaxy seed, planet positions/names) lives in `galaxy.yaml` (PRD 02) and is not duplicated here. The server loads both files — the galaxy definition is static, the global state evolves each turn.

### `players`

List of players in the game.

| Field      | Type   | Description |
|------------|--------|-------------|
| `username` | string | Unique player identifier — login/account name. Used as the owner reference throughout the game state. |
| `name`     | string | In-game empire/race name, displayed in the UI. |

Players are identified by `username`, not by a generated ID. All `owner` fields in other sections reference this value. In the future, usernames may be email addresses (Google Auth).

Phase 1 keeps players minimal. Future phases will add race traits, research levels, diplomacy state, and other per-player data.

### `designs`

Ship design registry. Every ship in the game is an instance of a design. Designs are defined here; fleets reference them by `design_id`.

| Field           | Type    | Description |
|-----------------|---------|-------------|
| `id`            | string  | Entity ID with `DE` prefix (PRD 04). |
| `owner`         | string  | Username of the player who owns this design. |
| `name`          | string  | Display name (e.g. "Long Range Scout"). |
| `hull`          | string  | Hull type identifier. Phase 1 has only `scout`. |
| `speed`         | integer | Maximum warp speed — distance units per turn. |
| `scanner_range` | integer | Scanner radius in distance units. 0 if the design has no scanner. |

In Phase 1, there is a single pre-defined design per player: a scout with a scanner. The ship designer is a future phase — for now, designs are generated at game creation and are immutable.

Future additions: components, fuel capacity, armour, weapons, cost, mass.

### `planets`

Planet state that changes over the course of the game. Each entry corresponds to a planet defined in `galaxy.yaml`, linked by `id`.

| Field        | Type        | Description |
|--------------|-------------|-------------|
| `id`         | string      | Entity ID with `PL` prefix (PRD 04). Matches the planet's `id` in `galaxy.yaml`. |
| `owner`      | string/null | Username of the player who controls this planet, or `null` if uncolonised. |
| `population` | integer     | Current population. 0 for uncolonised planets. |

Static planet properties (name, coordinates) are read from `galaxy.yaml` and not repeated here. This avoids duplication and keeps the global state focused on mutable game data.

Phase 1: home planets start with an owner and initial population. All other planets start uncolonised.

Future additions: scanner range, mineral concentrations, mineral surface deposits, factories, mines, defences, environment values, production queue.

### `fleets`

All fleets in the game.

| Field         | Type   | Description |
|---------------|--------|-------------|
| `id`          | string | Entity ID with `FL` prefix (PRD 04). |
| `owner`       | string | Username of the player who owns this fleet. |
| `position`    | object | Current location (see below). |
| `composition` | list   | Ships in the fleet (see below). |
| `waypoints`   | list   | Ordered destinations (see below). Empty if the fleet is idle/stationary. |

#### `position`

| Field | Type    | Description |
|-------|---------|-------------|
| `x`   | integer | Current x coordinate. |
| `y`   | integer | Current y coordinate. |

#### `composition` entries

| Field       | Type    | Description |
|-------------|---------|-------------|
| `design_id` | string  | Entity ID with `DE` prefix, referencing a design in the `designs` section. |
| `count`     | integer | Number of ships of this design in the fleet. |

#### `waypoints` entries

| Field | Type    | Description |
|-------|---------|-------------|
| `x`   | integer | Destination x coordinate. |
| `y`   | integer | Destination y coordinate. |

Waypoints are processed in order. When a fleet reaches the first waypoint, it is removed from the list and the fleet proceeds to the next. An empty waypoint list means the fleet is stationary.

Fleet movement each turn: the fleet moves toward its first waypoint at the speed of its slowest ship design, up to a maximum of `speed` distance units per turn. The fleet's `position` is updated to its new location. If the fleet reaches the waypoint exactly, it is consumed and the fleet may continue toward the next waypoint with any remaining movement.

## Relationship to `galaxy.yaml`

The global state deliberately does **not** duplicate static galaxy data. The server holds both files in memory:

- **`galaxy.yaml`** — immutable: planet names, coordinates, galaxy size, galaxy seed
- **`global-state-T{N}.yaml`** — mutable: everything that changes turn-to-turn

Planets are linked by `id` — each planet in `galaxy.yaml` has a unique `PL`-prefixed base36 `id` (see PRD 02), and the global state references the same IDs.

## Turn 0 Generation

When a new game is created, the server generates `global-state-T0.yaml`:

1. Create player entries from the game lobby/configuration
2. Assign each player a home planet (selection algorithm TBD — likely spread evenly across the galaxy)
3. Set home planet ownership and initial population
4. Create one scout fleet per player at their home planet
5. Create one scout design per player in the design registry
6. All other planets start uncolonised (`owner: null`, `population: 0`)

Planet IDs are allocated during galaxy generation. Design and fleet IDs are allocated during turn 0 setup. The `next_id` counter in the game section reflects the total number of IDs allocated.

## Example: Turn 0 (2-Player Small Galaxy)

```yaml
game:
  seed: 987654321
  turn: 0
  next_id: 54

players:
  - username: tim
    name: The Gage Empire
  - username: sara
    name: The Hive

designs:
  - id: DEa3f0p5
    owner: tim
    name: Scout
    hull: scout
    speed: 6
    scanner_range: 800
  - id: DE7xw2m9
    owner: sara
    name: Scout
    hull: scout
    speed: 6
    scanner_range: 800

planets:
  - id: PLk8m3x2
    owner: tim
    population: 25000
  - id: PL4fn9v6
    owner: null
    population: 0
  - id: PLr2j5b8
    owner: null
    population: 0
  # ... (remaining planets omitted)
  - id: PLw1c6q3
    owner: sara
    population: 25000

fleets:
  - id: FL9qb7w1
    owner: tim
    position:
      x: 549755813888
      y: 549755813888
    composition:
      - design_id: DEa3f0p5
        count: 1
    waypoints: []
  - id: FLp4h8e2
    owner: sara
    position:
      x: 552952127488
      y: 551903297536
    composition:
      - design_id: DE7xw2m9
        count: 1
    waypoints: []
```

## What's Out of Scope

- **Ship designer** — designs are pre-generated in Phase 1. Player-created designs come later.
- **Economy fields** — minerals, factories, mines, production queues are future phases.
- **Race/trait system** — player differentiation beyond naming is a future phase.
- **Research and technology** — future phase.
- **Fuel and cargo** — future phase.
- **Detailed movement rules** — Phase 1 uses simple distance-per-turn movement. Fuel consumption, stargates, and wormholes come later.
