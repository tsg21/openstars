# Component Image Modernisation — Notes

## Goal

Replace the original Stars! (1995) component GIFs with clean PNGs on a black
background, removing the grey panel frame and border artifacts.

## What we've done

1. **Explored the originals** — 183 GIF images in GCS at
   `gs://openstars-assets/components/`. Each is 64×64 with a classic Win95-style
   sunken panel: 1px black outer border, 1px white inner highlight, grey (192,192)
   fill, component in the centre.

2. **Tried flood-fill removal** — a Python/Pillow BFS flood-fill from the image
   edges. It removed most of the grey background but left two problems:
   - A 1px dark-grey shadow strip along the bottom and right edges (palette colours
     ~122–133 that fell between the black and grey tolerance buckets).
   - A grey anti-aliasing halo around component edges where the original GIF blended
     component pixels into the background.

3. **Switched to the OpenAI image edit API** — `upscale_starbmp.py` sends each GIF
   to `gpt-image-2` with a prompt asking it to place the component on a solid black
   background. This cleanly solves both problems with no halo and no border strip.

## Current state of the script

`tools/upscale_starbmp.py`:
- Accepts a single GIF/PNG **or** a directory as positional input
- Defaults: `gpt-image-2`, `medium` quality, `--target-size 64` (resizes the
  1024×1024 API output back to 64×64)
- `--skip-existing` flag for resumable batch runs
- `--limit N` for testing subsets

Run example:
```
source ~/.openai/openstars
uv run --with openai,pillow tools/upscale_starbmp.py tmp/components_src/components/armor/tritanium.gif
```

## Next steps

1. **Batch run** — run the script over all 183 GIFs in
   `tmp/components_src/components/`. Estimated cost: ~1846 tokens/image.
   ```
   uv run --with openai,pillow tools/upscale_starbmp.py \
     tmp/components_src/components/ \
     --output tmp/components_ai/ \
     --skip-existing
   ```
2. **Review output** — generate contact sheets (as before) and check quality
   across all categories.
3. **Upload to GCS** — `gsutil -m cp -r tmp/components_ai/ gs://openstars-assets/components/`
4. **Update manifest** — change all `.gif` → `.png` in
   `frontend/src/assets/components/manifest.json`.
5. **Wire up** — confirm `componentImages.ts` and the designer UI pick up the
   new PNGs correctly.

## Notes / gotchas

- `gpt-image-2` **does not** support `background="transparent"` in the edit API
  (403 error). Black background + chroma key later is the workaround.
- `gpt-image-1` does support transparent output but the org key was billing-limited
  at time of testing.
- Engine entries in the manifest have both an `image` and a `graph` field (fuel
  consumption charts). The graphs are also GIFs and will need the same treatment,
  but may look odd since they contain text/chart elements — worth checking separately.
- Source downloads are cached in `tmp/components_src/`. No need to re-download.
