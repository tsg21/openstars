# Waypoint UI Iteration

Follow-up frontend polish for waypoint editing and review in the fleet detail panel. The functional waypoint task flow already exists; this task tracks a smaller pass focused on clarity, layout, and ease of use while preserving the current behaviour.

## Step 1: Refine waypoint row presentation

- [x] Review the current waypoint list in `frontend/src/components/FleetDetail.tsx`
- [x] Show the planet name in the waypoint list when a destination matches a planet, falling back to coordinates only for deep-space waypoints
- [x] Improve the visual hierarchy of each waypoint row so destination, ETA, and task status are easier to scan
- [x] Remove circled waypoint numbers so the list leads with the destination label and uses space more efficiently
- [x] Combine waypoint controls into the main waypoint panel and keep the repeat route checkbox visible outside edit mode
- [x] Tighten spacing and button placement in edit mode so task editing feels less cramped

Unit tests:
- [x] Update `frontend/src/components/FleetDetail.test.tsx` to cover planet-name waypoint labels
- [x] Update `frontend/src/components/FleetDetail.test.tsx` for the always-visible repeat route control
- [ ] Update `frontend/src/components/DetailPanel.test.tsx` for any changed labels, roles, or visible waypoint metadata

## Step 2: Improve inline task editing affordances

- [x] Make the task editor entry point and open state clearer within the waypoint list
- [x] Use the task pill itself as the edit control in waypoint edit mode, including the `No task` state
- [x] Move task-type selection into a compact popover so the inline panel is reserved for task-specific editing
- [x] Ensure transport and transfer order details stay attached to their waypoint row instead of appearing as a temporary panel
- [ ] Keep transport and transfer editing flows visually consistent with the surrounding fleet UI

Unit tests:
- [x] Update `frontend/src/components/FleetDetail.test.tsx` for pill-triggered task editing
- [x] Update `frontend/src/components/FleetDetail.test.tsx` for popover-based task-type selection
- [x] Update `frontend/src/components/FleetDetail.test.tsx` to cover persistent transport and transfer order details
- [ ] Extend `frontend/src/components/DetailPanel.test.tsx` to cover the updated task-edit interaction

## Step 3: Validation and finish

- [x] Verify validation errors remain visible and understandable after the UI changes
- [x] Leave new cargo orders unset until the user chooses a cargo type, and block waypoint save while any order is incomplete
- [ ] Run `cd frontend && npm test`
- [ ] Run `cd frontend && npm run lint`
- [ ] Run `cd frontend && npx tsc --noEmit`
