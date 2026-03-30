# Shared button component

## Goal
Reduce repeated button styling across the frontend by extracting a shared button component for common action variants.

## Steps
- [x] Review current button usage and identify which styles are genuinely shared.
- [x] Add a shared button component with a small variant API and migrate repeated action buttons to it.
- [x] Run frontend lint and tests, then record the result.

## Status
✅ Complete

## Notes
- This refactor targets repeated action buttons first and intentionally leaves one-off clickable cards and panel toggles as plain `<button>` elements.
- Verification passed on March 29, 2026 with `npm run lint` and `npm test -- --run` in `frontend/`.
