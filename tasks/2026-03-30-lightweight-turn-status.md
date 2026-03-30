# Lightweight turn status polling

## Goal
Avoid expensive post-submit polling by exposing a tiny backend endpoint for the current turn number and using that for wait-state checks.

## Steps
- [x] Update the PRD/task record to note that wait-state polling uses a lightweight turn-status endpoint.
- [x] Add backend support for reading the current turn cheaply from game metadata, with a minimal authenticated API endpoint for polling.
- [x] Switch the frontend polling hook to the lightweight endpoint and run backend/frontend tests plus lint/type checks.

## Status
✅ Complete

## Notes
- `meta.json` now stores `current_turn`, which is initialized at game creation and advanced when a turn resolves.
- The backend turn lookup still falls back to scanning state files if metadata is missing or stale, so existing games remain readable.
- The shared `get_current_turn()` helper now centralises that lookup so both route modules use the same behavior.
- The frontend only reloads full turn data after the lightweight endpoint reports that the turn number has advanced.
