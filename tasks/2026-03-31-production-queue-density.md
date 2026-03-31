# Production Queue Density Refinement

Refines the owned-planet production queue UI from the initial PRD 13 implementation into a denser editor with one row per queue item and a single add-item picker.

## Step 1: Compact queue row layout

- [x] Replace the card-per-item layout in [`frontend/src/components/DetailPanel.tsx`](/Users/tim/code/openstars/frontend/src/components/DetailPanel.tsx) with a denser single-row presentation
- [x] Keep quantity, current-unit progress, reordering, and removal visible in each row
- [x] Preserve the existing queue editing behavior while reducing vertical space
- [x] Cover the updated row rendering in [`frontend/src/components/DetailPanel.test.tsx`](/Users/tim/code/openstars/frontend/src/components/DetailPanel.test.tsx)

## Step 2: Add-item popup picker

- [x] Replace the separate add buttons with a single top-level `+` trigger
- [x] Show a lightweight popup picker listing available queue item types
- [x] Keep currently supported Phase 1 types actionable and show unsupported future types as unavailable placeholders
- [x] Cover the picker interaction in [`frontend/src/components/DetailPanel.test.tsx`](/Users/tim/code/openstars/frontend/src/components/DetailPanel.test.tsx)

## Step 3: Verification

- [x] Run `cd frontend && npm test`
- [x] Run `cd frontend && npx tsc --noEmit`
- [x] Run `cd frontend && npm run lint`

## Notes

- The picker now lists future production categories such as ships, but only `mine` and `factory` are enabled because backend command validation is still limited to Phase 1 production types from PRD 13.
- The queue row was simplified again after the initial density pass: it now shows label, quantity, quantity controls, and remove action, while progress display is deferred for a later refinement.
- The temporary blocked-state explanatory copy was removed from the panel to keep the production editor focused on the queue controls.
- Queue-level actions now live together in the header, with a `ListX` icon button used for clear-queue so it reads differently from the per-row trash action.
