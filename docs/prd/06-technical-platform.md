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
│  Static SPA  │     │  API Server │     │  YAML files  │
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

A Node.js (TypeScript) API server. The game engine runs inside this service as a library — no separate engine process or service.

Responsibilities:
- Serve the game API (create game, submit commands, get player state, resolve turns)
- Load galaxy and global state from GCS
- Run the turn resolution engine
- Write updated state back to GCS
- Authenticate requests via Google Identity

The backend is **stateless**. All game state lives in GCS. Any Cloud Run instance can handle any request — no sticky sessions, no in-memory state between requests.

Cold starts are irrelevant for a turn-based game. A 1–2 second startup is invisible when turns take minutes to compose.

### State Storage — Google Cloud Storage

Game state files live in a GCS bucket, preserving the YAML-file model established in PRDs 03 and 05.

#### Bucket Layout

```
openstars-games/
  {game_id}/
    galaxy.yaml
    state/
      global-state-T0.yaml
      global-state-T1.yaml
      ...
    players/
      player-state-{username}-T0.yaml
      player-state-{username}-T1.yaml
      ...
    commands/
      player-command-{username}-T0.yaml
      player-command-{username}-T1.yaml
      ...
```

This maps directly to the three-file turn cycle from PRD 03:
- `state/` — server-only global state (one per turn)
- `players/` — per-player filtered views (generated each turn)
- `commands/` — player-submitted orders (one per player per turn)

Benefits of GCS over a database:
- **Human-readable** — download any file and inspect it. Essential for debugging a complex simulation.
- **Versioning built in** — GCS object versioning provides free audit trail.
- **Cheap** — pennies per month at hobby scale.
- **Simple** — no schema migrations, no connection pooling, no ORM.

If query patterns ever demand it (e.g. leaderboards across games, search, analytics), a database can be layered on later. For Phase 1, files are the right abstraction.

#### Concurrency

Turn command submission is inherently safe — each player writes to their own command file. Turn resolution is a single-writer operation triggered when all commands are in (or a deadline passes). No complex locking required.

For safety, the backend should use GCS **preconditions** (`ifGenerationMatch`) when writing global state files to prevent double-resolution of the same turn.

### Authentication — Google Identity Platform

Players authenticate via Google Sign-In. This aligns with PRD 04's decision that player identity is an email address (via Google Auth).

- Frontend uses the Google Identity Services SDK for sign-in
- Backend validates Google ID tokens on each API request
- The `username` field in game state maps to the authenticated email
- No custom auth system, no password storage

For local development, auth can be bypassed or mocked (see Local Development below).

## Docker Strategy

Both services are Dockerised with multi-stage builds.

### Frontend Dockerfile (sketch)

```dockerfile
# Build stage
FROM node:22-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Serve stage
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 8080
```

### Backend Dockerfile (sketch)

```dockerfile
# Build stage
FROM node:22-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Run stage
FROM node:22-alpine
WORKDIR /app
COPY --from=build /app/dist ./dist
COPY --from=build /app/node_modules ./node_modules
COPY package*.json ./
EXPOSE 8080
CMD ["node", "dist/server.js"]
```

### Local Development

```yaml
# docker-compose.yaml (root of repo)
services:
  frontend:
    build: ./frontend
    ports:
      - "3000:8080"
    environment:
      - VITE_API_URL=http://localhost:8080

  backend:
    build: ./backend
    ports:
      - "8080:8080"
    environment:
      - STORAGE_BACKEND=local
      - GAME_DATA_PATH=/data
      - AUTH_DISABLED=true
    volumes:
      - ./local-data:/data
```

Key local dev features:
- **`STORAGE_BACKEND=local`** — backend reads/writes YAML files to a local directory instead of GCS. Same code paths, swappable storage adapter.
- **`AUTH_DISABLED=true`** — skips token validation locally. Requests include a `X-Dev-User` header instead.
- **`./local-data`** mounted volume — game state files are visible on the host filesystem for inspection and manual editing.
- **`docker compose up`** — one command to run everything.

For engine development (Phase 1), Docker isn't even needed — the engine is a pure TypeScript library tested with Vitest. Docker becomes relevant when the server layer is added.

## Repository Structure

```
openstars/
  frontend/              # React + Vite SPA
    Dockerfile
    src/
    package.json
  backend/               # Node.js API server + game engine
    Dockerfile
    src/
      engine/            # Pure game engine (no framework deps)
      server/            # HTTP server, routes, middleware
      storage/           # GCS / local file storage adapter
    package.json
  docker-compose.yaml    # Local development
  docs/
    prd/
    references/
```

The engine lives inside the backend package but has **no dependencies on the server or storage layers**. It remains a pure, framework-independent module as established in the phasing strategy — importable and testable in isolation.

## CI/CD

GitHub Actions pipeline:

1. **On push to feature branch:** lint + test (engine unit tests, API integration tests)
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
- **GCS:** Free tier covers 5 GB storage. A game's YAML files are kilobytes each. Likely $0.
- **Artifact Registry:** Free tier covers 500 MB. Two small images. Likely $0.
- **Google Identity:** Free for basic Google Sign-In.
- **Networking:** Cloud Run includes a free egress allowance. Likely $0.

Realistic monthly cost: **$0–$1.** Scaling concerns are a problem we'd love to have.

## What's Out of Scope

- **Custom domain / HTTPS setup** — will be needed but is a deployment task, not a design decision.
- **Monitoring / alerting** — Cloud Run provides basic metrics out of the box. Structured logging can be added when needed.
- **Database** — not needed in Phase 1. Can be layered in later for cross-game queries.
- **WebSockets / real-time updates** — turn-based polling is sufficient. If we want push notifications for "it's your turn", Cloud Run supports WebSockets but that's a future concern.
- **Multi-region** — single region is fine at this scale.
