# PRD 09 — REST API Schema

## Overview

This document defines the Phase 1 REST API for the OpenStars! backend. The API is the contract between the frontend SPA and the Python (FastAPI) backend running on Cloud Run (PRD 06).

All endpoints are JSON over HTTPS. YAML is the internal storage format (PRD 03/05); the API translates to/from JSON at the boundary. Field names use **snake_case** to match the Python backend and YAML schemas — the frontend converts to camelCase at the client layer.

## Base URL

```
https://{backend-host}/api/v1
```

All routes below are relative to this base. Versioning is path-based to allow breaking changes in future phases without disrupting existing clients.

## Authentication

Phase 1: Google Identity token in the `Authorization` header.

```
Authorization: Bearer <google-id-token>
```

The backend validates the token and extracts the user's email as their `username`. All ownership checks use this identity.

For local development with `AUTH_DISABLED=true`, the backend accepts an `X-Dev-User` header instead (PRD 06).

### Player Impersonation (Development Only)

When `AUTH_DISABLED=true`, all endpoints that return player-scoped data accept an optional query parameter:

```
?as={username}
```

This overrides the authenticated identity, allowing a developer to act as any player in the game without switching accounts. Useful for testing fog of war, multi-player command submission, and turn resolution from a single browser.

**Examples:**
- `GET /api/v1/games/my-game/state?as=matt` — see Matt's view of the game
- `POST /api/v1/games/my-game/commands?as=matt` — submit commands as Matt
- `GET /api/v1/games/my-game/commands?as=matt` — retrieve Matt's submitted commands

This parameter is **ignored when auth is enabled** — it has no effect in production. The backend should log a warning if `?as` is used with auth enabled, to catch accidental misuse.

---

## Endpoints

### Games

#### `POST /api/v1/games`

Create a new game.

**Request body:**

```json
{
  "name": "Saturday Game",
  "galaxy_size": "small",
  "players": ["tim", "matt"]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | yes | Display name for the game. |
| `galaxy_size` | string | yes | One of `small`, `medium`, `large`, `huge` (PRD 02). |
| `players` | string[] | yes | List of player usernames. Must include the requesting user. Min 2. |

**Response: `201 Created`**

```json
{
  "game_id": "sat-game-abc123",
  "name": "Saturday Game",
  "galaxy_size": "small",
  "turn": 0,
  "players": [
    { "username": "tim", "name": "tim" },
    { "username": "matt", "name": "matt" }
  ],
  "created_at": "2026-03-28T13:00:00Z"
}
```

The server generates the galaxy, creates `global-state-T0.yaml`, and derives initial player states. The game is immediately playable.

`game_id` is server-generated: a URL-friendly slug derived from the name plus a random suffix for uniqueness.

**Errors:**

| Status | Condition |
|--------|-----------|
| `400` | Missing fields, invalid galaxy size, fewer than 2 players |
| `401` | Unauthenticated |

---

#### `GET /api/v1/games`

List games the authenticated user is a player in.

**Response: `200 OK`**

```json
{
  "games": [
    {
      "game_id": "sat-game-abc123",
      "name": "Saturday Game",
      "galaxy_size": "small",
      "turn": 3,
      "players": ["tim", "matt"],
      "your_turn_submitted": false,
      "all_turns_submitted": false,
      "created_at": "2026-03-28T13:00:00Z"
    }
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `your_turn_submitted` | boolean | Whether the requesting user has submitted commands for the current turn. |
| `all_turns_submitted` | boolean | Whether all players have submitted for the current turn. |

---

#### `GET /api/v1/games/{game_id}`

Get game metadata.

**Response: `200 OK`**

```json
{
  "game_id": "sat-game-abc123",
  "name": "Saturday Game",
  "galaxy_size": "small",
  "turn": 3,
  "players": [
    { "username": "tim", "name": "tim", "submitted": true },
    { "username": "matt", "name": "matt", "submitted": false }
  ],
  "created_at": "2026-03-28T13:00:00Z"
}
```

Shows per-player submission status for the current turn. Only accessible to players in the game.

**Errors:**

| Status | Condition |
|--------|-----------|
| `401` | Unauthenticated |
| `403` | User is not a player in this game |
| `404` | Game not found |

---

### Player State

#### `GET /api/v1/games/{game_id}/state`

Get the requesting player's state for the current turn. This is the primary data endpoint — the frontend calls this to render the game.

**Response: `200 OK`**

```json
{
  "player": "tim",
  "turn": 3,
  "planets": [
    {
      "id": "PLk8m3x2",
      "name": "Sol",
      "x": 549755813888,
      "y": 549755813888,
      "owner": "tim",
      "population": 32000
    },
    {
      "id": "PL4fn9v6",
      "name": "Alpha Centauri",
      "x": 550148141952,
      "y": 549755867136,
      "owner": null
    }
  ],
  "fleets": [
    {
      "id": "FL9qb7w1",
      "owner": "tim",
      "position": { "x": 549755813888, "y": 549755813888 },
      "composition": [{ "design_id": "DEa3f0p5", "count": 1 }],
      "waypoints": [{ "x": 550148141952, "y": 549755867136 }]
    }
  ],
  "designs": [
    {
      "id": "DEa3f0p5",
      "owner": "tim",
      "name": "Scout",
      "hull": "scout",
      "speed": 6,
      "scanner_range": 150
    }
  ],
  "events": [
    {
      "type": "fleet_arrived",
      "fleet_id": "FL9qb7w1",
      "fleet_name": "Scout Alpha",
      "planet_id": "PLk8m3x2",
      "planet_name": "Sol",
      "turn": 3
    }
  ]
}
```

This mirrors the `PlayerState` type from PRD 03. Enemy fleets within scanner range appear with limited info (no `composition` or `waypoints`). Planets outside scanner range are omitted entirely.

**Query parameters:**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `turn` | integer | current | Retrieve state for a specific historical turn (if retained). |

**Errors:**

| Status | Condition |
|--------|-----------|
| `401` | Unauthenticated |
| `403` | User is not a player in this game |
| `404` | Game or turn not found |

---

#### `GET /api/v1/games/{game_id}/galaxy`

Get the static galaxy definition. Immutable — same response every time for a given game.

**Response: `200 OK`**

```json
{
  "galaxy": {
    "name": "Saturday Game",
    "size": "small",
    "seed": 987654321
  },
  "planets": [
    { "id": "PLk8m3x2", "name": "Sol", "x": 549755813888, "y": 549755813888 },
    { "id": "PL4fn9v6", "name": "Alpha Centauri", "x": 550148141952, "y": 549755867136 }
  ]
}
```

Separated from `/state` because it never changes — the frontend can cache it aggressively.

**Errors:**

| Status | Condition |
|--------|-----------|
| `401` | Unauthenticated |
| `403` | User is not a player in this game |
| `404` | Game not found |

---

### Commands

#### `POST /api/v1/games/{game_id}/commands`

Submit (or resubmit) the player's commands for the current turn. Overwrites any previously submitted commands.

**Request body:**

```json
{
  "turn": 3,
  "commands": [
    {
      "type": "set_waypoints",
      "fleet_id": "FL9qb7w1",
      "waypoints": [
        { "x": 550148141952, "y": 549755867136 },
        { "x": 549311406080, "y": 549956141056 }
      ]
    }
  ]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `turn` | integer | yes | The turn these commands target. Must match the game's current turn. Prevents stale submissions from a client that hasn't refreshed. |
| `commands` | array | yes | List of commands. See PRD 07 for command types. |

This matches the `PlayerCommands` schema from PRD 07. Phase 1 supports only `set_waypoints`; the command type union will grow in later phases.

**Response: `200 OK`**

```json
{
  "status": "submitted",
  "turn": 3,
  "command_count": 1
}
```

**Errors:**

| Status | Condition |
|--------|-----------|
| `400` | Invalid command format, unknown fleet ID, fleet not owned by player, coordinates out of bounds |
| `401` | Unauthenticated |
| `403` | User is not a player in this game |
| `404` | Game not found |
| `409` | Turn mismatch — submitted `turn` doesn't match the game's current turn (stale client or turn already resolved) |

---

#### `GET /api/v1/games/{game_id}/commands`

Retrieve the player's currently submitted commands for this turn. Useful for the UI to restore state after a page reload.

**Response: `200 OK`**

```json
{
  "turn": 3,
  "commands": [
    {
      "type": "set_waypoints",
      "fleet_id": "FL9qb7w1",
      "waypoints": [
        { "x": 550148141952, "y": 549755867136 }
      ]
    }
  ]
}
```

Returns an empty `commands` array if the player hasn't submitted yet this turn.

**Errors:**

| Status | Condition |
|--------|-----------|
| `401` | Unauthenticated |
| `403` | User is not a player in this game |
| `404` | Game not found |

---

### Turn Resolution

#### `POST /api/v1/games/{game_id}/resolve`

Trigger turn resolution. Only succeeds if all players have submitted commands for the current turn.

**Response: `200 OK`**

```json
{
  "turn": 4,
  "status": "resolved"
}
```

The server runs the resolution pipeline (PRD 07), writes the new global state, and derives fresh player states. After this call returns, clients can `GET /state` for the new turn.

**Errors:**

| Status | Condition |
|--------|-----------|
| `401` | Unauthenticated |
| `403` | User is not a player in this game |
| `404` | Game not found |
| `409` | Not all players have submitted commands yet |

**Phase 1 note:** Resolution is manually triggered. There is no auto-resolution when the last player submits — that's a future enhancement for convenience. The frontend can poll `GET /games/{game_id}` to check `all_turns_submitted` and show a "Resolve" button.

---

## Error Response Format

All error responses use a consistent JSON body:

```json
{
  "error": {
    "code": "FLEET_NOT_OWNED",
    "message": "Fleet FL9qb7w1 is not owned by player tim"
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `code` | string | Machine-readable error code (UPPER_SNAKE_CASE). |
| `message` | string | Human-readable description. |

---

## Design Decisions

### Why snake_case in the API?

The backend is Python (FastAPI + Pydantic), and the game state YAML uses snake_case. Converting to camelCase at the API boundary would add a translation layer in the backend for no benefit — the canonical field names are snake_case. The frontend already handles the conversion (its TypeScript types use camelCase, mapped from the API response).

### Why separate `/galaxy` from `/state`?

The galaxy is immutable for the lifetime of a game. Separating it lets the frontend fetch it once and cache indefinitely, reducing payload size on every turn refresh. The player state endpoint only carries mutable data.

### Why manual resolution trigger?

Phase 1 is a development/testing tool — being able to control exactly when turns resolve is more useful than auto-resolution. It also avoids race conditions where a player submits and the turn instantly resolves before they can review. Auto-resolution (with optional countdown/deadline) will be added in Phase 5 (Multiplayer).

### Why not WebSockets?

Turn-based games don't need real-time push. Polling `GET /games/{game_id}` every few seconds is simple, reliable, and sufficient. WebSockets add complexity (reconnection logic, Cloud Run session affinity) with minimal UX benefit at this scale. They can be layered in later for "it's your turn" notifications.

---

## What's Out of Scope

- **Game deletion/archiving** — future admin functionality
- **Player invitations/lobby system** — Phase 5 (Multiplayer)
- **Turn deadlines and auto-skip** — Phase 5
- **Auto-resolution on last submission** — Phase 5
- **WebSocket push notifications** — future enhancement
- **Pagination** — not needed at Phase 1 scale (few games, few events)
- **Rate limiting** — Cloud Run provides basic protection; app-level limits are a future concern
- **OpenAPI spec generation** — FastAPI generates this automatically from the Pydantic models; no manual spec file needed
