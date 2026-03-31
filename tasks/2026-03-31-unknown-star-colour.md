# Unknown Star Colour

Makes stars with no known owner render in a brighter pale neutral tone regardless of current scanner coverage.

## Step 1: Map rendering

- [x] Update [`frontend/src/components/GalaxyMap.tsx`](/Users/tim/code/openstars/frontend/src/components/GalaxyMap.tsx) so unknown-owner planets use the ownership colour path even when `scanLevel` is `none`
- [x] Brighten the shared unknown/uncolonised planet colour token in [`frontend/src/index.css`](/Users/tim/code/openstars/frontend/src/index.css)
- [x] Cover the map rendering regression in [`frontend/src/components/GalaxyMap.test.tsx`](/Users/tim/code/openstars/frontend/src/components/GalaxyMap.test.tsx)

## Step 2: Map controls

- [x] Add a compact top-row toggle strip to [`frontend/src/components/GalaxyMap.tsx`](/Users/tim/code/openstars/frontend/src/components/GalaxyMap.tsx)
- [x] Add toggles for planet names and scanner overlays
- [x] Cover the map controls and label toggle rendering in [`frontend/src/components/GalaxyMap.test.tsx`](/Users/tim/code/openstars/frontend/src/components/GalaxyMap.test.tsx)

## Step 3: Hover affordance

- [x] Add a hover popover in [`frontend/src/components/GalaxyMap.tsx`](/Users/tim/code/openstars/frontend/src/components/GalaxyMap.tsx) to signal that planets are clickable
- [x] Show the hovered planet name with a brief selection hint
- [x] Cover hover show/hide behavior in [`frontend/src/components/GalaxyMap.test.tsx`](/Users/tim/code/openstars/frontend/src/components/GalaxyMap.test.tsx)

## Step 4: Verification

- [x] Run `cd frontend && npm test`
- [x] Run `cd frontend && npx tsc --noEmit`
- [x] Run `cd frontend && npm run lint`
