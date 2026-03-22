# PRD 05 — Global State Schema

## Overview

This document defines the schema for `global-state-T{N}.yaml` — the server's authoritative representation of the entire game at a given turn. PRD 03 established the role of this file in the turn lifecycle; this PRD specifies what's in it.

The schema here covers **Phase 1** — the minimum needed to support galaxy generation, fleet movement, fog of war, and turn resolution. Sections will be extended as mechanics are added in later phases.

## Top-Level Structure

```yaml
# global-state-T{N}.yaml

game:
  seed: 987654321             # game seed — secret, never exposed to players (PRD 04)
  turn: 0                     # current turn number

players:
  - id: 1
    username: "tim"
    name: "The Gage Empire"

designs:
  - id: 1
    owner: 1
    name: "Long Range Scout"
    hull: "scout"
    speed: 6                  # distance units per turn
    scanner_range: 800        # distance units

stars:
  - id: 1
    owner: null               # player id, or null if uncolonised
    population: 0             # integer — 0 for uncolonised

fleets:
  - id: 1
    owner: 1
    position:
      x: 549755813888
      y: 549755813888
    composition:
      - design_id: 1
        count: 1
    waypoints:                # ordered list of destinations — empty if idle
      - x: 550148141952
        y: 549755867136
```

## Sections

### `game`

Top-level game metadata.

| Field  | Type    | Description |
|--------|---------|-------------|
| `seed` | integer | Game seed for deterministic RNG (PRD 04). Secret — never included in player state. |
| `turn` | integer | Current turn number, zero-indexed. |

Galaxy-level metadata (size, galaxy seed, star positions/names) lives in `galaxy.yaml` (PRD 02) and is not duplicated here. The server loads both files — the galaxy definition is static, the global state evolves each turn.

### `players`

List of players in the game.

| Field      | Type    | Description |
|------------|---------|-------------|
| `id`       | integer | Unique player identifier, assigned at game creation. Stable across turns. |
| `username` | string  | Login/account name. |
| `name`     | string  | In-game empire/race name, displayed in the UI. |

Phase 1 keeps players minimal. Future phases will add race traits, research levels, diplomacy state, and other per-player data.

### `designs`

Ship design registry. Every ship in the game is an instance of a design. Designs are defined here; fleets reference them by `design_id`.

| Field           | Type    | Description |
|-----------------|---------|-------------|
| `id`            | integer | Unique design identifier. |
| `owner`         | integer | Player who owns this design. |
| `name`          | string  | Display name (e.g. "Long Range Scout"). |
| `hull`          | string  | Hull type identifier. Phase 1 has only `"scout"`. |
| `speed`         | integer | Maximum warp speed — distance units per turn. |
| `scanner_range` | integer | Scanner radius in distance units. 0 if the design has no scanner. |

In Phase 1, there is a single pre-defined design per player: a scout with a scanner. The ship designer is a future phase — for now, designs are generated at game creation and are immutable.

Future additions: components, fuel capacity, armour, weapons, cost, mass.

### `stars`

Star state that changes over the course of the game. Each entry corresponds to a star defined in `galaxy.yaml`, linked by `id`.

| Field        | Type         | Description |
|--------------|--------------|-------------|
| `id`         | integer      | Matches the star's `id` in `galaxy.yaml`. |
| `owner`      | integer/null | Player who controls this star, or `null` if uncolonised. |
| `population` | integer      | Current population. 0 for uncolonised stars. |

Static star properties (name, coordinates) are read from `galaxy.yaml` and not repeated here. This avoids duplication and keeps the global state focused on mutable game data.

Phase 1: home stars start with an owner and initial population. All other stars start uncolonised.

Future additions: scanner range, mineral concentrations, mineral surface deposits, factories, mines, defences, environment values, production queue.

### `fleets`

All fleets in the game.

| Field         | Type    | Description |
|---------------|---------|-------------|
| `id`          | integer | Unique fleet identifier. |
| `owner`       | integer | Player who owns this fleet. |
| `position`    | object  | Current location (see below). |
| `composition` | list    | Ships in the fleet (see below). |
| `waypoints`   | list    | Ordered destinations (see below). Empty if the fleet is idle/stationary. |

#### `position`

| Field | Type    | Description |
|-------|---------|-------------|
| `x`   | integer | Current x coordinate. |
| `y`   | integer | Current y coordinate. |

#### `composition` entries

| Field       | Type    | Description |
|-------------|---------|-------------|
| `design_id` | integer | References a design in the `designs` section. |
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

- **`galaxy.yaml`** — immutable: star names, coordinates, galaxy size, galaxy seed
- **`global-state-T{N}.yaml`** — mutable: everything that changes turn-to-turn

Stars are linked by `id` — each star in `galaxy.yaml` has a unique integer `id` (see PRD 02), and the global state references the same IDs.

## Turn 0 Generation

When a new game is created, the server generates `global-state-T0.yaml`:

1. Create player entries from the game lobby/configuration
2. Assign each player a home star (selection algorithm TBD — likely spread evenly across the galaxy)
3. Set home star ownership and initial population
4. Create one scout fleet per player at their home star
5. Create one scout design per player in the design registry
6. All other stars start uncolonised (`owner: null`, `population: 0`)

## Example: Turn 0 (2-Player Small Galaxy)

```yaml
game:
  seed: 987654321
  turn: 0

players:
  - id: 1
    username: "tim"
    name: "The Gage Empire"
  - id: 2
    username: "opponent"
    name: "The Hive"

designs:
  - id: 1
    owner: 1
    name: "Scout"
    hull: "scout"
    speed: 6
    scanner_range: 800
  - id: 2
    owner: 2
    name: "Scout"
    hull: "scout"
    speed: 6
    scanner_range: 800

stars:
  - id: 1
    owner: 1
    population: 25000
  - id: 2
    owner: null
    population: 0
  - id: 3
    owner: null
    population: 0
  # ... (remaining stars omitted)
  - id: 50
    owner: 2
    population: 25000

fleets:
  - id: 1
    owner: 1
    position:
      x: 549755813888
      y: 549755813888
    composition:
      - design_id: 1
        count: 1
    waypoints: []
  - id: 2
    owner: 2
    position:
      x: 552952127488
      y: 551903297536
    composition:
      - design_id: 2
        count: 1
    waypoints: []
```

## What's Out of Scope

- **Planet vs star distinction** — Phase 1 treats each star as a single colonisable location. Multi-planet systems may be introduced later.
- **Ship designer** — designs are pre-generated in Phase 1. Player-created designs come later.
- **Economy fields** — minerals, factories, mines, production queues are future phases.
- **Race/trait system** — player differentiation beyond naming is a future phase.
- **Research and technology** — future phase.
- **Fuel and cargo** — future phase.
- **Detailed movement rules** — Phase 1 uses simple distance-per-turn movement. Fuel consumption, stargates, and wormholes come later.
