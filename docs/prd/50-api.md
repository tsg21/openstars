# PRD 09 — REST API Schema

## Overview

This document defines the Phase 1 REST API for the OpenStars! backend. The API is the contract between the frontend SPA and the Python (FastAPI) backend running on Cloud Run (PRD 06).

All endpoints are JSON over HTTPS. The internal storage format is also JSON (PRD 03/05) — no conversion needed between wire format and storage. Field names use **snake_case** throughout the backend and storage — the frontend converts to camelCase at the client layer.

## Base URL

```
https://{backend-host}
```

All endpoints are shown as full paths (e.g. `/api/v1/games`). The `/api/v1` prefix provides path-based versioning to allow breaking changes in future phases without disrupting existing clients.

## Authentication

All player-scoped endpoints require a Google ID token as a bearer credential:

```
Authorization: Bearer {google-id-token}
```

The backend verifies the token on every request (`verify_id_token`) and takes the player identity from the token's verified email. Identity is **never** read from a client-supplied string.

**Examples:**
- `GET /api/v1/games/my-game/state` — the caller's view of the game
- `POST /api/v1/games/my-game/commands` — submit commands as the caller

The header is required on all player-scoped and participant-gated endpoints: `GET /games`, `POST /games`, `GET /games/{game_id}`, `GET /state`, `GET /galaxy`, `GET /commands`, and `POST /commands`. Requests without a valid token receive `401`.

### Play-as-any-player override

Games carry an `allow_player_override` flag, set at creation and defaulting to `false`. When it is `true`, a caller may act as a player other than their own identity, which supports local testing and multi-player dev without separate accounts.

The override is requested with the `X-Player` header:

```
Authorization: Bearer {google-id-token}
X-Player: {username to act as}
```

This is the header's **only** remaining role — it requests an override, it does not assert identity. The backend honours it only when both hold:

1. The target game has `allow_player_override = true`
2. The requested username is a participant in that game

Otherwise the request is rejected with `403`. On games without the flag, `X-Player` is rejected outright rather than silently ignored, so a misconfigured client fails loudly.

The flag is per-game rather than per-deployment so real and test games can coexist in one deployment, with a single explicit, auditable bypass.

Games created before the flag existed have no such field stored and are treated as `true`, keeping them reachable.

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
  "players": ["tim@example.com", "matt@example.com"],
  "allow_player_override": false
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | yes | Display name for the game. |
| `galaxy_size` | string | yes | One of `small`, `medium`, `large`, `huge` (PRD 02). |
| `players` | string[] | yes | List of player usernames — the authenticated email for games created under the sign-in gate. Min 1. |
| `allow_player_override` | boolean | no | Defaults to `false`. When `true`, the UI lets any participant be selected — see "Play-as-any-player override" above. |

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

The server generates the galaxy, creates `global-state-T0.json`, and derives initial player states. The game is immediately playable.

`game_id` is server-generated: a URL-friendly slug derived from the name plus a random suffix for uniqueness.

**Errors:**

| Status | Condition |
|--------|-----------|
| `400` | Missing fields, invalid galaxy size, fewer than 2 players |

---

#### `GET /api/v1/games`

List games visible to the caller. Game-summary fields are sourced from Firestore.

The response is the **union** of games containing the authenticated player and games with `allow_player_override = true`, deduplicated and ordered most-recent first. The second half of that union is what makes override games discoverable at all — their participants are test usernames, so they would never match the caller's email.

**Response: `200 OK`**

```json
{
  "games": [
    {
      "game_id": "sat-game-abc123",
      "name": "Saturday Game",
      "galaxy_size": "small",
      "turn": 3,
      "players": ["tim@example.com", "matt@example.com"],
      "all_turns_submitted": false,
      "allow_player_override": false,
      "created_at": "2026-03-28T13:00:00Z"
    }
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `all_turns_submitted` | boolean | Whether all players have submitted commands for the current turn. |
| `allow_player_override` | boolean | Whether the UI may offer a player picker for this game. |

---

#### `GET /api/v1/games/{game_id}`

Get game metadata. Game-summary fields are sourced from Firestore — the API surface and JSON shape are unchanged.

**Response: `200 OK`**

```json
{
  "game_id": "sat-game-abc123",
  "name": "Saturday Game",
  "galaxy_size": "small",
  "turn": 3,
  "players": [
    { "username": "tim@example.com", "name": "tim", "submitted": true },
    { "username": "matt@example.com", "name": "matt", "submitted": false }
  ],
  "allow_player_override": false,
  "created_at": "2026-03-28T13:00:00Z"
}
```

Shows per-player submission status for the current turn.

**Errors:**

| Status | Condition |
|--------|-----------|
| `403` | Player is not a participant in this game |
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
      "scan_level": "basic",
      "scan_age": 1,
      "owner": null
    }
  ],
  "fleets": [
    {
      "id": "FL9qb7w1",
      "name": "Fleet #1",
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
      "speed": 6
    }
  ],
  "events": [
    {
      "owner": "tim",
      "source_id": "PLk8m3x2",
      "code": "production.completed",
      "values": [1, "mine", "Sol"]
    }
  ]
}
```

This mirrors the `PlayerState` type from PRD 03. Enemy fleets within scanner range appear with limited info (no `composition` or `waypoints`). All planets in the galaxy are included — `scan_level` indicates detail level: `"none"` (name/position only), `"basic"`, or `"detailed"`. Staleness is indicated by `scan_age > 0` (number of turns since last scan). See PRD 11 for the full per-level field set.

Each event in `events[]` uses the generic envelope:

| Field | Type | Description |
|-------|------|-------------|
| `owner` | string | Player who should receive the event. |
| `source_id` | string \| null | Entity anchor for the UI (typically planet/fleet id). |
| `code` | string | Stable event code (API surface). |
| `values` | (string \| number)[] | Ordered template inserts interpreted by the frontend. |

All event codes and their `values` definitions are in [PRD 51 — Event Codes](51-event-codes.md).

**Query parameters:**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `turn` | integer | current | Retrieve state for a specific historical turn (if retained). |

**Errors:**

| Status | Condition |
|--------|-----------|
| `403` | Player is not a participant in this game |
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
| `403` | Player is not a participant in this game |
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
    },
    {
      "type": "rename_fleet",
      "fleet_id": "FL9qb7w1",
      "name": "Vanguard"
    }
  ]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `turn` | integer | yes | The turn these commands target. Must match the game's current turn. Prevents stale submissions from a client that hasn't refreshed. |
| `commands` | array | yes | List of commands. See PRD 07 for command types. |

This matches the `PlayerCommands` schema from PRD 07. Phase 1 supports `set_waypoints` and `rename_fleet`; the command type union will grow in later phases.

**Response: `200 OK`**

```json
{
  "status": "submitted",
  "turn": 3,
  "command_count": 1,
  "turn_resolved": false,
  "new_turn": null
}
```

When this submission was the last one needed (all players have now submitted), the turn resolves synchronously before the response is sent:

```json
{
  "status": "submitted",
  "turn": 3,
  "command_count": 1,
  "turn_resolved": true,
  "new_turn": 4
}
```

| Field | Type | Description |
|-------|------|-------------|
| `turn_resolved` | boolean | Whether this submission triggered turn resolution. |
| `new_turn` | int \| null | The new turn number if `turn_resolved` is true; otherwise `null`. |

**Errors:**

| Status | Condition |
|--------|-----------|
| `400` | Invalid command format, unknown fleet ID, fleet not owned by player, coordinates out of bounds |
| `403` | Player is not a participant in this game |
| `404` | Game not found |
| `409` | Turn mismatch — submitted `turn` doesn't match the game's current turn (stale client or turn already resolved) |
| `500` | Turn resolution failed after commands were saved (code: `RESOLUTION_FAILED`). The command file is retained; the player may resubmit once the issue is resolved. |

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
| `403` | Player is not a participant in this game |
| `404` | Game not found |

---

### Auth

#### `POST /api/v1/auth/session`

Write a `games` custom claim onto the authenticated Firebase user so the frontend can attach Firestore realtime listeners.

This endpoint exists **only** to maintain that claim. Firestore security rules execute inside Firestore and cannot call this API, so the claim is the sole mechanism for gating document reads — bearer authorisation on the API does not replace it.

**Headers:** `Authorization: Bearer {google-id-token}` (required)

**Request body:** empty

**Response: `200 OK`**

```json
{
  "username": "alice@example.com",
  "display_name": "Alice",
  "games": ["game-abc", "game-def"]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `username` | string | Verified email from the token — the caller's player identity. |
| `display_name` | string \| null | Display name from the token, if present. |
| `games` | string[] | Games the player participates in, as written to the custom claim. |

The claim `games: [game_id, ...]` is applied via `set_custom_user_claims` against the **uid extracted from the verified token**, never a client-supplied uid. Firestore security rules use this claim to gate read access to `games/{game_id}` documents.

Custom claims are capped at 1 000 bytes, so the list is clipped by serialised byte length; truncation is logged server-side. Claims only reach the ID token when it is reissued, so the frontend must call `getIdToken(true)` after this endpoint returns, and call this endpoint again whenever its game list changes (for example after creating a game).

**Errors:**

| Status | Condition |
|--------|-----------|
| `401` | Missing or malformed `Authorization` header |
| `401` | Token invalid, expired, or revoked |
| `401` | Token carries no verified email |

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

The backend is Python (FastAPI + Pydantic), and the game state JSON uses snake_case. Converting to camelCase at the API boundary would add a translation layer in the backend for no benefit — the canonical field names are snake_case. The frontend already handles the conversion (its TypeScript types use camelCase, mapped from the API response).

### Why separate `/galaxy` from `/state`?

The galaxy is immutable for the lifetime of a game. Separating it lets the frontend fetch it once and cache indefinitely, reducing payload size on every turn refresh. The player state endpoint only carries mutable data.

### Why not WebSockets?

Firestore realtime listeners (via `onSnapshot`) are used instead of WebSockets or Server-Sent Events. Key advantages over WebSockets:

- **No session affinity** — Cloud Run routes each request independently; WebSockets require sticky sessions, which break scale-to-zero and multi-instance deployments.
- **Free tier and managed infrastructure** — Firestore at hobby scale costs nothing and is fully managed; no custom push channel to operate.
- **Identical local dev via emulator** — the Firebase emulator suite replicates the production listener behaviour locally with no special test harness.

---

## What's Out of Scope

- **Game deletion/archiving** — future admin functionality
- **Player invitations/lobby system** — Phase 5 (Multiplayer)
- **Turn deadlines and auto-skip** — Phase 5
- **Pagination** — not needed at Phase 1 scale (few games, few events)
- **Rate limiting** — Cloud Run provides basic protection; app-level limits are a future concern
- **OpenAPI spec generation** — FastAPI generates this automatically from the Pydantic models; no manual spec file needed
