# Muted text component

## Goal
Reduce repeated muted text styling by extracting a tiny shared typography primitive for common label and status text.

## Steps
- [x] Review repeated `text-muted-foreground` usage and choose a low-friction extraction.
- [x] Add a shared muted text component and apply it to the repeated span-based label/status cases.
- [x] Run frontend lint and tests, then record the result.

## Status
✅ Complete

## Notes
- This refactor stays intentionally small: it targets the repeated label/status text first rather than wrapping every muted paragraph or container.
- Verification passed on March 29, 2026 with `npm run lint` and `npm test -- --run` in `frontend/`.
