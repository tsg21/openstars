# Real-time turn notifications & auto-resolve

**Date:** 2026-05-21
**Goal:** Replace the manual two-button submit + resolve flow with a single submit that auto-resolves once the last player has submitted, replace the existing 10-second polling loop with a Firestore-driven realtime listener so players are notified instantly when the next turn is available (and when other players have submitted in the current turn), and consolidate `meta.json.gz` into the same Firestore document so game-summary metadata has one source of truth.
**Relevant PRDs:** [03 — Turn Lifecycle](docs/prd/03-turn-lifecycle.md), [06 — Technical Platform](docs/prd/06-technical-platform.md), [50 — REST API](docs/prd/50-api.md), [60 — UI Overview](docs/prd/60-ui-overview.md)

## Decisions captured up-front

These were agreed before drafting the steps below — they are not open questions.

1. **Auto-resolve is synchronous** inside `POST /api/v1/games/{game_id}/commands`. The submit request from the last remaining player runs the resolution pipeline before responding.
2. **Local dev uses the Firebase emulator suite** (`firestore` + `auth` emulators) launched via `docker-compose`. No real GCP project is involved in `docker compose up`.
3. **The manual Resolve button is removed entirely** — including the turn-0 "Begin Game" affordance. Race selection at T0 auto-resolves the same way once all players submit their `select_race` command.
4. **Polling is removed entirely.** The Firestore listener is the only post-load mechanism for noticing turn / submission changes. On listener error the UI surfaces a banner with a manual reload button rather than re-introducing a poll loop.
5. **Firestore document model:** one document per game at `games/{game_id}` holding `{ name, galaxy_size, seed, players, current_turn, players_submitted, created_at, updated_at }`. All players in the game subscribe to the same doc.
6. **Firebase custom token endpoint:** dedicated `POST /api/v1/auth/firebase-token`. Token `uid = X-Player username`; custom claim `games: [game_ids the user participates in]`. Frontend refetches before expiry and whenever a listener attach reveals a game it doesn't have in its claims.
7. **Firestore is the system of record for game-summary metadata.** `meta.json.gz` is deleted entirely; the storage-adapter `save_game_meta` / `load_game_meta` / `list_games` interface is removed. GCS continues to own large per-turn artefacts (`galaxy.json.gz`, `state/`, `players/`, `commands/`). Game creation is a two-system write — write GCS first, then Firestore; on Firestore failure, the GCS blobs are orphaned but the game is invisible. A cleanup pass can reconcile.

---

## Step 1 — PRD updates

Land the design decisions in the PRDs *before* writing code so the rest of the steps reference the canonical documents.

- [ ] [docs/prd/03-turn-lifecycle.md](docs/prd/03-turn-lifecycle.md) § "Command Submission": replace the "no auto-resolution" wording with the new contract — the server resolves the turn as soon as it has received commands from every player. Note that resubmission is still allowed only while the current turn is open (i.e. before the last submission triggers resolution).
- [ ] [docs/prd/50-api.md](docs/prd/50-api.md):
  - Remove the `POST /api/v1/games/{game_id}/resolve` endpoint from the Endpoints section and from "Design Decisions" ("Why manual resolution trigger?"). Replace the "Phase 1 note" on manual triggering with a brief note that resolution is automatic on last submission.
  - Update `POST /api/v1/games/{game_id}/commands` to document that the response may reflect the *new* turn when this submission was the last one (i.e. when `all_turns_submitted` would have flipped to true). Add a `turn_resolved: boolean` and `new_turn: int | null` to the response.
  - Add a new "Auth" subsection documenting `POST /api/v1/auth/firebase-token` (returns `{ token: string, expires_at: ISO8601 }`).
  - Note in the `GET /api/v1/games` and `GET /api/v1/games/{id}` sections that game-summary fields are now sourced from Firestore (the API surface itself is unchanged — same fields, same JSON shape).
  - Update the "Why not WebSockets?" decision: keep the title but rewrite the body to record the new approach (Firestore realtime listeners) and why we picked it over WebSockets / SSE (no session affinity worries on Cloud Run, free tier, identical local dev via emulator).
  - Update "What's out of scope" to remove "Auto-resolution on last submission" and "WebSocket push notifications" — both are now in scope.
- [ ] [docs/prd/06-technical-platform.md](docs/prd/06-technical-platform.md):
  - Add a new "Realtime Notifications & Game Directory" section between "State Storage" and "Authentication". Describe the Firestore doc model (`games/{game_id}`), the writer (backend, via Admin SDK), the reader (frontend SDK via `onSnapshot`), the security model (Firestore rules check `gameId in request.auth.token.games`), and make explicit that Firestore is the system of record for game-summary metadata (not just a notification side-channel).
  - Update the GCS Bucket Layout: remove the `meta.json.gz` entry. Add a line clarifying that game-summary metadata now lives in Firestore.
  - Update the Storage Adapter Contract: remove the "Save/load `meta.json.gz`" and "List game IDs that have valid metadata" responsibilities.
  - Extend "Authentication" to describe Firebase custom tokens: backend mints via Admin SDK using the Cloud Run service account, frontend exchanges via `signInWithCustomToken`. Note that `X-Player` remains the API-side identity header for Phase 1; the Firebase token is purely for Firestore reads.
  - Update "Local Development" to mention the emulator suite, the `FIRESTORE_EMULATOR_HOST` / `FIREBASE_AUTH_EMULATOR_HOST` env vars, and the new `firebase-emulators` docker-compose service.
  - Update the architecture diagram (ASCII) to add Firestore as a service alongside GCS, with bi-directional arrows for the backend and a one-way read arrow from the frontend.
  - Update "What's out of scope" to remove "WebSockets / real-time updates".
- [ ] After the doc edits, run `scripts/rag-index` so subsequent steps' RAG queries see the new content.

No code or tests in this step.

---

## Step 2 — Backend: `GameDirectory` interface and implementations

New package: `backend/openstars/game_directory/`.

`GameDirectory` is the abstraction that owns the Firestore `games/{game_id}` document — both the realtime-notification writes *and* the game-summary metadata that used to live in `meta.json.gz`. The rest of the backend never imports `firebase_admin` directly.

- [ ] `backend/openstars/game_directory/base.py` — abstract `GameDirectory` with methods:
  - `create_game(game_id, summary: GameSummary) -> None` — writes the initial doc with `players_submitted = []`.
  - `get_game(game_id) -> GameSummary` — reads the doc; raises `GameNotFoundError` if missing.
  - `list_games_for_player(username, limit: int = 200) -> list[GameSummary]` — Firestore: `where("players", "array-contains", username)`. Returns most-recent first.
  - `player_submitted(game_id, players_submitted: list[str]) -> None` — `set({ players_submitted, updated_at }, merge=True)`.
  - `turn_resolved(game_id, new_turn: int) -> None` — `set({ current_turn: new_turn, players_submitted: [], updated_at }, merge=True)`.
  - `delete_game(game_id) -> None` — used only by cleanup tooling / tests; not exposed via API in this task.
  - Define a `GameSummary` Pydantic model with the doc fields from decision #5, plus `all_turns_submitted` as a derived `@property` (true iff `players_submitted` covers every entry in `players`).
- [ ] `backend/openstars/game_directory/firestore.py` — `FirestoreGameDirectory` wrapping a `firestore.Client` from `firebase_admin`. Reads decode to `GameSummary`; writes use `firestore.SERVER_TIMESTAMP` for `updated_at`.
- [ ] `backend/openstars/game_directory/memory.py` — `InMemoryGameDirectory` for unit tests and the `STORAGE_BACKEND=memory` dev mode. Replaces the `noop` notifier idea from the previous draft — the directory has real state now (game-summary metadata), so a pure no-op no longer makes sense.
- [ ] `backend/openstars/game_directory/factory.py` — `build_game_directory()` that inspects `GAME_DIRECTORY_BACKEND` env var (`firestore` | `memory`). Fail fast on unknown values, matching the `STORAGE_BACKEND` pattern in [backend/openstars/storage/](backend/openstars/storage/). `STORAGE_BACKEND=memory` implies `GAME_DIRECTORY_BACKEND=memory` unless explicitly overridden.
- [ ] `backend/openstars/server/deps.py` — add a `get_game_directory()` FastAPI dependency that caches the directory per-process (matches the existing `get_storage()` shape).
- [ ] Add `firebase-admin` to `backend/pyproject.toml` via `cd backend && uv add firebase-admin`.

Unit tests in this step (`backend/tests/server/test_game_directory.py`):

- [ ] `build_game_directory()` returns `InMemoryGameDirectory` for `memory`, `FirestoreGameDirectory` for `firestore`; raises on unknown values; raises when `firestore` is selected but `FIREBASE_PROJECT_ID` is missing.
- [ ] `InMemoryGameDirectory.create_game` then `get_game` round-trips a `GameSummary`.
- [ ] `InMemoryGameDirectory.list_games_for_player` filters by membership and orders by `created_at` desc.
- [ ] `InMemoryGameDirectory.player_submitted` updates only the supplied field and bumps `updated_at`.
- [ ] `InMemoryGameDirectory.turn_resolved` advances `current_turn` and resets `players_submitted` to `[]`.
- [ ] `FirestoreGameDirectory.create_game` issues the expected `set` payload (use a `unittest.mock.MagicMock` for the Firestore client). One mirrored test per method is enough; we don't need to re-cover the round-trip behaviour at the Firestore layer.
- [ ] `GameSummary.all_turns_submitted` is true iff `set(players_submitted) >= set(players)`.

---

## Step 3 — Backend: auto-resolve in `POST /commands`, remove `POST /resolve`

Refactor [backend/openstars/server/routes/play.py](backend/openstars/server/routes/play.py).

- [ ] Extract the resolution body of the existing `resolve` endpoint into a reusable function `resolve_current_turn(storage, directory, game_id, summary) -> ResolveOutcome` in a new module `backend/openstars/server/resolution.py`. `ResolveOutcome` carries `new_turn: int` and `resolved: bool`.
- [ ] Update `submit_commands`:
  - Load `summary = directory.get_game(game_id)` (replaces `storage.load_game_meta`). Player participation check now reads `summary.players`.
  - After persisting the command, recompute `players_submitted = [p for p in summary.players if player_submitted(storage, game_id, p, current_turn)]`.
  - Call `directory.player_submitted(game_id, players_submitted)`.
  - If `set(players_submitted) >= set(summary.players)`, call `resolve_current_turn(...)` synchronously. On success, the resolution function itself calls `directory.turn_resolved(game_id, new_turn)` once the new state + player states are durable. Return `SubmitCommandsResponse(turn=current_turn, command_count=..., turn_resolved=True, new_turn=new_turn)`.
  - Otherwise return `turn_resolved=False, new_turn=None`.
- [ ] Update `SubmitCommandsResponse` in [backend/openstars/server/schemas.py](backend/openstars/server/schemas.py) accordingly.
- [ ] Delete the `POST /resolve` route handler in `play.py`. Leave `ResolveResponse` in `schemas.py` only if used elsewhere; otherwise remove it.
- [ ] Replace every `storage.load_game_meta(game_id)` call in `play.py`, [race.py](backend/openstars/server/routes/race.py), [designs.py](backend/openstars/server/routes/designs.py) with `directory.get_game(game_id)`. Adjust the participant check (`username not in meta.get("players", [])` → `username not in summary.players`) and remove anywhere that previously mutated `meta["current_turn"]` and wrote back — that bookkeeping now lives in `directory.turn_resolved`.
- [ ] If the engine resolution raises mid-submit, the player's command file is already on disk — keep it (resubmission is allowed) and return a 500 with code `RESOLUTION_FAILED` so we don't silently swallow engine bugs.
- [ ] Make `directory.turn_resolved` happen *after* the new global-state and player-state files are persisted to GCS, so a listener that fires on `current_turn` change is guaranteed to find readable state.

Unit tests in this step (`backend/tests/server/test_submit_auto_resolve.py`):

- [ ] Submitting when other players are still pending returns `turn_resolved=False, new_turn=None` and calls `directory.player_submitted` once with the new list.
- [ ] Last-player submit returns `turn_resolved=True, new_turn=current_turn+1`, advances `directory.get_game(...).current_turn`, and calls `directory.turn_resolved` exactly once.
- [ ] Idempotent re-submission by a single player does not advance the turn (re-issues `player_submitted` with the same list — that's fine).
- [ ] Engine raising during resolution returns a 500 with `RESOLUTION_FAILED` and leaves `directory.get_game(...).current_turn` unchanged.
- [ ] Turn-0 race-selection completes via the same path — last `select_race` triggers resolution, producing turn 1.
- [ ] The deleted `POST /resolve` route returns 404 (or 405). Update or delete any tests in `backend/tests/server/` that exercised it.

Integration tests:

- [ ] Add an `int_tests/test_auto_resolve.py` that drives a 2-player game over HTTP: both players submit, the second submission response carries `turn_resolved=True, new_turn=1`. Adapt [backend/int_tests/test_game_lifecycle.py](backend/int_tests/test_game_lifecycle.py) where it currently calls `/resolve` to remove that call.

---

## Step 4 — Backend: Firebase custom-token endpoint

New router: `backend/openstars/server/routes/auth.py`.

- [ ] `POST /api/v1/auth/firebase-token` with `X-Player` header.
- [ ] Body: empty.
- [ ] Response: `{ "token": "<custom-jwt>", "expires_at": "<iso8601>" }` (Firebase custom tokens are valid for 1 hour; expose the absolute expiry so the frontend can pre-emptively refresh).
- [ ] Compute the `games` claim from `directory.list_games_for_player(x_player, limit=200)`. Cap the list at 200 and log a warning if the directory returned the limit (potential truncation) — custom tokens have a 1 KB claims cap, and 200 × ~16-byte ids is comfortably safe.
- [ ] Use `firebase_admin.auth.create_custom_token(uid=x_player, developer_claims={"games": [...]})`. Initialise the default Firebase app lazily once per process; in tests this is mocked.
- [ ] Register the router in [backend/openstars/server/main.py](backend/openstars/server/main.py).
- [ ] When `FIREBASE_AUTH_EMULATOR_HOST` is set, `firebase_admin.auth.create_custom_token` works against the emulator with no extra code — but the SDK still requires a project ID. Read `FIREBASE_PROJECT_ID` from env on init.

Unit tests in this step (`backend/tests/server/test_auth_routes.py`):

- [ ] Endpoint requires `X-Player`; missing header → 422.
- [ ] Token endpoint returns a string token and an ISO-8601 `expires_at` ~1 hour ahead (mock `firebase_admin.auth.create_custom_token` to return a known sentinel; assert it was called with `uid=x_player` and the expected `games` claim).
- [ ] When the user has no games, `games` is an empty list (not omitted).
- [ ] When `list_games_for_player` returns 200 entries, the response succeeds and a warning is logged.

Integration test:

- [ ] Extend `int_tests/test_auto_resolve.py` (or add a small `test_firebase_token.py`) to hit `/api/v1/auth/firebase-token` against the running backend with the auth emulator wired up, and assert the response shape.

---

## Step 5 — Backend: wire `GameDirectory` into the game lifecycle

- [ ] [backend/openstars/server/routes/games.py](backend/openstars/server/routes/games.py) — `POST /api/v1/games`: after the GCS writes (`save_galaxy`, `create_global_state`, `save_player_state` × N) succeed, call `directory.create_game(game_id, GameSummary(...))` with `players_submitted=[]` and `current_turn=0`. If `create_game` raises, log the orphan GCS state but propagate a 500 to the caller — the cleanup pass (deferred) reconciles the orphan. The order matters: GCS first, Firestore last.
- [ ] Confirm no other code paths advance `current_turn` — turn resolution via `directory.turn_resolved` is the only place. Grep to be sure.
- [ ] Add the directory env vars to the backend dev defaults: `GAME_DIRECTORY_BACKEND=memory` for backend-only unit/integration runs; `firestore` when the full local stack with emulators is up (set via docker-compose in Step 8).

Unit tests in this step (extend `backend/tests/server/test_games_routes.py`):

- [ ] Creating a game invokes `directory.create_game` once with the expected `GameSummary` (members, turn 0, empty `players_submitted`).
- [ ] When `directory.create_game` raises, the route returns 500 and the failure is logged; the GCS-side blobs are present (orphan).

---

## Step 6 — Backend: remove `meta.json.gz`, rewire game-listing through `GameDirectory`, migration script

This is the consolidation step. After it lands, `meta.json.gz` and the `*_game_meta` storage methods are gone.

- [ ] [backend/openstars/storage/base.py](backend/openstars/storage/base.py): delete the abstract methods `save_game_meta`, `load_game_meta`, and `list_games`. Delete `meta.json.gz` knowledge from `local.py` and `gcs.py` implementations.
- [ ] [backend/openstars/server/routes/games.py](backend/openstars/server/routes/games.py):
  - `GET /api/v1/games` → `directory.list_games_for_player(x_player or _all_)` — the new directory call handles the membership filter. For `x_player is None`, expose a separate `directory.list_all_games()` method (Phase 1 has no admin/auth gate, so this is fine; phase 5 will hide it). Compute `all_turns_submitted` from each summary's `players_submitted` field rather than probing GCS — this is a substantial speed-up.
  - `GET /api/v1/games/{game_id}` → `directory.get_game(game_id)`. The per-player submission status (`players[i].submitted`) is derived directly from `summary.players_submitted`, no GCS probe required.
- [ ] [backend/openstars/server/turns.py](backend/openstars/server/turns.py): `get_current_turn(storage, game_id, meta)` becomes `get_current_turn(storage, game_id, summary)` — its only meta access was `meta.get("current_turn", 0)`, which becomes `summary.current_turn`. Update every call site.
- [ ] Grep for any remaining `meta.json.gz` mentions in code, tests, or fixtures and remove them. Update `backend/int_tests/conftest.py` if it seeds meta files.
- [ ] Drop the GCS adapter's bucket-layout helper for the meta path.
- [ ] No migration of existing prod games — production data is treated as disposable for this change. Any existing `meta.json.gz` blobs in the prod GCS bucket can be left as orphans (or deleted in a follow-up cleanup); games that existed before this change won't be re-created in Firestore and won't appear in the lobby after the new backend ships. Document this explicitly in the deploy notes so we don't surprise anyone.

Unit tests in this step:

- [ ] `backend/tests/server/test_games_routes.py`: rewrite the `GET /games` and `GET /games/{id}` tests to assert the directory is queried (not GCS).
- [ ] `backend/tests/storage/`: delete or update any tests that exercised `save_game_meta` / `load_game_meta` / `list_games`.

Integration test:

- [ ] `int_tests/test_game_lifecycle.py`: confirm game create → list flow works end-to-end with the directory as the source of truth.

---

## Step 7 — Infra: Terraform for Firestore, Firebase Auth, and IAM

Edit [infra/](infra/) — these touch production. Plan carefully; explain each change in the PR description.

- [ ] [infra/provider.tf](infra/provider.tf): make sure `google` and `google-beta` providers are both configured (Firestore database creation often needs `google-beta`).
- [ ] New file `infra/firebase.tf`:
  - `google_project_service` resources enabling `firestore.googleapis.com`, `identitytoolkit.googleapis.com`, and `firebase.googleapis.com`.
  - `google_firebase_project` (one-shot enable of Firebase on the GCP project; uses `google-beta`).
  - `google_firestore_database` in native mode, location `eur3` (multi-region matching `europe-west1`), with `concurrency_mode = OPTIMISTIC`.
  - `google_firebaserules_ruleset` + `google_firebaserules_release` to deploy [infra/firestore.rules](infra/firestore.rules) (created in this step) to the `cloud.firestore` service. Rules content:
    ```
    rules_version = '2';
    service cloud.firestore {
      match /databases/{database}/documents {
        match /games/{gameId} {
          allow read: if request.auth != null
                      && request.auth.token.games is list
                      && gameId in request.auth.token.games;
          allow write: if false;
        }
      }
    }
    ```
    Admin SDK writes from the backend bypass these rules.
- [ ] [infra/iam.tf](infra/iam.tf): grant the backend Cloud Run service account (currently `{project_number}-compute@developer.gserviceaccount.com`):
  - `roles/datastore.user` — Firestore read/write.
  - `roles/iam.serviceAccountTokenCreator` *on itself* — required to sign Firebase custom tokens with the default credentials path. (Use `google_service_account_iam_member` targeting the SA's own resource.)
- [ ] [infra/cloud_run.tf](infra/cloud_run.tf): add backend env vars `GAME_DIRECTORY_BACKEND=firestore`, `FIREBASE_PROJECT_ID=<project_id>`. Add frontend env vars `FIREBASE_PROJECT_ID`, `FIREBASE_API_KEY`, `FIREBASE_AUTH_DOMAIN` — sourced from a `google_firebase_web_app` resource (or hard-coded from the Firebase console output for the project). Confirm the frontend container's static-server image template already substitutes these into `index.html` or a runtime config endpoint; if not, this step needs to add that (small Vite env injection).
- [ ] [infra/variables.tf](infra/variables.tf): add any new variables required (e.g. `firebase_web_api_key`).
- [ ] Document blast radius in the task notes section at the bottom of this file: Firestore is a project-level resource; enabling Firebase on an existing GCP project is one-way; the SA token-creator grant is on the SA itself, not project-wide.

No unit tests for terraform (we don't have a TF test harness). Verification is `terraform plan` running cleanly + a manual review of the plan output.

---

## Step 8 — Local dev: Firebase emulators in docker-compose

- [ ] New file `firebase.json` at repo root with `emulators.firestore.port = 8085`, `emulators.auth.port = 9099`, `emulators.ui.port = 4001`. Use `host: 0.0.0.0` so containers can reach the service.
- [ ] New file `.firebaserc` at repo root pinning the demo project id (e.g. `{"projects": {"default": "openstars-local"}}`) — emulators don't need a real project but the CLI expects one.
- [ ] [docker-compose.yaml](docker-compose.yaml): add a new `firebase-emulators` service using the `andreysenov/firebase-tools` image (or build a tiny Dockerfile under `infra/firebase-emulators/`) running `firebase emulators:start --only auth,firestore --project openstars-local`. Mount the repo root so `firebase.json` and `.firebaserc` are visible. Expose ports `4001`, `8085`, `9099`.
- [ ] Update `backend` service in docker-compose:
  - Add env `GAME_DIRECTORY_BACKEND=firestore`, `FIREBASE_PROJECT_ID=openstars-local`, `FIRESTORE_EMULATOR_HOST=firebase-emulators:8085`, `FIREBASE_AUTH_EMULATOR_HOST=firebase-emulators:9099`.
  - `depends_on: [firebase-emulators]`.
- [ ] Update `frontend` service in docker-compose:
  - Add env `VITE_FIREBASE_PROJECT_ID=openstars-local`, `VITE_FIREBASE_API_KEY=fake-api-key`, `VITE_FIREBASE_AUTH_DOMAIN=openstars-local.firebaseapp.com`, `VITE_FIREBASE_USE_EMULATORS=true`.
  - When `VITE_FIREBASE_USE_EMULATORS=true` the frontend connects to the emulators on `localhost:8085` / `localhost:9099` (browser-side, hence localhost not the container hostname).
- [ ] Update the AGENTS.md "Cursor Cloud" section to add the firebase-emulators command and note the new env vars. Add a "Services overview" row for the emulators.
- [ ] Quick smoke step: `docker compose up firebase-emulators backend` and confirm `curl localhost:8080/api/v1/health` works and `curl localhost:8085` responds. Document this in the task Notes section once verified.

No automated tests in this step — verification is the smoke command above.

---

## Step 9 — Frontend: Firebase SDK setup and emulator wiring

- [ ] `cd frontend && npm install firebase` (latest v10).
- [ ] New file `frontend/src/lib/firebase.ts`:
  - Exports a singleton `firebaseApp`, `firebaseAuth`, `firebaseDb`.
  - Reads `import.meta.env.VITE_FIREBASE_*` at init.
  - When `import.meta.env.VITE_FIREBASE_USE_EMULATORS === "true"`, calls `connectAuthEmulator(auth, "http://localhost:9099", { disableWarnings: true })` and `connectFirestoreEmulator(db, "localhost", 8085)`.
- [ ] Make sure the relevant env vars are documented in [frontend/.env.example](frontend/.env.example) (create the file if absent).
- [ ] `frontend/vite.config.ts` — no change expected; Vite picks up `VITE_*` automatically.

Unit tests in this step (`frontend/src/lib/firebase.test.ts`):

- [ ] Module exports `firebaseAuth` and `firebaseDb`. Connecting emulators is invoked when the env flag is on (mock the Firebase SDK and assert `connectAuthEmulator` / `connectFirestoreEmulator` calls).
- [ ] When the env flag is off, the emulator connectors are not called.

---

## Step 10 — Frontend: Firebase auth hook

New hook: `frontend/src/hooks/useFirebaseAuth.ts`.

Responsibilities:

- On mount (and whenever `player` changes), call `POST /api/v1/auth/firebase-token` (via a new helper in [frontend/src/api/client.ts](frontend/src/api/client.ts) — `fetchFirebaseToken(player)`).
- `signInWithCustomToken(firebaseAuth, token)`.
- Track expiry; schedule a refresh ~5 minutes before `expires_at`.
- Expose `{ status: "idle" | "signed-in" | "error", refresh: () => Promise<void>, error?: Error, claims?: { games: string[] } }`.
- On refresh failure, surface the error and stay in `error` state until the consumer triggers `refresh()` again (no automatic retries — the listener-error banner in Step 12 will offer a manual reload).
- The hook reads claims from the signed-in user's ID token (via `firebaseAuth.currentUser.getIdTokenResult()`).

Unit tests (`frontend/src/hooks/useFirebaseAuth.test.tsx`):

- [ ] On mount, fetches a token and calls `signInWithCustomToken` once (mock the firebase SDK entirely).
- [ ] After successful sign-in, exposes `status: "signed-in"` and `claims.games`.
- [ ] When the token endpoint returns 401/500, exposes `status: "error"` with the error message.
- [ ] Schedules a refresh before expiry and re-signs-in with the new token.
- [ ] Switching `player` resets the hook and re-authenticates.

---

## Step 11 — Frontend: game notifications listener

New hook: `frontend/src/hooks/useGameNotifications.ts`.

Signature: `useGameNotifications({ gameId, currentTurn, onTurnAdvanced, onSubmissionsChanged })`.

- [ ] Uses `onSnapshot(doc(firebaseDb, "games", gameId), ...)` to subscribe to the game doc.
- [ ] Reads claims from `useFirebaseAuth()`. If `gameId` is not in `claims.games` (e.g. the user just joined a new game in this session), call `refresh()` once before attaching the listener. (For Phase 1, games are created once and immutable membership-wise, so this is mostly a defensive code path.)
- [ ] When the snapshot reports `current_turn > currentTurn`, call `onTurnAdvanced(newTurn)`.
- [ ] When `players_submitted` changes, call `onSubmissionsChanged(players_submitted)`.
- [ ] On listener error or permission-denied, set an internal `error` state and stop calling callbacks. Expose `error` so the consumer can render the reload banner.
- [ ] Cleans up the listener on unmount and on `gameId` change.

Unit tests (`frontend/src/hooks/useGameNotifications.test.tsx`):

- [ ] Calls `onTurnAdvanced(newTurn)` exactly once when the snapshot reports a higher turn.
- [ ] Calls `onSubmissionsChanged(newList)` when `players_submitted` changes, including when it shrinks (turn resolution resets to `[]`).
- [ ] Stops calling callbacks after the listener errors and exposes `error`.
- [ ] Tears down the listener on `gameId` change and re-attaches to the new doc.
- [ ] When `gameId` is not in current claims, calls `refresh()` before attaching (assert order).

---

## Step 12 — Frontend: rewire `useGameState`, remove polling and resolve button

Edit [frontend/src/hooks/useGameState.ts](frontend/src/hooks/useGameState.ts):

- [ ] Delete the polling effect that runs `setTimeout(poll, 10_000)` and its `submittedTurn` state. The hook no longer polls.
- [ ] Delete the `resolve()` callback exposed by the hook.
- [ ] Inside the hook (or in a new orchestrator hook colocated with `useGameState`), instantiate `useFirebaseAuth()` and `useGameNotifications()`. Wire:
  - `onTurnAdvanced(newTurn)` → reload galaxy/state/commands/gameDetail (same as the polling code did when it noticed a turn advance).
  - `onSubmissionsChanged(players_submitted)` → update `gameDetail.players[].submitted` in-place so the top-bar "Waiting: X of Y submitted" copy refreshes live, without re-fetching `gameDetail`.
- [ ] When `submit()` returns `turn_resolved: true`, eagerly reload immediately (don't wait for the listener) — both code paths arriving at "new turn is available" is fine; the listener guard already handles the no-op case.
- [ ] Expose a `notificationsError: Error | null` field on the hook return.

Edit [frontend/src/components/panels/TopBar.tsx](frontend/src/components/panels/TopBar.tsx):

- [ ] Remove the `onResolve`, `allSubmitted`, `resolveLabel`, `resolveDisabledReason` props and the corresponding `<Button>` block. The waiting copy stays (`"Waiting: X of Y submitted"`).
- [ ] Remove the "All submitted" copy variant — once everyone has submitted, the turn resolves automatically, so this state only exists for a few hundred ms and the UI should already be reloading.

Edit [frontend/src/App.tsx](frontend/src/App.tsx):

- [ ] Remove the `gameState.resolve`, `allSubmitted`, `resolveLabel`, `resolveDisabledReason`, `isTurnZeroRacePhase`-derived resolve wiring. Update the `TopBar` mount accordingly.
- [ ] Render a `notificationsError` banner above the top bar (use the existing `ErrorBox` primitive) with text `"Realtime updates disconnected"` and a `Reload` button that triggers a full state reload via the hook's existing reload mechanism.

Edit [frontend/src/api/client.ts](frontend/src/api/client.ts):

- [ ] Remove the `resolveTurn(gameId, player)` API function.
- [ ] Update the `submitCommands` return type to include `turn_resolved` and `new_turn`.
- [ ] Add `fetchFirebaseToken(player)` returning `{ token, expiresAt }`.

Unit tests in this step:

- [ ] `frontend/src/hooks/useGameState.test.tsx`: existing polling tests are deleted or rewritten — assert that the hook does not call `setInterval`/`setTimeout` for polling, and that supplying a fake `useGameNotifications` callback path triggers state reload.
- [ ] `frontend/src/components/panels/TopBar.test.tsx`: drop tests for the Resolve button. Add a test that asserts the Resolve button is *not* rendered regardless of submission state.
- [ ] `frontend/src/App.test.tsx`: remove the existing tests covering the Resolve flow. Add a test that the "realtime disconnected" banner renders when the hook surfaces `notificationsError`.
- [ ] `frontend/src/api/client.test.ts`: cover the new `submitCommands` response shape and `fetchFirebaseToken`.

---

## Step 13 — Integration verification

- [ ] `cd backend && uv run pytest` — all unit tests pass.
- [ ] `cd backend && uv run ruff check . && uv run ruff format --check .` — clean.
- [ ] `./backend/int_tests/run.sh` — integration tests pass. The harness should bring up the emulator container alongside the backend (extend [backend/int_tests/docker-compose.yaml](backend/int_tests/docker-compose.yaml) to include the same `firebase-emulators` service as the root compose file; backend `GAME_DIRECTORY_BACKEND` set to `firestore` pointing at the emulator).
- [ ] `cd frontend && npm run typecheck && npm run lint && npm test` — clean.
- [ ] Manual smoke (only if explicitly requested per the AGENTS.md testing preference): `docker compose up`, open two browser tabs as different players, submit a turn each, confirm the second submission auto-advances both tabs without a page reload and without anyone clicking "Resolve". If skipped, call that out in the final summary.

---

## Blast radius / rollback notes

- **Terraform changes touch the live GCP project.** Enabling `firebase.googleapis.com` and creating a `google_firebase_project` is effectively one-way (you can disable, but it's noisy). `terraform plan` review is essential before apply. The IAM grants (`roles/datastore.user`, `roles/iam.serviceAccountTokenCreator`) are scoped to the backend SA only.
- **Removing the `POST /resolve` endpoint is a breaking change** for any existing client that hits it. The frontend is the only client; deploy backend + frontend together. If we ever want to support older clients, we'd 410 the endpoint with a clear message instead.
- **Removing `meta.json.gz` is a one-way data break for existing prod games.** Pre-existing games will not appear in the new lobby because no Firestore doc exists for them, and no migration is being run. Suggested deploy order: (1) apply terraform → Firestore exists; (2) ship the new backend + frontend together; (3) optionally delete the orphaned `meta.json.gz` blobs in GCS as a cleanup pass. Communicate the loss of pre-change games to anyone using prod before the cutover.
- **Custom claim updates require token refresh.** A user who creates or joins a game after their token was minted needs to re-fetch `/auth/firebase-token` to include the new game in `games`. The listener hook handles this lazily on attach.
- **Firestore becomes load-bearing** for game listing and creation, not just realtime notifications. A Firestore outage now means new games can't be created and the lobby can't be listed. At hobby scale + Firestore's SLA this is acceptable; documented in PRD 06.

## Deferred / out of scope

- **GCS cleanup pass** to delete orphaned blobs from a partial game-create failure or the orphaned `meta.json.gz` files left over after the cutover — small admin script, not blocking.
- Per-player private push channels (e.g. for "new diplomatic message") — easy to add later as `games/{game_id}/players/{username}` if needed.
- Read replicas / multi-region — `eur3` already gives us multi-region durability.
- Real Google identity for the API layer — still `X-Player` for Phase 1; Firebase Auth is only used for Firestore reads.
- Turn deadlines / auto-skip — Phase 5.
- Production fallback to polling if Firestore is unhealthy — Phase 5 if it ever becomes a real problem; for now the disconnected banner with a manual reload covers it.
- Game deletion via API — `delete_game` exists on the directory but is not surfaced as an endpoint in this task.

## Status

🟡 Planned — not yet started.

## Notes

(Fill in during implementation: anything surprising about the Firebase Admin SDK + Cloud Run default credentials path, any docker-compose gotchas with the emulator image, terraform plan output that needed manual blessing, etc.)
