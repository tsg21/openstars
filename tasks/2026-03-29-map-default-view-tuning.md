# Map default view tuning

## Goal
Show more of the galaxy on screen by widening the fixed default viewport without reintroducing zoom controls.

## Steps
- [x] Review the fixed-scale viewport implementation and identify the single source of truth for the map zoom level.
- [x] Adjust the default/effective fixed scale so the map shows about twice as much galaxy space at once.
- [x] Update tests and record the change.

## Status
✅ Complete

## Notes
- The fixed viewport now shows roughly 400 parsecs across 1000 pixels instead of 200.
- This keeps the no-zoom interaction model from March 28 while making the default map framing less cramped.
