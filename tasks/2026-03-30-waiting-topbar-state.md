# Waiting top bar state

## Goal
Make the post-submit waiting state feel clearer by showing an explicit "Waiting for the next turn" message with a subtle pulse in the top bar.

## Steps
- [x] Update the top-bar wait-state copy and styling for the submitted-but-not-advanced state.
- [x] Add frontend test coverage for the waiting indicator and run frontend tests, typecheck, and lint.

## Status
✅ Complete

## Notes
- The pulse only appears while the player has submitted and is waiting for the next turn to be generated.
