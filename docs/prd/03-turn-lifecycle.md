# PRD 03 — Turn Lifecycle

## Overview

OpenStars! uses a **simultaneous-turn, command-and-resolve** model. Each turn follows a strict three-stage cycle driven by three file types:

1. **Global state** — the server's authoritative truth
2. **Player state** — a per-player filtered view of the world
3. **Player commands** — orders submitted by each player

All files use **JSON** for easy integration with the REST API and tooling ecosystem (see "File Format" below).

The server orchestrates this cycle. Clients never see the global state and never resolve game logic.

## The Turn Cycle

```
                    ┌─────────────────────────────────┐
                    │         SERVER                   │
                    │                                  │
                    │  global-state-T0.json             │
                    │         │                        │
                    │         ▼                        │
                    │  ┌─── Derive ───┐                │
                    │  │              │                │
                    │  ▼              ▼                │
                    │  player-state   player-state     │
                    │  P1-T0.json    P2-T0.json       │
                    └──┬──────────────┬────────────────┘
                       │              │
                       ▼              ▼
                    Player 1 UI    Player 2 UI
                       │              │
                       ▼              ▼
                    player-command  player-command
                    P1-T0.json     P2-T0.json
                       │              │
                       ▼              ▼
                    ┌──┴──────────────┴────────────────┐
                    │         SERVER                    │
                    │                                   │
                    │  Resolve(global-state-T0,          │
                    │          all player commands)      │
                    │         │                          │
                    │         ▼                          │
                    │  global-state-T1.json              │
                    │         │                          │
                    │         ▼                          │
                    │       (cycle repeats)              │
                    └───────────────────────────────────┘
```

### Stage 1: Generate Global State

The server holds the single authoritative game state in `global-state-T{N}.json`. This file contains **everything** — all planets, fleets, players, resources, and any other game objects. It is private to the server and never sent to any client.

- **Turn 0** is auto-generated when a new game is created. It includes the galaxy (from `galaxy.json`), initial player positions, starting fleets, and home planet state.
- **Turn N+1** is produced by the resolution engine from `global-state-T{N}.json` plus all submitted player commands.

A new file is created each turn. Previous turn files are retained (they form a complete game history and enable replay/debugging).

### Stage 2: Derive Player States

Once the global state for turn N exists, the server derives a **player state file** for each player:

```
global-state-T{N}.json  →  player-state-P{id}-T{N}.json  (one per player)
```

Each player state contains only the information that player has access to, filtered by fog of war and scanner coverage. This is the player's **current knowledge** of the game world — what they can see right now.

Player state files are the only game state a client ever receives.

### Stage 3: Collect Player Commands

Each player uses the UI to compose orders based on their player state. The UI is an **order editor** — it helps the player understand their situation and issue commands, but performs no simulation or resolution.

Commands are submitted as `player-command-P{id}-T{N}.json`. This file contains all orders the player wants executed during turn N's resolution.

Once the server has received commands from all players, it resolves the turn and produces the next global state. The cycle repeats.

## File Naming Conventions

| File | Pattern | Example |
|------|---------|---------|
| Global state | `global-state-T{N}.json` | `global-state-T0.json` |
| Player state | `player-state-P{id}-T{N}.json` | `player-state-P1-T0.json` |
| Player commands | `player-command-P{id}-T{N}.json` | `player-command-P1-T0.json` |

- `{N}` — zero-indexed turn number
- `{id}` — player identifier (integer, assigned at game creation)

## Turn 0 — Initial State

Turn 0 is generated automatically when a new game starts. No player commands are involved. The server:

1. Loads the galaxy definition (`galaxy.json`)
2. Assigns each player a home planet and starting position
3. Creates initial fleets and planet state for each player
4. Writes `global-state-T0.json`
5. Derives `player-state-P{id}-T0.json` for each player

Players then open the game, view their starting position, and submit commands for turn 0.

## Command Submission

- Players may **resubmit** commands at any time before the turn resolves. The latest submission overwrites any previous one. Once the last remaining player's submission triggers resolution, resubmission is no longer possible for that turn.
- **The server resolves the turn automatically as soon as every player has submitted commands.** There is no separate resolution trigger — the `POST /commands` call from the last remaining player runs the resolution pipeline synchronously before responding. The response from that call reflects the new turn (see PRD 50 for the updated response schema).
- There is **no deadline enforcement** in Phase 1. The server waits until all players have submitted. (Deadlines and auto-skip are future enhancements.)
- A player who has not yet submitted commands for the current turn is shown as "pending" to the server.
- **Turn-0 race selection** resolves via the same mechanism: when every player has submitted a `select_race` command, the turn auto-resolves and turn 1 begins.

## Player State Contents

The player state file contains two top-level sections:

### `state` — Current Knowledge

Everything the player can currently see, filtered by scanner coverage and fog of war:

- Planets within scanner range (with known attributes)
- The player's own planets (full detail)
- The player's own fleets (full detail)
- Other players' fleets and planets within scanner range (limited detail)

This represents the player's **current knowledge** of the world — what they can see right now, plus last-known data for planets they've previously scanned but can no longer see. Planets outside scanner range with no scan history are still included (name and position only). See PRD 11 for full historical knowledge rules and the `scan_level: "stale"` schema.

### `events` — What Happened This Turn

A list of notable events that occurred during the most recent turn resolution, relevant to this player:

```json
{
  "events": [
    {
      "owner": "tim",
      "source_id": "PLk8m3x2",
      "code": "movement.fleet_arrived",
      "values": ["Scout Alpha", "Proxima"]
    },
    {
      "owner": "tim",
      "source_id": "PLk8m3x2",
      "code": "mining.complete",
      "values": ["Proxima", 10, 8, 6]
    }
  ]
}
```

Events give the UI a clear "here's what happened" summary without requiring the client to diff against the previous turn's state. The event list is **per-turn** — it only contains events from the resolution that produced this state.

### Generic event envelope contract

Each event is a generic envelope:

- `owner: string` — player username that should see the event
- `source_id: string | null` — entity ID to anchor UI interactions (usually a planet/fleet ID)
- `code: string` — stable, versioned event identifier
- `values: (string | number)[]` — ordered inserts for frontend message templates

`code` values are part of the API contract and must remain stable. Human-readable text is frontend-owned so it can evolve independently and be localised without backend schema changes.

The full registry of event codes and their `values` definitions is maintained in [PRD 51 — Event Codes](51-event-codes.md).

### Migration note (legacy typed events)

Older payloads used typed, attribute-heavy events (for example `type`, `planet_id`, `item_type`, `quantity`). Those fields are replaced by `code + values` in the generic envelope.

## File Format

All files use **JSON**. This keeps the storage format identical to the API wire format — no conversion layer needed. JSON is human-readable (use `jq` or `python -m json.tool` for pretty-printing), universally supported, and natively handled by both Python (Pydantic) and TypeScript.

The specific schema for each file type (field names, nesting, data types) will be defined alongside the mechanics that populate them — this PRD defines the lifecycle and structure, not the detailed schema.

## Turn Resolution

The resolution engine is a pure function:

```
resolve(globalState[T], playerCommands[]) → globalState[T+1]
```

It is **deterministic** — the same inputs always produce the same outputs. The specific resolution pipeline (ordering of movement, combat, production, etc.) is defined separately as mechanics are implemented. See PRD 01 for the full Stars! resolution order as a reference target.

## What's Out of Scope

- **Resolution pipeline ordering** — defined per-mechanic as they're implemented
- **Deadline enforcement** — future enhancement for multiplayer
- **Detailed file schemas** — defined alongside the mechanics that need them
- **Turn replay/rewind** — retained files enable this, but the tooling is future work
