# Google sign-in and bearer-token authorisation

**Date:** 2026-08-02
**Goal:** Require Google sign-in before the lobby or any game route is reachable, make the verified email the player identity, and replace the trusted `X-Player` header with server-verified bearer tokens on every endpoint.
**Relevant PRDs:** [04 — Engine Conventions](docs/prd/04-engine-conventions.md), [06 — Technical Platform](docs/prd/06-technical-platform.md), [50 — REST API](docs/prd/50-api.md), [60 — UI Overview](docs/prd/60-ui-overview.md)

**Supersedes:** the unmerged `codex/implement-google-auth-in-ui` branch (`tasks/2026-04-20-google-auth-ui-gate.md`, 21 Apr 2026). That plan predates PR #169 and specified the standalone Google Identity Services SDK, which would have stood up a second identity stack alongside the `firebase/auth` session #169 introduced. Do not merge that branch.

## Decisions captured up-front

These were agreed before drafting the steps below — they are not open questions.

1. **Firebase Auth, not the standalone GIS SDK.** Sign-in uses `GoogleAuthProvider` + `signInWithPopup` on the existing `firebaseAuth` instance in [frontend/src/lib/firebase.ts](frontend/src/lib/firebase.ts). One Firebase app, one session, and the auth emulator already in `docker-compose` covers local dev.

2. **Bearer tokens replace `X-Player` in this task, not a later one.** Every endpoint takes `Authorization: Bearer <google-id-token>` and derives identity server-side via `verify_id_token`. An earlier draft staged this as follow-up work; that was wrong. Step 3 already builds the verification machinery, and leaving 47 call sites trusting a plain-text header beside it buys nothing.

3. **The custom-token mint is removed.** `POST /api/v1/auth/firebase-token` mints a token with `uid = X-Player` — it manufactures an identity from a client-supplied string. Google sign-in already yields a verified token, so nothing needs minting.

4. **The session endpoint survives anyway, for Firestore only.** Firestore security rules execute inside Firestore and cannot call the API, so the `games` custom claim remains the only way to gate document reads. `POST /api/v1/auth/session` exists solely to maintain that claim. Bearer auth on the API does not remove the need for it.

5. **`set_custom_user_claims` writes to the Firebase user record, not to a token.** It is a persistent, server-side mutation of the account, keyed on the uid returned by `verify_id_token` — a Firebase-generated uid, not the email. Claims reach the client only in tokens minted *after* the write, hence the forced refresh in step 5. The write **replaces** the entire claims object rather than merging, and the whole payload is capped at 1 000 bytes.

6. **Firestore security rules are unchanged.** They gate on `request.auth.token.games`, a claim, not on uid — which is the only reason the uid namespace can change from `"tim"` to a Google-generated id without breaking reads.

7. **Play-as-any-player is a per-game flag, and it is enforced.** `GameSummary.allow_player_override` decides whether a caller may act as a player other than their verified identity. The backend honours an override only when the game carries the flag *and* the requested player is a participant. Per-game means real and test games coexist in one deployment, with one explicit, auditable bypass.

8. **Defaults differ between the model and the create API, deliberately.** The Pydantic field defaults to `True` so existing Firestore documents — which have no such field — keep working and current test games stay reachable. The `POST /api/v1/games` request field defaults to `False`, so new games are strict unless the creator opts in.

9. **`X-Player` naming the caller's own identity is not an override.** `get_game_player` treats the override header as a request to act as *somebody else*: when `X-Player` equals the verified email it is ignored entirely, and the `allow_player_override` flag is never consulted. Only a header naming a *different* player triggers the flag-and-participant check (and a 403 when either fails). This is not a nicety — **the step 4 test fixture depends on it.** That fixture overrides `get_current_identity` to return the `X-Player` header, so in every one of the ~161 existing test call sites the identity and the apparent override are the same string. Treating "header present" as an override outright would 403 the entire existing suite against games that (correctly) default to `allow_player_override = False`. An earlier draft of step 2 implied the stricter reading; it was wrong.

10. **Usernames must admit `@` and `+`.** `_USERNAME_RE` in [backend/openstars/server/routes/games.py](backend/openstars/server/routes/games.py) was `^[a-zA-Z0-9][a-zA-Z0-9._-]*$`, which rejects every email address — so `POST /games` would have refused the identities decision #2 makes primary, and step 7's "Players (comma-separated emails)" form would have failed on submit. The character class now also permits `@` and `+` (plus-addressing is how test accounts are usually spelled). The leading-alphanumeric anchor and the 64-character limit are unchanged, so `/`, `\`, whitespace, `..` traversal and leading-dot names are still rejected. Done in step 2 because it blocks everything downstream.

---

## Step 1 — PRD updates

Land the design in the PRDs before writing code so later steps reference the canonical documents.

- [x] [docs/prd/06-technical-platform.md](docs/prd/06-technical-platform.md) § "Authentication — Google Identity Platform":
  - Frontend uses **Firebase Auth (`GoogleAuthProvider`)**, not the standalone GIS SDK. Sign-in is required before the lobby is reachable.
  - Backend verifies the Google ID token on **every** request; identity is never taken from a client-supplied string.
  - Replace the "Firebase custom tokens" subsection with "Session establishment", describing the claim-maintenance flow and why it is separate from API authorisation (decision #4).
  - Record the claim mechanics from decision #5 — user-record write, refresh-to-propagate, replace-not-merge, 1 000-byte cap.
- [x] [docs/prd/50-api.md](docs/prd/50-api.md) § "Authentication":
  - Replace the transitional `X-Player` model with the bearer model: `Authorization: Bearer <id-token>` required on all player-scoped endpoints, identity extracted server-side.
  - Document `X-Player` in its **new, narrow role**: an override header honoured only for games with `allow_player_override`, never as a primary identity.
  - Replace `POST /auth/firebase-token` with `POST /auth/session`.
  - Document `allow_player_override` on `POST /games` and in the games responses, and the `GET /games` listing rule.
  - Add `401` (missing/invalid/expired token) to the error tables for player-scoped endpoints.
- [x] [docs/prd/60-ui-overview.md](docs/prd/60-ui-overview.md): add "Access and Sign-in Gate" — sign-in screen as the unauthenticated entry point, gated lobby and game routes, redirect behaviour, sign-out clearing in-memory state, loading and retryable-error states, and the override picker. Remove the stale "Game lobby / game creation UI (Phase 5)" out-of-scope line.
- [x] [docs/prd/04-engine-conventions.md](docs/prd/04-engine-conventions.md) § "Player IDs": the username **is** the authenticated email for new games; legacy and override games keep free-text usernames, so the engine must treat it as an opaque string.
- [x] Run `scripts/rag-index` after the doc edits.

No code or tests in this step.

---

## Step 2 — Backend: auth dependencies

New module `backend/openstars/server/auth.py`, with dependencies wired in alongside the existing `get_storage` / `get_game_directory` pattern in [backend/openstars/server/deps.py](backend/openstars/server/deps.py).

- [x] `get_current_identity` — extracts the bearer token, calls `firebase_admin.auth.verify_id_token`, returns the verified email.
  - **401** on a missing or malformed `Authorization` header, and on `InvalidIdTokenError` / `ExpiredIdTokenError` / `RevokedIdTokenError`. Never 500.
  - **401** if the token carries no verified email — identity is the email, so such a token is unusable.
  - Landed as two dependencies: `get_verified_token` does the header parsing and `verify_id_token` call and returns the decoded claims; `get_current_identity` depends on it and extracts the email. Step 3 needs the `uid` and `name` claims, so it depends on `get_verified_token` directly rather than re-verifying.
  - `verify_id_token` is called with `check_revoked` left off (it costs a round-trip to the user record on every request). `RevokedIdTokenError` is still mapped to a 401 so enabling it stays a one-line change.
  - Error codes: `MISSING_CREDENTIALS`, `MALFORMED_CREDENTIALS`, `TOKEN_EXPIRED`, `TOKEN_REVOKED`, `TOKEN_INVALID`, `NO_VERIFIED_EMAIL`. Expired and revoked are checked before invalid — in `firebase_admin` both subclass `InvalidIdTokenError`, so the broad clause would otherwise swallow them.
- [x] `get_game_player` — resolves the effective player for a game-scoped route. Takes `game_id` (path), `get_current_identity`, the optional `X-Player` override header, and the game directory.
  - Loads the game; **404** if missing.
  - No override header → effective player is the verified email.
  - Override header present **and naming a different player** → permitted only when the game has `allow_player_override` **and** the requested player is in `summary.players`. Otherwise **403** (`OVERRIDE_NOT_ALLOWED` / `NOT_PARTICIPANT`). See decision #9 for why an `X-Player` equal to the caller's own identity is ignored instead.
  - Effective player not a participant → **403 NOT_PARTICIPANT**.
  - Returns a `GamePlayer` NamedTuple, so routes can either unpack `summary, player = …` or use attributes, without re-reading the game.
- [x] `GameSummary.allow_player_override` — the model field and the `new()` parameter (listed under step 4) were pulled forward, because `get_game_player` cannot be written or tested without them. The rest of step 4's flag work — directory queries, schemas, route wiring, the Firestore index — is untouched.
- [ ] This dependency replaces `_validate_player`, which is currently duplicated verbatim in [designs.py:35](backend/openstars/server/routes/designs.py#L35) and [play.py:32](backend/openstars/server/routes/play.py#L32), plus inline participant checks in [games.py:187](backend/openstars/server/routes/games.py#L187) and [race.py:66](backend/openstars/server/routes/race.py#L66). Delete all four. **Deferred to step 4**, where the routes are migrated — deleting them earlier would leave the routes with nothing to call.
- [x] Unit tests:
  - Valid token → identity is the token's email
  - Missing, malformed, invalid, expired and revoked tokens → 401, distinct error codes
  - Token without an email claim → 401
  - Override honoured for an override game when the target is a participant
  - Override **rejected** (403) for a non-override game, even when the target is a participant
  - Override **rejected** (403) when the target is not a participant, even on an override game
  - Verified identity not a participant → 403
  - Unknown game → 404, and 404 takes precedence over the participant check
  - Landed in `backend/tests/server/test_auth_deps.py`. It mounts the real dependencies on a throwaway `FastAPI()` with `main.game_error_handler` attached, rather than on the shared app — so these tests keep exercising the real auth path after step 4 installs its `dependency_overrides` fixture on `openstars.server.main.app`. Add to this file, not the shared app, when you want genuine auth coverage.
  - `_patch_verify(monkeypatch, …)` in that file swaps `firebase_admin.auth.verify_id_token` for a stub that returns a claims dict, or raises it when handed an exception. Reuse it in step 3.

---

## Step 3 — Backend: session endpoint

Rewrite [backend/openstars/server/routes/auth.py](backend/openstars/server/routes/auth.py).

- [x] Remove `POST /firebase-token` and the `create_custom_token` path entirely.
- [x] Add `POST /api/v1/auth/session`, authenticated by the bearer token like every other endpoint (no request body):
  - Resolve `uid` and `email` from the verified token — reuse the verification from step 2 rather than re-implementing it.
  - `directory.list_games_for_player(email, limit=_GAMES_FETCH_LIMIT)` → game ids → existing `_fit_game_ids` byte-clipping → `set_custom_user_claims(uid, {"games": game_ids})`.
  - Respond `{ "username": email, "display_name": ..., "games": [...] }`.
  - Landed depending on **both** `get_verified_token` (for the `uid`) and `get_current_identity` (for the email). FastAPI caches dependencies within a request, so the token is verified exactly once, and the `NO_VERIFIED_EMAIL` rule stays in one place instead of being restated here.
  - `display_name` is the token's `name` claim and is `None` when the token carries none — a genuine external boundary, so no invented fallback.
- [x] Keep `_fit_game_ids` and the truncation warning log unchanged. **`_firebase_app()` has already moved** — step 2 needed it, and importing it from `routes/auth.py` into `server/auth.py` would have been circular. It now lives in `backend/openstars/server/auth.py` as `firebase_app()` (no leading underscore, since it is no longer module-private). It is otherwise byte-for-byte the same `lru_cache`d initialiser. `routes/auth.py` should import it from there; `tests/server/test_auth_routes.py` currently does `from openstars.server.routes.auth import _firebase_app` and will need updating.
  - The log message prefix changed from `firebase_token.games_truncated` to `auth_session.games_truncated`; the logger and the warning condition are unchanged.
- [x] Unit tests (patching `verify_id_token` and `set_custom_user_claims`):
  - Valid token → 200, claims written against the **verified** uid, response carries email and games
  - Invalid/expired token → 401, no claims written
  - Player in no games → 200 with `games: []`
  - Games list exceeding the byte limit is truncated and logs a warning
  - Also covers: missing `Authorization` header → 401, a token with an unverified email → 401, a token with no `name` claim → `display_name: null`, and `POST /auth/firebase-token` now 404ing.

---

## Step 4 — Backend: route migration and the override flag

- [x] Migrate all 47 `x_player: str = Header(...)` occurrences across `games.py`, `play.py`, `designs.py`, `race.py` and `auth.py` to the step 2 dependencies. Rename the local to `player` — keeping `x_player` would misdescribe where the value now comes from.
  - `_validate_player` deleted from `play.py` and `designs.py`; the inline checks in `games.py` and `race.py` went with them.
  - `race.py`'s participant check used its own `NOT_PLAYER` error code. The shared dependency reports `NOT_PARTICIPANT`, as every other route already did, so that code no longer exists.
  - `designs.py`'s `_player_for_game()` now takes the `GameSummary` the dependency already read, removing the duplicate `get_game()` call flagged in the step 2 notes.
- [x] `GET /games` and `POST /games` have no game context: use `get_current_identity` directly.
- [x] Test fixtures: each of the 5 test files builds its own `TestClient` (there is no shared conftest). Add `app.dependency_overrides[get_current_identity]` reading the `X-Player` header and returning it, so the 161 existing `headers={"X-Player": ...}` call sites keep working unchanged. Add a small number of tests that exercise the *real* dependency, so the override cannot hide a broken auth path.
  - Landed as a shared `tests/server/conftest.py` holding one `client` fixture, rather than the same fixture copied five times. The five local copies were identical; `test_auth_routes.py` keeps a local one that shadows it, because those tests need the real auth path.
  - The 5th file was `test_global_state_designs.py`, not `test_auth_routes.py` — it builds a client but never sent `X-Player`, so it does not appear in a grep for that header.
  - The override raises the real `401 MISSING_CREDENTIALS` when the header is absent rather than letting FastAPI return 422, so a test that forgets the header fails the way an unauthenticated caller does.
  - Real-dependency coverage is in `tests/server/test_route_auth_migration.py`: every route family × (no credentials / `X-Player` only / malformed `Authorization`).
- [x] [backend/openstars/game_directory/base.py](backend/openstars/game_directory/base.py): add `allow_player_override: bool = True` to `GameSummary`, and an `allow_player_override: bool = False` parameter on `GameSummary.new()`. Comment the split — decision #8 reads like a bug otherwise. *(Pulled forward into step 2.)*
- [x] Add `list_games_for_player_or_override(username, limit)` to the `GameDirectory` ABC, returning the union of "games containing this player" and "games with the flag", deduplicated by `game_id`, most-recent first. Without the second half, override games (whose participants are test usernames) would never appear for a signed-in user.
  - Firestore cannot `OR` across different fields: issue the existing `array-contains` query plus `where("allow_player_override", "==", True)` and merge in Python.
  - Implement in both the Firestore and in-memory directories.
  - Needs a composite index (`allow_player_override` + `updated_at desc`) in `infra/firebase.tf`. The emulator does not enforce composite indexes, so this only fails against real Firestore — add it in the same change.
  - **Index ordered by `created_at DESC`, not `updated_at`** — resolving the open question in the step 2 notes. The two halves are merged and re-sorted in Python, so ordering them by different fields would make the merged "most-recent first" contract meaningless; `updated_at` would also reshuffle the lobby every time anyone submitted a turn. Landed as `google_firestore_index.games_by_override_created_at`.
  - A Firestore equality filter does not match documents that lack the field, so pre-existing games never come back from the override query. Their participants still reach them through the membership query, which is what decision #8 protects. Noted in the code.
- [x] [backend/openstars/server/schemas.py](backend/openstars/server/schemas.py): add `allow_player_override: bool` to `GameSummaryResponse` and `GameDetail`; add `allow_player_override: bool = False` to the create-game request. Wire it through to `GameSummary.new()`.
  - `create_game` built a `GameSummary(...)` directly and never called `new()`, so it would have bypassed the strict default entirely. It now goes through `GameSummary.new()`.
- [x] Point `GET /games` at `list_games_for_player_or_override`.
- [x] Unit tests:
  - Every migrated route rejects an unauthenticated request with 401
  - A `GameSummary` deserialised without the field defaults to `True`; `GameSummary.new()` defaults to `False`
  - Create-game honours the request field in both positions
  - `list_games_for_player_or_override` returns own + override games, deduplicated when both, ordered most-recent-first
  - The flag round-trips through `GET /games` and `GET /games/{id}`
  - Plus: `FirestoreGameDirectory.create_game` persists the field, and a newly created strict game reads back strict — with a negative-control test proving the round-trip would catch the field being dropped (the second step 2 note).

---

## Step 5 — Frontend: auth foundations

- [x] [frontend/src/lib/firebase.ts](frontend/src/lib/firebase.ts): export `googleProvider = new GoogleAuthProvider()`. One app, one session — no second instance.
- [x] Replace [frontend/src/hooks/useFirebaseAuth.ts](frontend/src/hooks/useFirebaseAuth.ts) with a `useAuth` hook owning the whole session:
  - State: `{ status: "loading" | "signed-out" | "signed-in" | "error", user: { email, displayName } | null, games: string[], error: Error | null }`.
  - `onAuthStateChanged` restores the session on reload rather than forcing a fresh popup — this replaces the old plan's bespoke session persistence.
  - `signIn()` → `signInWithPopup(firebaseAuth, googleProvider)`.
  - On sign-in: `postAuthSession()`, then `await user.getIdToken(true)`. **Order matters** — refreshing before the claims are written yields a stale token, and Firestore then denies the listener.
  - `signOut()` → `firebaseSignOut(firebaseAuth)`, reset to `signed-out`.
  - `refreshSession()` — re-runs the session call and forced refresh, for use after game creation changes the games list.
  - Treat `auth/popup-closed-by-user` and `auth/cancelled-popup-request` as a return to `signed-out`, not as errors.
  - `useGameState` called `useFirebaseAuth(player)` itself, so the session was owned per mounted game. There is one signed-in user for the whole app, so `App` now owns `useAuth()` and passes it down; `useGameNotifications` takes `{ games, refreshSession }` in place of `{ claims, refresh }`.
- [x] [frontend/src/api/client.ts](frontend/src/api/client.ts): `request()` at line 52 is the single choke point. Replace the `player?: string` parameter with an injected async token getter that sets `Authorization: Bearer <token>`; call `getIdToken()` (unforced) per request so the SDK's own refresh handles expiry.
  - Keep an optional `playerOverride` argument that sets `X-Player`, used only for override games.
  - On a 401, surface it distinctly so the UI can drop to the sign-in screen rather than showing a generic error.
  - The token getter is injected via a module-level `setAuthTokenGetter()` that `useAuth` installs, rather than the client importing Firebase itself.
  - 401 now throws `AuthError extends ApiError`, so existing `ApiError` handlers keep working while the UI can test for the auth case.
  - `listGames()` lost its `player` argument entirely, since the listing is identity-scoped server-side now.
  - `createGame()` gained an `allowPlayerOverride` argument (default `false`), and `GameSummary` / `GameDetail` gained `allowPlayerOverride`.
- [x] Replace `fetchFirebaseToken` with `postAuthSession()`.
- [x] Delete `useFirebaseAuth.test.tsx`; add `useAuth.test.tsx`:
  - Signed-out initial state once `onAuthStateChanged` reports no user
  - Successful sign-in populates email, display name and games
  - The session call happens **before** the forced refresh
  - A failing session call surfaces `error` without a half-signed-in state
  - Popup dismissal returns to `signed-out`, not `error`
  - `signOut` clears user and games
  - `refreshSession` re-issues both calls
- [x] API client tests: bearer header attached from the token getter; `X-Player` sent only when an override is passed; 401 surfaced distinctly.

---

## Step 6 — Frontend: sign-in screen and route gating

- [ ] New `frontend/src/components/panels/SignInScreen.tsx` — OpenStars! branding reusing the lobby's cover-art treatment, one primary "Sign in with Google" action, a loading state, and an `ErrorBox` with retry. Build from existing `ui/` primitives per [frontend/AGENTS.md](frontend/AGENTS.md).
- [ ] Export from `frontend/src/components/index.ts`.
- [ ] [frontend/src/App.tsx](frontend/src/App.tsx): gate ahead of the existing lobby branch at line 204 — `loading` → spinner, `signed-out` / `error` → `SignInScreen`, `signed-in` → current behaviour. Keep `App.tsx` to orchestration only.
- [ ] Derive `player` from the signed-in email, except for games with `allowPlayerOverride`, where the `?player=` deep-link and picker selection win.
- [ ] Drop the `?player=` parameter for non-override games so the address bar stops advertising an identity the app no longer takes from it.
- [ ] Component tests:
  - Signed-out renders `SignInScreen` and no lobby content
  - Loading renders neither
  - Signed-in renders the lobby
  - Error state renders a retry that re-invokes sign-in
  - `?player=` ignored for a non-override game, honoured for an override game

---

## Step 7 — Frontend: lobby identity, override picker, sign-out

- [ ] [frontend/src/components/panels/GameLobby.tsx](frontend/src/components/panels/GameLobby.tsx):
  - Show the signed-in email (or display name) and a sign-out action in the header.
  - Call `listGames()` authenticated rather than unfiltered.
  - Show the "Join as:" picker (lines 126–152) **only** when `game.allowPlayerOverride`; otherwise join directly as the signed-in email.
  - If a non-override game does not contain the signed-in email, say so instead of joining as someone else.
  - Create form: prefill the creator's email, relabel to "Players (comma-separated emails)", add an "Allow play-as-any-player (testing)" checkbox.
  - Call `refreshSession()` after a successful create so the new game lands in the `games` claim and its listener can attach.
- [ ] Add a sign-out affordance to the in-game shell.
- [ ] On sign-out, clear lobby and game state so nothing previously loaded survives.
- [ ] Component tests:
  - Signed-in email displayed
  - Override game shows the picker; non-override joins as the signed-in email
  - Non-override game not containing the email surfaces the mismatch
  - Create sends `allow_player_override` per the checkbox and prefills the creator's email
  - `refreshSession` called after create
  - Sign-out clears state and returns to the sign-in screen
  - Post-sign-out render exposes no previously loaded game list data

---

## Step 8 — Integration coverage and documentation

- [ ] Frontend integration test: sign-in → lobby → join → sign-out, with the Firestore listener attaching under refreshed claims.
- [ ] Backend integration test: authenticated `GET /games` returning own + override games; an unauthenticated call to each route family returning 401.
- [ ] Verify a game created before this change (no `allow_player_override` field in Firestore) is still listed and joinable — the legacy path decision #8 exists to protect, and the most likely regression.
- [ ] Document local-dev sign-in against the auth emulator in `AGENTS.md`: the emulator serves a fake account picker for `signInWithPopup`, and `FIREBASE_AUTH_EMULATOR_HOST` (already set in `docker-compose`) makes `verify_id_token` skip signature checks.
- [ ] Update `frontend/AGENTS.md` if feature components are expected to consume the auth hook directly.
- [ ] Verification commands:
  - `cd frontend && npm run lint`
  - `cd frontend && npm run typecheck`
  - `cd frontend && npm test`
  - `cd backend && uv run pytest`
- [ ] Mark this file's checkboxes as work completes.

---

## Notes

- **This is a breaking API change.** Every player-scoped endpoint starts rejecting `X-Player`-only requests with 401, and `POST /auth/firebase-token` disappears while the deployed frontend still calls it on load. Backend and frontend must ship together; a partial deploy takes the app down rather than degrading it. Worth confirming the Cloud Run deploy in `.github/workflows` does both, or sequencing the release deliberately.
- **`X-Player` survives, in a narrower role.** It no longer asserts identity — it requests an override, and only for games that permit one. Anywhere it is still read as primary identity after step 4 is a bug.
- **Identity Platform configuration.** Google must be enabled as a sign-in provider on the Firebase project and the deployed origins added to the authorised-domains list. Commits `481a9fe` and `bf86b81` record how easily this configuration bites.
- **Any existing API consumer outside the frontend breaks.** Scripts or tooling calling the API with `X-Player` need a token. Checked: the only non-frontend consumer is `backend/int_tests/client.py:45`, whose `_auth_headers` returns `{"X-Player": self._player}`. There is nothing in `tools/` or `scripts/`.
- Use British English in UI copy and docs where practical.

### Notes carried out of step 2 for whoever picks up step 3

- **`POST /games` and `GET /games` are currently unauthenticated in the tests.** Neither the `_create_game` helpers in `test_api.py` / `test_designer_api.py` / `test_race_routes.py` / `test_submit_auto_resolve.py` nor `test_auth_routes.py:121` send an `X-Player` header on create, and several `GET /api/v1/games` assertions call it with no header at all to exercise the unfiltered listing. Step 4 makes both endpoints require identity, so those call sites need headers added — they are *not* covered by the "161 existing call sites keep working unchanged" claim, which only holds for calls that already send `X-Player`.
- **`GET /api/v1/games` currently treats `X-Player` as an optional filter** (`x_player: str | None = Header(None)`, falling back to `list_all_games()`). That fall-back disappears in step 4: the endpoint becomes identity-scoped via `list_games_for_player_or_override`. Any test asserting "no header lists everything" is asserting the old contract.
- **`GET /api/v1/race/predefined` has no player scope** — it returns static preset data and takes no header today. It is not in the 47 `x_player` occurrences and step 4 does not mention it. Left unauthenticated; revisit only if the whole API should be closed.
- **`POST /api/v1/race/preview` takes `x_player` purely to discard it** (`del x_player` at `race.py:48`). It needs `get_current_identity` rather than `get_game_player` — there is no game in scope.
- **`designs.py` has a second game read.** Besides `_validate_player`, `_player_for_game()` calls `directory.get_game()` again to reach `global_state.players`. Once routes take `GamePlayer`, pass `context.summary` in rather than leaving the duplicate read.
- **`list_games_for_player` orders by `created_at`, not `updated_at`**, in both the Firestore and in-memory directories, and the shipped composite index in `infra/firebase.tf` is `players CONTAINS` + `created_at DESC`. Step 4 specifies the new index as `allow_player_override` + `updated_at desc`; unless the new query is deliberately ordered differently from the existing one, that should almost certainly be `created_at DESC` to match. Resolve before applying the Terraform.
- **`FirestoreGameDirectory.create_game` writes an explicit field list**, so `allow_player_override` will be silently dropped from new documents unless it is added there too — the model default of `True` would then mask the bug on read, and every new game would quietly permit overrides.
