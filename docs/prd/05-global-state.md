# PRD 05 — Global State Schema

## Overview

This document defines the schema for `global-state-T{N}.json` — the server's authoritative representation of the entire game at a given turn. PRD 03 established the role of this file in the turn lifecycle; this PRD specifies what's in it.

The schema here covers **Phase 1** — the minimum needed to support galaxy generation, fleet movement, fog of war, and turn resolution. Sections will be extended as mechanics are added in later phases.

## Top-Level Structure

```json
{
  "state_version": 1,
  "game": {
    "seed": 987654321,
    "turn": 0,
    "next_id": 54,
    "combat_ruleset": "altair"
  },
  "players": [
    { "username": "tim", "name": "The Gage Empire" }
  ],
  "planets": [
    { "id": "PLk8m3x2", "owner": null, "population": 0 }
  ],
  "fleets": [
    {
      "id": "FL9qb7w1",
      "owner": "tim",
      "position": { "x": 549755813888, "y": 549755813888 },
      "composition": [{ "design_id": "DEa3f0p5", "count": 1 }],
      "waypoints": [{ "x": 550148141952, "y": 549755867136 }]
    }
  ]
}
```

## Sections

### `state_version`

Root-level persisted schema version for this state file.

| Field           | Type    | Description |
|-----------------|---------|-------------|
| `state_version` | integer | Version of the persisted state-file schema. The current version is `1`. |

This version applies to the whole JSON document, not just one subsection. Future backend versions may upgrade older saved payloads to the current schema before validating them into runtime models.

### `game`

Top-level game metadata.

| Field             | Type    | Description |
|-------------------|---------|-------------|
| `seed`            | integer | Game seed for deterministic RNG (PRD 04). Secret — never included in player state. |
| `turn`            | integer | Current turn number, zero-indexed. |
| `next_id`         | integer | Next value for the entity ID counter (PRD 04). Used to allocate base36 IDs for new entities. Incremented each time a new fleet (or other entity) is created — including fleets created by `merge_split_fleets` during turn resolution (PRD 07) and battles allocated during combat resolution (PRD 80). |
| `combat_ruleset`  | string  | Combat ruleset id for this game — `"altair"` or `"classic"`. Set at game creation, immutable for the life of the game. Determines which engine resolves battles in the turn pipeline. See PRD 80. Default: `"altair"`. |

Galaxy-level metadata (size, galaxy seed, planet positions/names) lives in `galaxy.json` (PRD 02) and is not duplicated here. The server loads both files — the galaxy definition is static, the global state evolves each turn.

### `players`

List of players in the game.

| Field      | Type   | Description |
|------------|--------|-------------|
| `username` | string | Unique player identifier — login/account name. Used as the owner reference throughout the game state. |
| `name`     | string | In-game empire/race name, displayed in the UI. |
| `race`     | object \| null | The player's race record (PRD 22). `null` from game-start generation through the turn-0 command phase; populated when turn-0 resolution snapshots the player's selection. |
| `research_state` | object | Per-player research levels, progress, and field allocation (PRD 21). |

Players are identified by `username`, not by a generated ID. All `owner` fields in other sections reference this value. In the future, usernames may be email addresses (Google Auth).

Per-player race and research records are documented in their owning PRDs (22 and 21 respectively). Future phases will add diplomacy state and other per-player data.

### Ship definitions (external dependency)

Ship-definition lifecycle and schema are owned by [PRD 18 — Ship Design](18-ship-design.md), not by global state.

Global state stores only fleet composition references (`design_id` + `count`). The referenced ship definitions live in the design registry accessed via the PRD 18 design endpoints.

### `planets`

Planet state that changes over the course of the game. Each entry corresponds to a planet defined in `galaxy.json`, linked by `id`.

| Field        | Type        | Description |
|--------------|-------------|-------------|
| `id`         | string      | Entity ID with `PL` prefix (PRD 04). Matches the planet's `id` in `galaxy.json`. |
| `owner`      | string/null | Username of the player who controls this planet, or `null` if uncolonised. |
| `population` | integer     | Current population. 0 for uncolonised planets. |

Static planet properties (name, coordinates) are read from `galaxy.json` and not repeated here. This avoids duplication and keeps the global state focused on mutable game data.

Phase 1: home planets start with an owner and initial population. All other planets start uncolonised.

Additional planet fields are added by later PRDs: mineral concentrations and surface deposits (PRD 12), environment values — gravity, temperature, radiation (PRD 14), mines, factories, scanners (PRDs 12, 11), production queue (PRD 13), starbase (PRD 17), research mode toggle (PRD 21).

### `fleets`

All fleets in the game.

| Field         | Type   | Description |
|---------------|--------|-------------|
| `id`          | string | Entity ID with `FL` prefix (PRD 04). |
| `name`        | string | Display name for the fleet (e.g. "Fleet #1"). Set at creation; players can rename via the `rename_fleet` command (PRD 07). |
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
| `design_id` | string  | Entity ID with `DE` prefix, referencing a ship definition in the PRD 18 design registry. |
| `count`     | integer | Number of ships of this referenced definition in the fleet. |

#### `waypoints` entries

| Field | Type    | Description |
|-------|---------|-------------|
| `x`   | integer | Destination x coordinate. |
| `y`   | integer | Destination y coordinate. |

Waypoints are processed in order. When a fleet reaches the first waypoint, it is removed from the list and the fleet proceeds to the next. An empty waypoint list means the fleet is stationary.

Fleet movement each turn: the fleet moves toward its first waypoint at the speed of its slowest referenced ship definition, up to a maximum of `speed` distance units per turn. The fleet's `position` is updated to its new location. If the fleet reaches the waypoint exactly, it is consumed and the fleet may continue toward the next waypoint with any remaining movement.

## Relationship to `galaxy.json`

The global state deliberately does **not** duplicate static galaxy data. The server holds both files in memory:

- **`galaxy.json`** — immutable: planet names, coordinates, galaxy size, galaxy seed
- **`global-state-T{N}.json`** — mutable: everything that changes turn-to-turn

Planets are linked by `id` — each planet in `galaxy.json` has a unique `PL`-prefixed base36 `id` (see PRD 02), and the global state references the same IDs.

## Turn 0 Generation

Turn 0 is split across two phases — the canonical specification lives in PRD 22 §"Turn 0 Generation".

**Game-start generation** runs when the host starts the game:

1. Generate the galaxy per PRD 02 (planet positions, names, IDs).
2. Create one `Player` entry per game lobby member with `race = null`.
3. Generate per-planet mineral concentrations (PRD 12) and environment values (PRD 14) for every planet.
4. No planet has an `owner` or `is_homeworld = true` yet. No fleets, designs, or installations are materialised.
5. Open `T=0`. Players submit race-selection orders (PRD 22) — the only legal command at this turn.

**Turn-0 resolution** runs once every player has submitted a race selection:

1. For each player (alphabetical username order), snapshot the chosen race onto `Player.race`.
2. Assign home planets (selection algorithm: spread evenly across the galaxy).
3. Set home-planet ownership, population, mines, factories, surface minerals, starbase, and habitability override per the player's race.
4. Create starting fleets and starting ship designs (PRD 18) for each player.
5. The build_result advances `turn` to 1.

Planet IDs are allocated during galaxy generation. Fleet and ship-definition IDs are allocated during turn-0 resolution. The `next_id` counter reflects IDs allocated across both phases.

All newly written global state files use `state_version: 1`.

## Example: Turn 0 (2-Player Small Galaxy)

```json
{
  "state_version": 1,
  "game": {
    "seed": 987654321,
    "turn": 0,
    "next_id": 54,
    "combat_ruleset": "altair"
  },
  "players": [
    { "username": "tim", "name": "The Gage Empire" },
    { "username": "sara", "name": "The Hive" }
  ],
  "planets": [
    { "id": "PLk8m3x2", "owner": "tim", "population": 25000 },
    { "id": "PL4fn9v6", "owner": null, "population": 0 },
    { "id": "PLr2j5b8", "owner": null, "population": 0 },
    { "id": "PLw1c6q3", "owner": "sara", "population": 25000 }
  ],
  "fleets": [
    {
      "id": "FL9qb7w1",
      "name": "Fleet #1",
      "owner": "tim",
      "position": { "x": 549755813888, "y": 549755813888 },
      "composition": [{ "design_id": "DEa3f0p5", "count": 1 }],
      "waypoints": []
    },
    {
      "id": "FLp4h8e2",
      "name": "Fleet #1",
      "owner": "sara",
      "position": { "x": 552952127488, "y": 551903297536 },
      "composition": [{ "design_id": "DE7xw2m9", "count": 1 }],
      "waypoints": []
    }
  ]
}
```

The `design_id` values used in fleet composition reference ship definitions stored in the PRD 18 design registry, not in this file.

## What's Out of Scope

- **Ship-definition API/schema** — defined in [PRD 18 — Ship Design](18-ship-design.md), not in global state.
- **Economy fields** — minerals, factories, mines, and production queues are defined in PRDs 12 and 13; not part of this PRD's base schema.
- **Race/trait system** — defined in [PRD 22 — Race Design](22-race-design.md). The `Player.race` field is reserved here; PRD 22 specifies the full record.
- **Research and technology** — defined in [PRD 21 — Research & Technology](21-research-and-technology.md). The `Player.research_state` field is reserved here; PRD 21 specifies it.
- **Fuel and cargo** — defined in PRDs 10 and 15.
- **Detailed movement rules** — Phase 1 uses simple distance-per-turn movement. Fuel consumption, stargates, and wormholes are defined in PRD 10.
