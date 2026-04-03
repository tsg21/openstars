# Game Lobby Cover Art

Incorporate the hosted `stars.jpg` cover art into the game lobby without copying the asset into the repository.

## Step 1: Add the hosted art as a faded lobby background

- [x] Keep the existing lobby layout intact
- [x] Reference the hosted cover art directly from Google Cloud Storage behind the lobby content
- [x] Fade the art into the background so the existing UI remains readable

Unit tests:
- [x] Update `frontend/src/components/GameLobby.test.tsx` to assert the cover art is rendered from the hosted URL

Validation:
- [x] `cd frontend && npm test`
- [x] `cd frontend && npm run lint`
- [x] `cd frontend && npx tsc --noEmit`

## Step 5: Fix the framed art to a centred box

- [x] Replace the viewport-relative frame with a centred fixed-size background box
- [x] Set the hosted cover art frame to `850x700` while preserving the existing lobby layout

Unit tests:
- [x] No additional tests needed; existing lobby coverage still applies

Validation:
- [x] `cd frontend && npm test`
- [x] `cd frontend && npm run lint`
- [x] `cd frontend && npx tsc --noEmit`

## Step 4: Increase the outer frame

- [x] Expand the inset around the background art so the border reads much more strongly
- [x] Keep the existing lobby content position unchanged while widening the framed margin

Unit tests:
- [x] No additional tests needed; existing lobby coverage still applies

Validation:
- [x] `cd frontend && npm test`
- [x] `cd frontend && npm run lint`
- [x] `cd frontend && npx tsc --noEmit`

## Step 3: Add a framed edge around the background art

- [x] Pull the hosted cover art in from the viewport edges instead of letting it fully fill the screen
- [x] Add a subtle outer border so the background reads like a framed backdrop behind the existing layout

Unit tests:
- [x] No additional tests needed; existing lobby coverage still applies

Validation:
- [x] `cd frontend && npm test`
- [x] `cd frontend && npm run lint`
- [x] `cd frontend && npx tsc --noEmit`

## Step 2: Tune the background fade

- [x] Reduce the dark wash so the hosted art reads more clearly behind the existing layout
- [x] Keep the lobby content readable while making the art noticeably more visible

Unit tests:
- [x] No additional tests needed; existing lobby coverage still applies

Validation:
- [x] `cd frontend && npm test`
- [x] `cd frontend && npm run lint`
- [x] `cd frontend && npx tsc --noEmit`
