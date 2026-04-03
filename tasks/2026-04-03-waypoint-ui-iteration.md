# Waypoint UI Iteration

Follow-up frontend polish for waypoint editing and review in the fleet detail panel. The functional waypoint task flow already exists; this task tracks a smaller pass focused on clarity, layout, and ease of use while preserving the current behaviour.

## Step 1: Refine waypoint row presentation

- [x] Review the current waypoint list in `frontend/src/components/FleetDetail.tsx`
- [x] Show the planet name in the waypoint list when a destination matches a planet, falling back to coordinates only for deep-space waypoints
- [x] Improve the visual hierarchy of each waypoint row so destination, ETA, and task status are easier to scan
- [x] Remove circled waypoint numbers so the list leads with the destination label and uses space more efficiently
- [ ] Tighten spacing and button placement in edit mode so task editing feels less cramped

Unit tests:
- [x] Update `frontend/src/components/FleetDetail.test.tsx` to cover planet-name waypoint labels
- [ ] Update `frontend/src/components/DetailPanel.test.tsx` for any changed labels, roles, or visible waypoint metadata

## Step 2: Improve inline task editing affordances

- [x] Make the task editor entry point and open state clearer within the waypoint list
- [x] Use the task pill itself as the edit control in waypoint edit mode, including the `No task` state
- [ ] Ensure the active task editor reads as attached to its waypoint row rather than a detached block
- [ ] Keep transport and transfer editing flows visually consistent with the surrounding fleet UI

Unit tests:
- [x] Update `frontend/src/components/FleetDetail.test.tsx` for pill-triggered task editing
- [ ] Extend `frontend/src/components/DetailPanel.test.tsx` to cover the updated task-edit interaction

## Step 3: Validation and finish

- [ ] Verify validation errors remain visible and understandable after the UI changes
- [ ] Run `cd frontend && npm test`
- [ ] Run `cd frontend && npm run lint`
- [ ] Run `cd frontend && npx tsc --noEmit`
