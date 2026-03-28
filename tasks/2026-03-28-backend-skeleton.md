# Backend Skeleton — Phase 1 API

**Date:** 2026-03-28
**Goal:** Implement the Phase 1 REST API (PRD 09) as a Python backend with FastAPI, local file storage, and the core engine (galaxy generation + turn resolution).
**Relevant PRDs:** 02 (galaxy), 03 (turn lifecycle), 04 (engine conventions), 05 (global state), 06 (platform), 07 (turn mechanics), 09 (API)

---

## Step 1 — Project Scaffold

Set up the Python project structure, dependencies, and dev tooling.

- [x] Create `backend/` directory following PRD 06 repo structure
- [x] `pyproject.toml` with project metadata and dependencies: `fastapi`, `uvicorn`, `pydantic`
- [x] Dev dependencies: `pytest`, `ruff`, `httpx` (for FastAPI test client)
- [x] Create package layout:
  ```
  backend/
    pyproject.toml
    requirements.txt
    openstars/
      __init__.py
      engine/
        __init__.py
      server/
        __init__.py
        main.py
      storage/
        __init__.py
    tests/
      __init__.py
      engine/
        __init__.py
      server/
        __init__.py
  ```
- [x] `main.py`: minimal FastAPI app with a `GET /api/v1/health` endpoint returning `{"status": "ok"}`
- [x] Verify: `uvicorn openstars.server.main:app` starts, health check responds
- [x] Verify: `ruff check` and `pytest` pass (even if no tests yet)

**Output:** A runnable FastAPI app that does nothing useful but proves the scaffold works.

---

## Step 2 — Pydantic Models

Define all data models matching the JSON schemas from PRDs 05 and 07, plus the API request/response schemas from PRD 09.

- [x] `engine/models.py` — game state models:
  - `Position` (x, y)
  - `GalaxyMetadata` (name, size, seed)
  - `GalaxyPlanet` (id, name, x, y)
  - `Galaxy` (galaxy metadata + planets list)
  - `GameMeta` (seed, turn, next_id)
  - `Player` (username, name)
  - `Design` (id, owner, name, hull, speed, scanner_range)
  - `PlanetState` (id, owner, population)
  - `FleetComposition` (design_id, count)
  - `Fleet` (id, owner, position, composition, waypoints)
  - `GlobalState` (game, players, designs, planets, fleets)
  - `PlayerPlanet` (id, name, x, y, owner, population?)
  - `PlayerFleet` (id, owner, position, composition?, waypoints?)
  - `GameEvent` variants (fleet_arrived, planet_scanned, fleet_detected)
  - `PlayerState` (player, turn, planets, fleets, designs, events)
  - `SetWaypointsCommand`, `PlayerCommands`
- [x] `server/schemas.py` — API request/response models:
  - `CreateGameRequest` (name, galaxy_size, players)
  - `CreateGameResponse` (game_id, name, galaxy_size, turn, players, created_at)
  - `GameSummary` (for list endpoint)
  - `GameDetail` (with per-player submission status)
  - `SubmitCommandsRequest` (turn, commands)
  - `SubmitCommandsResponse` (status, turn, command_count)
  - `ResolveResponse` (turn, status)
  - `ErrorDetail` (code, message) wrapped in `ErrorResponse` (`{ "error": ErrorDetail }`)
- [x] Tests: model validation (required fields, type coercion, rejection of invalid data)

**Output:** All types defined and tested. No endpoints wired yet.

---

## Step 3 — Storage Layer

Abstract file I/O behind a storage interface so the same code works with local files now and GCS later.

- [x] `storage/base.py` — abstract `GameStorage` class:
  - `save_galaxy(game_id, galaxy)` / `load_galaxy(game_id)`
  - `save_global_state(game_id, turn, state)` / `load_global_state(game_id, turn)`
  - `save_player_state(game_id, username, turn, state)` / `load_player_state(game_id, username, turn)`
  - `save_commands(game_id, username, turn, commands)` / `load_commands(game_id, username, turn)`
  - `has_commands(game_id, username, turn)`
  - `list_games()` / `load_game_meta(game_id)` (lightweight — game_id, name, turn, players)
- [x] `storage/local.py` — `LocalStorage(base_path)` implementation:
  - Directory layout mirrors GCS bucket layout from PRD 06:
    ```
    {base_path}/{game_id}/galaxy.json
    {base_path}/{game_id}/state/global-state-T{N}.json
    {base_path}/{game_id}/players/player-state-{username}-T{N}.json
    {base_path}/{game_id}/commands/player-command-{username}-T{N}.json
    ```
  - JSON serialisation via Pydantic's built-in `.model_dump_json()` / `.model_validate_json()`
  - No extra serialisation dependency needed
- [x] Tests: write → read round-trip for each file type, using tmp directories

**Output:** Fully tested local storage that can persist and retrieve all game state as JSON files.

---

## Step 4 — Entity ID Generator

Implement the Feistel cipher ID generator from PRD 04.

- [x] `engine/ids.py`:
  - `allocate_id(next_id, seed, prefix)` → returns `(entity_id, new_next_id)`
  - Feistel cipher: 4-round, operating on the base36 space (~2.18B values)
  - Base36 encoding (6 chars, lowercase a-z + 0-9)
  - Prefix prepended (PL, FL, DE)
- [x] Tests:
  - Determinism: same seed + counter → same ID
  - Uniqueness: generate 1000 IDs, all distinct
  - Format: 2-char prefix + 6-char base36 suffix
  - Cross-seed: different seeds produce different sequences

**Output:** Working ID generator, fully tested.

---

## Step 5 — Galaxy Generation

Implement galaxy generation from PRD 02.

- [x] `engine/galaxy.py`:
  - `generate_galaxy(name, size, seed, num_planets)` → `Galaxy`
  - Seeded RNG (PRD 04) — deterministic from galaxy seed
  - Planet placement via rejection sampling (min distance between planets)
  - Planet naming (can use a simple scheme — e.g. Greek letters + numbers, or a name list)
  - Planet IDs allocated via the Feistel generator (Step 4)
- [x] Tests:
  - Determinism: same seed → same galaxy
  - Planet count matches requested
  - All planets within bounds
  - Minimum separation enforced
  - All IDs unique and correctly prefixed

**Output:** Galaxy generation producing valid `galaxy.json` content.

---

## Step 6 — Turn 0 Generation

Create the initial game state from a galaxy and player list.

- [x] `engine/setup.py`:
  - `create_initial_state(galaxy, players, game_seed)` → `GlobalState`
  - Assign home planets (spread across galaxy — e.g. maximise minimum distance between home planets)
  - Set home planet ownership and starting population (25,000)
  - Create one scout design per player (speed: 6, scanner_range: 150)
  - Create one scout fleet per player at their home planet
  - Set `next_id` counter correctly after all allocations
- [x] `engine/fog.py`:
  - `derive_player_state(global_state, galaxy, username)` → `PlayerState`
  - Filter planets by scanner range (own fleets' scanners)
  - Include all own planets (full detail) even outside scanner range
  - Include own fleets (full detail)
  - Include enemy fleets in scanner range (limited: no composition/waypoints)
  - Generate events list (empty for turn 0)
- [x] Tests:
  - Correct number of players, designs, fleets
  - Home planets assigned and owned
  - Player state only contains visible information
  - Enemy fleet info is limited

**Output:** Can go from galaxy + player list → full initial game state + player views.

---

## Step 7 — Turn Resolution Engine

Implement the Phase 1 resolution pipeline from PRD 07.

- [x] `engine/resolve.py`:
  - `resolve_turn(global_state, galaxy, all_commands)` → `GlobalState`
  - Step 1: Apply commands (set_waypoints)
  - Step 2: Move fleets (integer arithmetic movement algorithm from PRD 07)
  - Step 3: Increment turn counter
  - Command validation (fleet ownership, bounds checking)
  - Processing order: players alphabetical, fleets by ID (determinism)
- [x] `engine/movement.py`:
  - `move_fleet(fleet, speed_parsecs)` → updated fleet
  - Integer square root (`isqrt`)
  - Multi-waypoint consumption in a single turn
  - Parsec ↔ coordinate unit conversion
- [x] `engine/events.py`:
  - Generate events during resolution (fleet_arrived, planet_scanned)
  - Events attached to the resulting global state, filtered per player in fog.py
- [x] Tests:
  - Fleet moves correct distance toward waypoint
  - Fleet arrives at waypoint and consumes it
  - Multi-waypoint traversal in one turn
  - Stationary fleet (no waypoints) doesn't move
  - Commands applied correctly
  - Invalid commands rejected
  - Full turn cycle: state → commands → resolve → new state
  - Determinism: same inputs → identical output

**Output:** Working turn resolution. The core game loop functions without a server.

---

## Step 8 — API Endpoints

Wire up the FastAPI routes using the engine and storage layer.

- [x] `server/routes/games.py`:
  - `POST /api/v1/games` — create game (generate galaxy, create T0 state, derive player states, store everything)
  - `GET /api/v1/games` — list games (optional `?player=` filter)
  - `GET /api/v1/games/{game_id}` — game detail with submission status
- [x] `server/routes/play.py`:
  - `GET /api/v1/games/{game_id}/galaxy` — return galaxy definition
  - `GET /api/v1/games/{game_id}/state` — return player state (current turn or `?turn=N`), player from `X-Player` header
  - `POST /api/v1/games/{game_id}/commands` — submit commands (validate turn match), player from `X-Player` header
  - `GET /api/v1/games/{game_id}/commands` — retrieve submitted commands, player from `X-Player` header
  - `POST /api/v1/games/{game_id}/resolve` — trigger resolution (409 if not all submitted)
- [x] Dependency injection: storage instance injected via FastAPI `Depends()`
- [x] Error handling: consistent `ErrorResponse` format, proper HTTP status codes
- [x] Tests (using `httpx` + FastAPI `TestClient`):
  - Full game lifecycle: create → get state → submit commands → resolve → get new state
  - Player isolation: each player sees only their own data
  - Turn validation on command submission
  - Error cases: missing player, invalid game, turn mismatch

**Output:** Fully functional API. Can play a game via curl/httpx.

---

## Step 9 — Docker & Local Dev

Containerise the backend and set up docker-compose for local development.

- [x] `backend/Dockerfile` (PRD 06 sketch — Python 3.13 slim, uvicorn)
- [x] Update `docker-compose.yaml` in repo root:
  - Backend service on port 8080, `STORAGE_BACKEND=local`, `GAME_DATA_PATH=/data`
  - Volume mount for local game data
  - Frontend service on port 3000 (existing)
- [x] `GAME_DATA_PATH` environment variable configures local storage base path
- [x] `.dockerignore` for backend (exclude .venv, tests, cache)
- [ ] Verify: `docker compose up` starts both services ⏸️ No Docker on EC2 — deferred to local testing
- [ ] Verify: can create a game and play a turn via the API ⏸️ Deferred (no Docker)

**Output:** One-command local dev setup. Both frontend and backend running together.

---

## Step 10 — Wire Frontend to Backend

Connect the existing frontend to the real API instead of mock data.

- [x] `frontend/src/api/client.ts` — API client module:
  - Typed functions matching each endpoint
  - snake_case → camelCase conversion on responses
  - camelCase → snake_case conversion on requests
  - Base URL from `VITE_API_URL` environment variable
- [x] Replace `useMockGameState` with real API calls:
  - `useGameState` hook fetches galaxy, player state, and game detail
  - Fetches galaxy once on game load (cached in state)
  - Fetches player state on load and after turn resolution
  - Submit commands via POST, resolve turn via POST
  - Refreshes game detail for submission status
- [x] Game selection: GameLobby component with game list, create game form
- [x] Player selection: click player name from game card in lobby; deep-link via `?game=<id>&player=<name>` URL params
- [x] Error handling: ApiError class, error states in UI (lobby, loading, game view), inline error in top bar
- [x] Vite dev proxy configured for `/api` → `http://localhost:8080`
- [x] TopBar updated with real submission status, player name, resolve button, back-to-lobby
- [x] Tests: 6 API client tests, 3 App tests (lobby rendering), all 66 tests passing

**Output:** The frontend works against the real backend. End-to-end gameplay with actual turn resolution.
