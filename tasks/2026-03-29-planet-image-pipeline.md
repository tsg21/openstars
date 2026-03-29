# Planet image pipeline (external static hosting)

## Goal
Provide a practical path for generating and hosting static planet images outside the frontend repository.

## Steps
- [x] Document recommended external asset pipeline (generation, manifest, hosting, versioning).
- [x] Add helper script to build manifest JSON from generated image outputs.
- [x] Include deterministic image-selection guidance to keep visuals stable by planet id.

## Status
✅ Complete

## Notes
- No frontend runtime change was made in this task.
- This is intentionally decoupled so assets can be hosted in GCS/CDN independently of app deploys.
