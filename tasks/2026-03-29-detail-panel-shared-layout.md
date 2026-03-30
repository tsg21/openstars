# Detail panel shared layout cleanup

## Goal
Improve readability in the React detail panel by extracting repeated layout, heading, and card styling into shared primitives.

## Steps
- [x] Identify repeated detail panel wrapper and heading markup in the current component.
- [x] Extract small shared detail panel primitives and update the existing panel states to use them.
- [x] Run frontend tests and lint, then record any follow-up notes.

## Status
✅ Complete

## Notes
- Keeping this refactor intentionally local to `DetailPanel.tsx` so we reduce duplication without introducing a premature global component API.
- Verification passed on March 29, 2026 with `npm run lint` and `npm test -- --run` in `frontend/`.
