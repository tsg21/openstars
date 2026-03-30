# Lobby shared UI primitives

## Goal
Reduce repeated Tailwind utility strings in the lobby by extracting shared surface and form primitives for common card and field styling.

## Steps
- [x] Review repeated lobby surface and form-field styling and choose a minimal shared API.
- [x] Add shared UI primitives for panel cards and form fields, then migrate the lobby to use them.
- [x] Run frontend tests, typecheck, and lint, then record the result.

## Status
✅ Complete

## Notes
- Keeping this cleanup focused on the lobby so we improve reuse without over-generalising the rest of the UI yet.
- Added a shared `PanelCard` primitive for repeated bordered panel surfaces and shared `FormField`/`TextInput`/`SelectInput` primitives for the create-game form.
- Verification passed on March 30, 2026 with `npm test -- --run`, `npx tsc --noEmit`, and `npm run lint` in `frontend/`.
