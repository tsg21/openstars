# PRD 03 — Turn Lifecycle

## Overview

OpenStars! uses a **simultaneous-turn, command-and-resolve** model. Each turn follows a strict three-stage cycle driven by three file types:

1. **Global state** — the server's authoritative truth
2. **Player state** — a per-player filtered view of the world
3. **Player commands** — orders submitted by each player

The server orchestrates this cycle. Clients never see the global state and never resolve game logic.

## The Turn Cycle

```
                    ┌─────────────────────────────────┐
                    │         SERVER                   │
                    │                                  │
                    │  global-state-T0.yaml            │
                    │         │                        │
                    │         ▼                        │
                    │  ┌─── Derive ───┐                │
                    │  │              │                │
                    │  ▼              ▼                │
                    │  player-state   player-state     │
                    │  P1-T0.yaml    P2-T0.yaml       │
                    └──┬──────────────┬────────────────┘
                       │              │
                       ▼              ▼
                    Player 1 UI    Player 2 UI
                       │              │
                       ▼              ▼
                    player-command  player-command
                    P1-T0.yaml     P2-T0.yaml
                       │              │
                       ▼              ▼
                    ┌──┴──────────────┴────────────────┐
                    │         SERVER                    │
                    │                                   │
                    │  Resolve(global-state-T0,          │
                    │          all player commands)      │
                    │         │                          │
                    │         ▼                          │
                    │  global-state-T1.yaml              │
                    │         │                          │
                    │         ▼                          │
                    │       (cycle repeats)              │
                    └───────────────────────────────────┘
```

### Stage 1: Generate Global State

The server holds the single authoritative game state in `global-state-T{N}.yaml`. This file contains **everything** — all stars, planets, fleets, players, resources, and any other game objects. It is private to the server and never sent to any client.

- **Turn 0** is auto-generated when a new game is created. It includes the galaxy (from `galaxy.yaml`), initial player positions, starting fleets, and home planet state.
- **Turn N+1** is produced by the resolution engine from `global-state-T{N}.yaml` plus all submitted player commands.

A new file is created each turn. Previous turn files are retained (they form a complete game history and enable replay/debugging).

### Stage 2: Derive Player States

Once the global state for turn N exists, the server derives a **player state file** for each player:

```
global-state-T{N}.yaml  →  player-state-P{id}-T{N}.yaml  (one per player)
```

Each player state contains only the information that player has access to, filtered by fog of war and scanner coverage. This is the player's **current knowledge** of the game world — what they can see right now.

Player state files are the only game state a client ever receives.

### Stage 3: Collect Player Commands

Each player uses the UI to compose orders based on their player state. The UI is an **order editor** — it helps the player understand their situation and issue commands, but performs no simulation or resolution.

Commands are submitted as `player-command-P{id}-T{N}.yaml`. This file contains all orders the player wants executed during turn N's resolution.

Once the server has received commands from all players, it resolves the turn and produces the next global state. The cycle repeats.

## File Naming Conventions

| File | Pattern | Example |
|------|---------|---------|
| Global state | `global-state-T{N}.yaml` | `global-state-T0.yaml` |
| Player state | `player-state-P{id}-T{N}.yaml` | `player-state-P1-T0.yaml` |
| Player commands | `player-command-P{id}-T{N}.yaml` | `player-command-P1-T0.yaml` |

- `{N}` — zero-indexed turn number
- `{id}` — player identifier (integer, assigned at game creation)

## Turn 0 — Initial State

Turn 0 is generated automatically when a new game starts. No player commands are involved. The server:

1. Loads the galaxy definition (`galaxy.yaml`)
2. Assigns each player a home star and starting position
3. Creates initial fleets and planet state for each player
4. Writes `global-state-T0.yaml`
5. Derives `player-state-P{id}-T0.yaml` for each player

Players then open the game, view their starting position, and submit commands for turn 0.

## Command Submission

- Players may **resubmit** commands at any time before the turn resolves. The latest submission overwrites any previous one.
- There is **no deadline enforcement** in Phase 1. The server waits until all players have submitted. (Deadlines and auto-skip are future enhancements.)
- A player who has not yet submitted commands for the current turn is shown as "pending" to the server.

## Player State Contents

The player state file contains two top-level sections:

### `state` — Current Knowledge

Everything the player can currently see, filtered by scanner coverage and fog of war:

- Stars within scanner range (with known attributes)
- The player's own planets (full detail)
- The player's own fleets (full detail)
- Other players' fleets and planets within scanner range (limited detail)

This represents the player's **current snapshot** of the world. It does not include historical or stale information — if a player can no longer see a star, it is absent from their state. Historical knowledge tracking is a future extension.

### `events` — What Happened This Turn

A list of notable events that occurred during the most recent turn resolution, relevant to this player:

```yaml
events:
  - type: fleet_arrived
    fleet: "Scout Alpha"
    star: "Proxima"
    turn: 3

  - type: planet_scanned
    star: "Proxima"
    minerals: { ironium: 50, boranium: 30, germanium: 80 }
    population: 0
    turn: 3

  - type: fleet_detected
    owner: 2
    star: "Vega"
    turn: 3
```

Events give the UI a clear "here's what happened" summary without requiring the client to diff against the previous turn's state. The event list is **per-turn** — it only contains events from the resolution that produced this state.

Event types will be defined as game mechanics are implemented. Phase 1 events will likely be limited to fleet movement and scanning results.

## File Format

All files use **YAML** for human readability and ease of debugging. During development and testing, the ability to read and hand-edit game state is more valuable than parsing performance.

The engine will need a YAML parser/serializer. The specific schema for each file type (field names, nesting, data types) will be defined alongside the mechanics that populate them — this PRD defines the lifecycle and structure, not the detailed schema.

## Turn Resolution

The resolution engine is a pure function:

```
resolve(globalState[T], playerCommands[]) → globalState[T+1]
```

It is **deterministic** — the same inputs always produce the same outputs. The specific resolution pipeline (ordering of movement, combat, production, etc.) is defined separately as mechanics are implemented. See PRD 01 for the full Stars! resolution order as a reference target.

## What's Out of Scope

- **Resolution pipeline ordering** — defined per-mechanic as they're implemented
- **Deadline enforcement** — future enhancement for multiplayer
- **Historical/stale knowledge** — future extension, potentially a separate file
- **Detailed file schemas** — defined alongside the mechanics that need them
- **Turn replay/rewind** — retained files enable this, but the tooling is future work
