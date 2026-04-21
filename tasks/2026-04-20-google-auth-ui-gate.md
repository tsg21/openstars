# Google Auth UI Gate for Lobby Access

**PRDs:**
- [60-ui-overview.md](../docs/prd/60-ui-overview.md) — Access and Sign-in Gate
- [50-api.md](../docs/prd/50-api.md) — transitional `X-Player` auth model
- [06-technical-platform.md](../docs/prd/06-technical-platform.md) — staged Google Identity rollout

Implement Google sign-in in the frontend so users must authenticate before they can access the games list (lobby) or enter a game route. Backend bearer-token validation is explicitly out of scope for this task.

---

## Step 1 — Frontend auth foundations and configuration

- [ ] Add frontend auth configuration for Google Identity Services (client ID, environment wiring, and startup validation)
- [ ] Add an auth domain model (`unauthenticated` / `loading` / `authenticated` / `error`) and shared types for signed-in user identity
- [ ] Add a small auth service layer that wraps GIS initialisation and sign-in/sign-out operations
- [ ] Persist minimal sign-in session state appropriate for SPA reloads (without storing sensitive tokens long-term)
- [ ] Unit tests:
  - Auth service initialises GIS successfully
  - Auth service returns a retryable error when GIS fails to load
  - Auth state transitions are deterministic for success/failure/sign-out paths

## Step 2 — Route guarding and login screen UX

- [ ] Add a dedicated login screen as the default unauthenticated entry point
- [ ] Gate lobby (games list), game creation, and game routes behind authentication
- [ ] Redirect authenticated users from login screen to lobby
- [ ] Redirect unauthenticated users trying to access protected routes back to login
- [ ] Add loading and error UI states on the login screen for GIS initialisation/sign-in failures
- [ ] Component/router tests:
  - Unauthenticated user sees login screen and cannot access lobby content
  - Authenticated user is redirected to lobby
  - Protected route navigation bounces unauthenticated users to login
  - Login error state renders retry affordance

## Step 3 — API client integration with transitional identity header

- [ ] Update frontend API client wiring so authenticated identity drives `X-Player`
- [ ] Use signed-in Google email as the `X-Player` value for existing endpoints
- [ ] Ensure API calls are blocked or short-circuited while auth is unresolved/unauthenticated
- [ ] Preserve existing backend contract (no bearer-token changes in this task)
- [ ] Unit tests:
  - API client sends `X-Player` header from authenticated email
  - API client omits protected requests when user is signed out
  - Existing game list/game state calls continue to decode successfully under authenticated flow

## Step 4 — Header/session controls and sign-out behaviour

- [ ] Add signed-in identity display in lobby/top-level UI (email or display name)
- [ ] Add sign-out action accessible from lobby/game shell
- [ ] On sign-out, clear frontend auth/session state and return to login screen
- [ ] Ensure stale game/lobby data is not shown after sign-out
- [ ] Component/state tests:
  - Sign-out clears auth state and triggers login redirect
  - Post sign-out render does not expose previously loaded game list data

## Step 5 — Integration coverage and documentation touch-ups

- [ ] Add/update frontend integration tests for the full login → lobby → sign-out flow
- [ ] Update frontend developer documentation for required Google client ID configuration and local-dev auth behaviour
- [ ] Confirm lint/typecheck/tests pass for frontend workspace
- [ ] Verification commands (from `frontend/`):
  - `npm run lint`
  - `npm run typecheck`
  - `npm test`

## Notes

- Backend authorisation/token validation is intentionally deferred; follow-up work will migrate from `X-Player` to bearer tokens.
- Keep implementation compatible with existing local development workflow.
- Use British English in UI copy and docs where practical.
