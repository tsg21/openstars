# Planet Image Pipeline (External Static Assets)

This guide describes a simple way to generate many planet images and host them outside the frontend repo (for example in a public/private GCS bucket).

## Recommended architecture

1. Generate planet images offline/in a separate tooling step.
2. Upload all generated images to a dedicated bucket path, e.g.:
   - `gs://openstars-assets/planets/v1/*.png`
3. Publish a manifest JSON in the same bucket, e.g.:
   - `gs://openstars-assets/planets/v1/manifest.json`
4. In the UI, build image URLs from either:
   - a deterministic key (`planetType` + `variant`), or
   - direct URL lookup from `manifest.json`.

This keeps binary assets and generation tooling out of the main UI codebase while still making image lookup deterministic and cacheable.

## Bucket layout

```text
gs://openstars-assets/
  planets/
    v1/
      manifest.json
      terrestrial-001.png
      terrestrial-002.png
      gas-giant-001.png
      ice-001.png
      lava-001.png
```

## Manifest format

Use a compact manifest so the client can choose a consistent image per planet id.

```json
{
  "version": "v1",
  "baseUrl": "https://storage.googleapis.com/openstars-assets/planets/v1",
  "imagesByClass": {
    "terrestrial": [
      "terrestrial-001.png",
      "terrestrial-002.png"
    ],
    "gas_giant": [
      "gas-giant-001.png"
    ],
    "ice": ["ice-001.png"],
    "lava": ["lava-001.png"]
  }
}
```

## Deterministic selection strategy

To avoid image "flicker" between sessions:

- assign each planet a class (`terrestrial`, `gas_giant`, etc.)
- compute `index = hash(planetId) % imagesByClass[class].length`
- use that image filename consistently

This allows many planets to reuse a finite pool of generated assets while preserving stable visuals.

## Generation workflow

1. Create a prompt catalog with one prompt per output image.
2. Run batch generation (OpenAI Images API, or any image model/tooling you choose).
3. Run a quick quality pass (remove obvious artifacts).
4. Normalize files to fixed dimensions and naming convention.
5. Normalize outputs to `480x480` PNG/WebP for UI use.
6. Build `manifest.json`.
7. Upload files + manifest to GCS.
8. Version by path (`v1`, `v2`) rather than replacing in place.

## Operational recommendations

- Keep final UI images square at `480x480` (generate larger if needed, then downscale).
- Add long-lived cache headers to versioned assets.
- Keep manifest small and cacheable; it can also be bundled server-side if preferred.
- Use lifecycle rules in GCS to clean stale experiment folders.
- Add moderation/safety filtering in generation stage before upload.

## Why this is usually the best approach

- No large binaries in the UI repository
- Easy CDN/browser caching
- Easy rollback by switching manifest/version
- Supports future style packs (e.g. `realistic`, `stylized`) with parallel manifests


## Batch generation script

Use the included batch script to generate planet images and save normalized `480x480` files:

```bash
OPENAI_API_KEY=... python tools/planet_images/batch_generate_openai.py \
  --output-dir ./planet-outputs \
  --count-per-class 12
```

Notes:
- Defaults to `--target-size 480`.
- Requests `1024x1024` from the API by default (`--api-size`) and downsamples to `480x480` (requires Pillow).
- If you do not want Pillow installed, use `--no-resize` and choose a provider size close to your target.
- Output files are named by class, e.g. `terrestrial-001.png`, ready for manifest generation.
