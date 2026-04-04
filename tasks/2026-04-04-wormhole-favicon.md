# Wormhole favicon

Implement a custom browser favicon for the frontend, matching the PR feedback to use a wormhole theme.

## Step 1: Add favicon asset

- [x] Add a `frontend/public/favicon.svg` asset with a wormhole-inspired design suitable for small tab rendering
- [x] Keep the icon high-contrast so it remains recognisable at favicon sizes

Unit tests:
- [x] Not applicable for static SVG asset

## Step 2: Wire favicon in HTML shell

- [x] Confirm the frontend HTML head links to `/favicon.svg`
- [x] Add explicit `sizes="any"` for SVG favicon semantics

Unit tests:
- [x] Not applicable for static HTML metadata change

## Step 3: Validation

- [x] `cd frontend && npm run lint`
