#!/bin/sh

# The model to use for image generation. One of dall-e-2, dall-e-3, or a GPT image model (gpt-image-1, gpt-image-1-mini, gpt-image-1.5). Defaults to dall-e-2 unless a parameter specific to the GPT image models is used.

uv run batch_generate_openai.py --count-per-class=3 --output-dir=./images --model=dall-e-3
uv run generate_manifest.py --input-dir=./images \
  --base-url=https://storage.googleapis.com/openstars-assets/images/ \
  --output=images/manifest.json
gcloud storage rsync --recursive ./images/ gs://openstars-assets/images/