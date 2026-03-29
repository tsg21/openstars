# Batch planet image generation script (480x480)

## Goal
Provide a runnable script to batch-generate planet images and save normalized 480x480 outputs for external static hosting.

## Steps
- [x] Add batch generation script for OpenAI Images API.
- [x] Set default final image size to 480x480.
- [x] Update pipeline guide with script usage and 480x480 recommendation.

## Status
✅ Complete

## Notes
- Script writes class-based filenames suitable for manifest generation.
- Defaults request size to 1024x1024 from provider and resizes locally to 480x480.
