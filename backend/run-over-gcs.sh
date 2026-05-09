#!/bin/sh

export STORAGE_BACKEND=gcs
export GOOGLE_CLOUD_PROJECT=${GOOGLE_CLOUD_PROJECT:-openstars}
export GCS_BUCKET_NAME=openstars-games
uv run --all-extras uvicorn openstars.server.main:app --host 0.0.0.0 --port 8080
