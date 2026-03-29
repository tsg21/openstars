#!/bin/sh

uv run batch_generate_openai.py --count-per-class=3 --output-dir=./images
uv run generate_manifest.py --input-dir=./images \
  --base-url=https://storage.googleapis.com/openstars-assets/images/ \
  --output=images/manifest.json
gcloud storage rsync --recursive ./images/ gs://openstars-assets/images/