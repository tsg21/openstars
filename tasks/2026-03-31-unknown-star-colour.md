# Unknown Star Colour

Makes stars with no known owner render in a brighter pale neutral tone regardless of current scanner coverage.

## Step 1: Map rendering

- [x] Update [`frontend/src/components/GalaxyMap.tsx`](/Users/tim/code/openstars/frontend/src/components/GalaxyMap.tsx) so unknown-owner planets use the ownership colour path even when `scanLevel` is `none`
- [x] Brighten the shared unknown/uncolonised planet colour token in [`frontend/src/index.css`](/Users/tim/code/openstars/frontend/src/index.css)
- [x] Cover the map rendering regression in [`frontend/src/components/GalaxyMap.test.tsx`](/Users/tim/code/openstars/frontend/src/components/GalaxyMap.test.tsx)

## Step 2: Verification

- [x] Run `cd frontend && npm test`
- [x] Run `cd frontend && npx tsc --noEmit`
- [x] Run `cd frontend && npm run lint`
