# PRD 06 — Technical Platform

## Overview

This document defines the runtime platform, deployment strategy, and local development setup for OpenStars! The guiding principle is **zero base cost at hobby scale** — nothing runs (or costs anything) when nobody is playing.

## Platform: Google Cloud Platform

GCP was chosen for one key reason: **Cloud Run scales to zero.** A turn-based game has inherently bursty traffic — players submit turns in bursts, then nothing happens until the next round. Paying for idle compute makes no sense here.

AWS alternatives (Lambda containers, App Runner, Fargate) either lack true scale-to-zero, have packaging friction, or require extra orchestration. Cloud Run is Docker-native with no adapter layers.

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Frontend    │     │  Backend    │     │  GCS Bucket  │
│  (Cloud Run) │────▶│  (Cloud Run) │────▶│  (Game State)│
│  Static SPA  │     │  API Server │     │  JSON files  │
└─────────────┘     └─────────────┘     └─────────────┘
       │                    │
       │                    │
       ▼                    ▼
┌─────────────┐     ┌─────────────┐
│  Artifact   │     │  Google     │
│  Registry   │     │  Identity   │
│  (Images)   │     │  (Auth)     │
└─────────────┘     └─────────────┘
```

### Frontend — Cloud Run (Static SPA)

A React + TypeScript + Vite application, served from a Docker container running a lightweight static server (e.g. `nginx:alpine` or `serve`).

Dockerising the frontend — rather than hosting on Cloud Storage + CDN — keeps the tooling consistent: one `docker compose up` runs the full stack locally, and both services deploy the same way.

At the scale this project will realistically see, the marginal cost difference between static hosting and a Cloud Run container is negligible. If it ever matters, we can revisit.

### Backend — Cloud Run (API Server)

A Python API server built with **FastAPI**. The game engine runs inside this service as a package — no separate engine process or service.

Key libraries:
- **FastAPI** — async web framework with automatic OpenAPI docs and request validation
- **Pydantic** — data models and validation for game state, commands, and API schemas
- **Pydantic's built-in JSON** — serialisation for game state files (no extra dependency)
- **google-cloud-storage** — GCS client library
- **uvicorn** — ASGI server

Responsibilities:
- Serve the game API (create game, submit commands, get player state, resolve turns)
- Load and save game state via a storage adapter (`GameStorage`)
- Run the turn resolution engine
- Write updated state back to storage
- Authenticate requests via Google Identity

The backend is **stateless**. All game state lives in GCS. Any Cloud Run instance can handle any request — no sticky sessions, no in-memory state between requests.

Cold starts are irrelevant for a turn-based game. A 1–2 second startup is invisible when turns take minutes to compose.

#### Why Python (not TypeScript end-to-end)

The frontend is TypeScript (React + Vite). The backend is Python. This means the frontend and backend don't share type definitions directly — API types are defined via the FastAPI/Pydantic schema and can be consumed by the frontend via the auto-generated OpenAPI spec (with codegen tools like `openapi-typescript` if desired).

The tradeoff: Python is more accessible to collaborators, and FastAPI + Pydantic provide excellent type safety and validation within the backend. The engine remains a pure Python package with no web framework dependencies, fully testable in isolation with **pytest**.

### State Storage — Google Cloud Storage

Production game state lives in a GCS bucket, preserving the JSON-file model established in PRDs 03 and 05. The backend talks to storage through a `GameStorage` interface so the same code can run against local files in development and GCS in production.

Persisted state files are self-versioned. `global-state-T{N}.json` and `player-state-{username}-T{N}.json` include a root-level `state_version` field, starting at `1`, so the backend can recognise older save formats and upgrade them before model validation when the schema evolves.

#### Bucket Layout

```
openstars-games/
  {game_id}/
    galaxy.json
    meta.json
    state/
      global-state-T0.json
      global-state-T1.json
      ...
    players/
      player-state-{username}-T0.json
      player-state-{username}-T1.json
      ...
    commands/
      player-command-{username}-T0.json
      player-command-{username}-T1.json
      ...
    preferences/
      player-preferences-{username}.json
```

This maps directly to the three-file turn cycle from PRD 03:
- `state/` — server-only global state (one per turn)
- `players/` — per-player filtered views (generated each turn)
- `commands/` — player-submitted orders (one per player per turn)
- `meta.json` — lightweight game metadata used for game listings and lobby views

`preferences/` is reserved for future per-player settings. It is not part of the Phase 1 storage interface yet.

#### Storage Adapter Contract

Phase 1 storage is defined by an abstract `GameStorage` interface with these responsibilities:

- Save/load `galaxy.json`
- Save/load `state/global-state-T{N}.json`
- Save/load `players/player-state-{username}-T{N}.json`
- Save/load `commands/player-command-{username}-T{N}.json`
- Check whether a player's command file exists for a turn
- Save/load `meta.json`
- List game IDs that have valid metadata

`storage/local.py` is the development implementation. `storage/gcs.py` will implement the same contract for production, using the bucket root directly rather than an additional configurable object prefix.

Benefits of GCS over a database:
- **Human-readable** — download any file and inspect it. Essential for debugging a complex simulation.
- **Versioning built in** — GCS object versioning provides free audit trail.
- **Cheap** — pennies per month at hobby scale.
- **Simple** — no schema migrations, no connection pooling, no ORM.

Schema compatibility is handled in the application layer, not by GCS itself. Object versioning preserves prior blobs; `state_version` tells the backend how to interpret a blob's JSON structure.

If query patterns ever demand it (e.g. leaderboards across games, search, analytics), a database can be layered on later. For Phase 1, files are the right abstraction.

#### Concurrency

Turn command submission is inherently safe — each player writes to their own command file. Turn resolution is a single-writer operation triggered when all commands are in (or a deadline passes). No complex locking required.

For safety, the backend should use GCS **preconditions** (`ifGenerationMatch`) when writing the authoritative global state file for a turn (`state/global-state-T{N}.json`) to prevent double-resolution of the same turn. Command submission and derived player-state writes can use normal overwrite behaviour because they are not the single source of truth for turn advancement.

### Authentication — Google Identity Platform

OpenStars authentication rollout is staged to de-risk delivery:

1. **UI sign-in gate first** (current): frontend uses Google Identity Services (GIS) and requires login before lobby access.
2. **Backend bearer-token validation later**: backend validates Google ID tokens and extracts identity server-side.

Identity model decisions remain the same:

- `username` in game state maps to authenticated email identity
- No custom auth system, no password storage

During stage 1, the frontend maps the signed-in email to `X-Player` when calling the existing API (see PRD 50). This keeps endpoint contracts stable while backend authorisation work is pending.

For local development, auth can be bypassed or mocked when needed (see Local Development below).

## Docker Strategy

Both services are Dockerised with multi-stage builds.

### Local Development

A `docker-compose.yaml` file exists in the root for local dev.

Key local dev features:
- **`STORAGE_BACKEND=local`** — backend reads/writes JSON files to a local directory instead of GCS. Same code paths, swappable storage adapter.
- **`GAME_DATA_PATH=./local-data`** — local storage root on disk
- **`./local-data`** mounted volume — game state files are visible on the host filesystem for inspection and manual editing.
- **`docker compose up`** — one command to run everything.

`STORAGE_BACKEND` must be set explicitly. The backend should fail fast on startup if it is missing or set to an unknown value, rather than silently defaulting to local storage.

When running against GCS, the backend uses:

- **`STORAGE_BACKEND=gcs`**
- **`GCS_BUCKET_NAME`** — target bucket for game data
- Application Default Credentials locally, and the attached Cloud Run service account in production

The GCS adapter uses the bucket root directly for game objects; no extra path prefix is required.

For engine development (Phase 1), Docker isn't even needed — the engine is a pure Python package tested with pytest. Docker becomes relevant when the server layer is added.

## Repository Structure

```
openstars/
  frontend/                  # React + Vite SPA (TypeScript)
    Dockerfile
    src/
    package.json
  backend/                   # Python API server + game engine
    Dockerfile
    requirements.txt
    pyproject.toml
    openstars/
      engine/                # Pure game engine (no framework deps)
        galaxy.py
        resolve.py
        models.py            # Pydantic models for game state
        rng.py               # Seeded deterministic RNG
      server/
        main.py              # FastAPI app
        routes/
        middleware/
      storage/               # GCS / local file storage adapter
        base.py              # Abstract storage interface
        gcs.py
        local.py
    tests/
      engine/                # Engine unit tests (pytest)
      server/                # API integration tests
  docker-compose.yaml        # Local development
  docs/
    prd/
    references/
```

The engine lives inside the backend package but has **no dependencies on the server, storage, or web framework layers**. It remains a pure Python package as established in the phasing strategy — importable and testable in isolation with pytest.

### Type Safety Across the Stack

The backend defines API schemas via Pydantic models and FastAPI. The auto-generated OpenAPI spec serves as the contract between frontend and backend. If needed, `openapi-typescript` (or similar) can generate TypeScript types from the spec to keep the frontend in sync — but for Phase 1, manual type definitions on the frontend are fine.

## CI/CD

GitHub Actions pipeline:

1. **On push to feature branch:** lint + test (frontend: ESLint + Vitest; backend: ruff + pytest)
2. **On merge to main:** build Docker images → push to Artifact Registry → deploy to Cloud Run

Deployment is automated. No manual steps after merge.

### Artifact Registry

Docker images are stored in Google Artifact Registry (GCP's container registry). One repository per service:

- `europe-west1-docker.pkg.dev/{project}/openstars-frontend`
- `europe-west1-docker.pkg.dev/{project}/openstars-backend`

Region: `europe-west1` (Belgium) — close to Tim in the UK, and GCP's primary European region.

## Cloud Run Configuration

| Setting | Frontend | Backend |
|---------|----------|---------|
| Min instances | 0 | 0 |
| Max instances | 1 | 2 |
| CPU | 1 | 1 |
| Memory | 256 MB | 512 MB |
| Concurrency | 80 | 10 |
| Timeout | 60s | 300s |

Backend concurrency is low because turn resolution is CPU-intensive and should not be multiplexed heavily. The 300s timeout accommodates large galaxy resolution.

Both services scale to zero when idle.

## Cost Estimate (Hobby Scale)

At hobby scale (a few players, a few games):

- **Cloud Run:** Free tier covers 2 million requests/month and 360,000 vCPU-seconds. Likely $0.
- **GCS:** Free tier covers 5 GB storage. A game's JSON files are kilobytes each. Likely $0.
- **Artifact Registry:** Free tier covers 500 MB. Two small images. Likely $0.
- **Google Identity:** Free for basic Google Sign-In.
- **Networking:** Cloud Run includes a free egress allowance. Likely $0.

Realistic monthly cost: **$0–$1.** Scaling concerns are a problem we'd love to have.

## Observability

### Structured Logging

The backend writes structured JSON to stdout. Cloud Run automatically captures stdout and routes it to Cloud Logging — no agent, SDK, or configuration needed.

Every log entry is a single JSON object with at minimum:

```json
{
  "severity": "INFO",
  "message": "Turn resolved",
  "timestamp": "2026-03-22T14:05:00.000Z",
  "gameId": "abc123",
  "turn": 5,
  "username": "tim"
}
```

#### Standard Fields

| Field | Type | Description |
|-------|------|-------------|
| `severity` | string | `DEBUG`, `INFO`, `WARNING`, `ERROR`. Cloud Logging parses this for filtering and display. |
| `message` | string | Human-readable description. |
| `timestamp` | string | ISO-8601 timestamp. Cloud Logging uses this instead of ingestion time if present. |

#### Context Fields

Include where relevant — these make logs filterable and correlatable:

| Field | Type | When |
|-------|------|------|
| `gameId` | string | Any request scoped to a game |
| `turn` | integer | Turn resolution, state reads/writes |
| `username` | string | Authenticated requests |
| `durationMs` | integer | Operations worth timing (resolution, GCS reads/writes) |
| `error` | string | Error messages (alongside severity `ERROR`) |
| `stack` | string | Stack trace on exceptions |

#### Request Correlation

Cloud Run injects a `X-Cloud-Trace-Context` header on each request. The backend should extract it and include it in log entries as `logging.googleapis.com/trace`:

```json
{
  "severity": "INFO",
  "message": "Command submitted",
  "logging.googleapis.com/trace": "projects/my-project/traces/abc123def456",
  "gameId": "game-1",
  "username": "tim"
}
```

This links application logs to Cloud Run's automatic request logs — clicking a request in the console shows all related application logs.

#### Implementation

A thin logger utility in the backend — not a framework, just a function that serialises a JSON object with `severity`, `message`, `timestamp`, and any additional context fields to stdout. All application code uses this instead of raw `print()`. This keeps log output consistent and parseable.

#### What Cloud Run Provides Automatically

Beyond application logs, Cloud Run captures with zero configuration:

- **Request logs** — every HTTP request with method, path, status code, latency, response size
- **Instance lifecycle** — cold starts, shutdowns, scaling events
- **Metrics** — request count, latency percentiles, error rate, instance count, CPU/memory utilisation (visible in Cloud Monitoring dashboards)
- **Error Reporting** — stack traces in stderr are automatically grouped, with first/last seen and occurrence counts

### Frontend

The frontend is a static SPA — no server-side logging needed. Browser errors are visible in the user's dev console. If client-side error reporting becomes valuable later, it can be added as a future concern.

## What's Out of Scope

- **Custom domain / HTTPS setup** — will be needed but is a deployment task, not a design decision.
- **Alerting** — log-based alerts and error rate notifications can be layered on when needed.
- **Database** — not needed in Phase 1. Can be layered in later for cross-game queries.
- **WebSockets / real-time updates** — turn-based polling is sufficient. If we want push notifications for "it's your turn", Cloud Run supports WebSockets but that's a future concern.
- **Multi-region** — single region is fine at this scale.
