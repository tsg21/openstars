# Backend Skeleton — Phase 1 API

**Date:** 2026-03-28
**Goal:** Implement the Phase 1 REST API (PRD 09) as a Python backend with FastAPI, local file storage, and the core engine (galaxy generation + turn resolution).
**Relevant PRDs:** 02 (galaxy), 03 (turn lifecycle), 04 (engine conventions), 05 (global state), 06 (platform), 07 (turn mechanics), 09 (API)

---

## Step 1 — Project Scaffold

Set up the Python project structure, dependencies, and dev tooling.

- [ ] Create `backend/` directory following PRD 06 repo structure
- [ ] `pyproject.toml` with project metadata and dependencies: `fastapi`, `uvicorn`, `pydantic`, `pyyaml`
- [ ] Dev dependencies: `pytest`, `ruff`, `httpx` (for FastAPI test client)
- [ ] Create package layout:
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
- [ ] `main.py`: minimal FastAPI app with a `GET /api/v1/health` endpoint returning `{"status": "ok"}`
- [ ] Verify: `uvicorn openstars.server.main:app` starts, health check responds
- [ ] Verify: `ruff check` and `pytest` pass (even if no tests yet)

**Output:** A runnable FastAPI app that does nothing useful but proves the scaffold works.

---

## Step 2 — Pydantic Models

Define all data models matching the YAML schemas from PRDs 05 and 07, plus the API request/response schemas from PRD 09.

- [ ] `engine/models.py` — game state models:
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
- [ ] `server/schemas.py` — API request/response models:
  - `CreateGameRequest` (name, galaxy_size, players)
  - `CreateGameResponse` (game_id, name, galaxy_size, turn, players, created_at)
  - `GameSummary` (for list endpoint)
  - `GameDetail` (with per-player submission status)
  - `SubmitCommandsRequest` (turn, commands)
  - `SubmitCommandsResponse` (status, turn, command_count)
  - `ResolveResponse` (turn, status)
  - `ErrorResponse` (code, message)
- [ ] Tests: model validation (required fields, type coercion, rejection of invalid data)

**Output:** All types defined and tested. No endpoints wired yet.

---

## Step 3 — Storage Layer

Abstract file I/O behind a storage interface so the same code works with local files now and GCS later.

- [ ] `storage/base.py` — abstract `GameStorage` class:
  - `save_galaxy(game_id, galaxy)` / `load_galaxy(game_id)`
  - `save_global_state(game_id, turn, state)` / `load_global_state(game_id, turn)`
  - `save_player_state(game_id, username, turn, state)` / `load_player_state(game_id, username, turn)`
  - `save_commands(game_id, username, turn, commands)` / `load_commands(game_id, username, turn)`
  - `has_commands(game_id, username, turn)`
  - `list_games()` / `load_game_meta(game_id)` (lightweight — game_id, name, turn, players)
- [ ] `storage/local.py` — `LocalStorage(base_path)` implementation:
  - Directory layout mirrors GCS bucket layout from PRD 06:
    ```
    {base_path}/{game_id}/galaxy.yaml
    {base_path}/{game_id}/state/global-state-T{N}.yaml
    {base_path}/{game_id}/players/player-state-{username}-T{N}.yaml
    {base_path}/{game_id}/commands/player-command-{username}-T{N}.yaml
    ```
  - YAML serialisation via PyYAML
  - Pydantic models ↔ YAML round-trip
- [ ] Tests: write → read round-trip for each file type, using tmp directories

**Output:** Fully tested local storage that can persist and retrieve all game state as YAML files.

---

## Step 4 — Entity ID Generator

Implement the Feistel cipher ID generator from PRD 04.

- [ ] `engine/ids.py`:
  - `allocate_id(next_id, seed, prefix)` → returns `(entity_id, new_next_id)`
  - Feistel cipher: 4-round, operating on the base36 space (~2.18B values)
  - Base36 encoding (6 chars, lowercase a-z + 0-9)
  - Prefix prepended (PL, FL, DE)
- [ ] Tests:
  - Determinism: same seed + counter → same ID
  - Uniqueness: generate 1000 IDs, all distinct
  - Format: 2-char prefix + 6-char base36 suffix
  - Cross-seed: different seeds produce different sequences

**Output:** Working ID generator, fully tested.

---

## Step 5 — Galaxy Generation

Implement galaxy generation from PRD 02.

- [ ] `engine/galaxy.py`:
  - `generate_galaxy(name, size, seed, num_planets)` → `Galaxy`
  - Seeded RNG (PRD 04) — deterministic from galaxy seed
  - Planet placement via rejection sampling (min distance between planets)
  - Planet naming (can use a simple scheme — e.g. Greek letters + numbers, or a name list)
  - Planet IDs allocated via the Feistel generator (Step 4)
- [ ] Tests:
  - Determinism: same seed → same galaxy
  - Planet count matches requested
  - All planets within bounds
  - Minimum separation enforced
  - All IDs unique and correctly prefixed

**Output:** Galaxy generation producing valid `galaxy.yaml` content.

---

## Step 6 — Turn 0 Generation

Create the initial game state from a galaxy and player list.

- [ ] `engine/setup.py`:
  - `create_initial_state(galaxy, players, game_seed)` → `GlobalState`
  - Assign home planets (spread across galaxy — e.g. maximise minimum distance between home planets)
  - Set home planet ownership and starting population (25,000)
  - Create one scout design per player (speed: 6, scanner_range: 150)
  - Create one scout fleet per player at their home planet
  - Set `next_id` counter correctly after all allocations
- [ ] `engine/fog.py`:
  - `derive_player_state(global_state, galaxy, username)` → `PlayerState`
  - Filter planets by scanner range (own fleets' scanners)
  - Include all own planets (full detail) even outside scanner range
  - Include own fleets (full detail)
  - Include enemy fleets in scanner range (limited: no composition/waypoints)
  - Generate events list (empty for turn 0)
- [ ] Tests:
  - Correct number of players, designs, fleets
  - Home planets assigned and owned
  - Player state only contains visible information
  - Enemy fleet info is limited

**Output:** Can go from galaxy + player list → full initial game state + player views.

---

## Step 7 — Turn Resolution Engine

Implement the Phase 1 resolution pipeline from PRD 07.

- [ ] `engine/resolve.py`:
  - `resolve_turn(global_state, galaxy, all_commands)` → `GlobalState`
  - Step 1: Apply commands (set_waypoints)
  - Step 2: Move fleets (integer arithmetic movement algorithm from PRD 07)
  - Step 3: Increment turn counter
  - Command validation (fleet ownership, bounds checking)
  - Processing order: players alphabetical, fleets by ID (determinism)
- [ ] `engine/movement.py`:
  - `move_fleet(fleet, speed_parsecs)` → updated fleet
  - Integer square root (`isqrt`)
  - Multi-waypoint consumption in a single turn
  - Parsec ↔ coordinate unit conversion
- [ ] `engine/events.py`:
  - Generate events during resolution (fleet_arrived, planet_scanned)
  - Events attached to the resulting global state, filtered per player in fog.py
- [ ] Tests:
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

- [ ] `server/routes/games.py`:
  - `POST /api/v1/games` — create game (generate galaxy, create T0 state, derive player states, store everything)
  - `GET /api/v1/games` — list games (optional `?player=` filter)
  - `GET /api/v1/games/{game_id}` — game detail with submission status
- [ ] `server/routes/play.py`:
  - `GET /api/v1/games/{game_id}/galaxy` — return galaxy definition
  - `GET /api/v1/games/{game_id}/state?player={username}` — return player state (current turn or `?turn=N`)
  - `POST /api/v1/games/{game_id}/commands?player={username}` — submit commands (validate turn match)
  - `GET /api/v1/games/{game_id}/commands?player={username}` — retrieve submitted commands
  - `POST /api/v1/games/{game_id}/resolve` — trigger resolution (409 if not all submitted)
- [ ] Dependency injection: storage instance injected via FastAPI `Depends()`
- [ ] Error handling: consistent `ErrorResponse` format, proper HTTP status codes
- [ ] Tests (using `httpx` + FastAPI `TestClient`):
  - Full game lifecycle: create → get state → submit commands → resolve → get new state
  - Player isolation: each player sees only their own data
  - Turn validation on command submission
  - Error cases: missing player, invalid game, turn mismatch

**Output:** Fully functional API. Can play a game via curl/httpx.

---

## Step 9 — Docker & Local Dev

Containerise the backend and set up docker-compose for local development.

- [ ] `backend/Dockerfile` (PRD 06 sketch — Python 3.13 slim, uvicorn)
- [ ] Update `docker-compose.yaml` in repo root:
  - Backend service on port 8080, `STORAGE_BACKEND=local`, `GAME_DATA_PATH=/data`
  - Volume mount for local game data
  - Frontend service on port 3000 (existing)
- [ ] `GAME_DATA_PATH` environment variable configures local storage base path
- [ ] Verify: `docker compose up` starts both services
- [ ] Verify: can create a game and play a turn via the API

**Output:** One-command local dev setup. Both frontend and backend running together.

---

## Step 10 — Wire Frontend to Backend

Connect the existing frontend to the real API instead of mock data.

- [ ] `frontend/src/api/client.ts` — API client module:
  - Typed functions matching each endpoint
  - snake_case → camelCase conversion on responses
  - camelCase → snake_case conversion on requests
  - Base URL from `VITE_API_URL` environment variable
- [ ] Replace `useMockGameState` with real API calls:
  - Fetch galaxy once on game load (cache in state)
  - Fetch player state on load and after turn resolution
  - Submit commands via POST
  - Poll game status for turn submission progress
- [ ] Game selection: simple game list / game ID input (doesn't need to be fancy)
- [ ] Player selection: dropdown or `?player=` in URL for dev mode
- [ ] Error handling: show API errors in the UI

**Output:** The frontend works against the real backend. End-to-end gameplay with actual turn resolution.
