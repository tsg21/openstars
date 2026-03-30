# Turn submission polling

## Goal
Refresh the UI automatically after a player submits so it notices when the next turn is generated without requiring a manual reload.

## Steps
- [x] Update the UI PRD to document automatic post-submit polling during the wait state.
- [x] Add frontend polling that refreshes submission status every 10 seconds after submission and reloads state when a new turn appears.
- [x] Add or update frontend tests to cover the polling behaviour, then run frontend tests, typecheck, and lint.

## Status
✅ Complete

## Notes
- Polling only runs while the current player is in the submitted state for the current turn.
- Each poll refreshes `gameDetail` so the top-bar waiting text stays current while the player waits.
- When the server advances the game to a later turn, the hook reloads galaxy, player state, and submission metadata in one pass.
