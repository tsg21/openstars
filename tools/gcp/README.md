# GCP Helpers

## `create_game_state_bucket.sh`

Creates the game-state bucket for the backend and grants the backend Cloud Run
runtime service account object-level access to it.

Example:

```bash
PROJECT_ID=openstars \
BUCKET_NAME=openstars-games \
./tools/gcp/create_game_state_bucket.sh
```

If the backend service account cannot be discovered automatically from the
Cloud Run service, provide it directly:

```bash
PROJECT_ID=openstars \
BUCKET_NAME=openstars-games \
BACKEND_SERVICE_ACCOUNT=backend@openstars.iam.gserviceaccount.com \
./tools/gcp/create_game_state_bucket.sh
```

If your Cloud Run region and bucket location differ, set them separately:

```bash
PROJECT_ID=openstars \
BUCKET_NAME=openstars-games \
RUN_REGION=europe-west1 \
BUCKET_LOCATION=eu \
./tools/gcp/create_game_state_bucket.sh
```

The script:

- creates the bucket if it does not already exist
- enables uniform bucket-level access
- enforces public access prevention
- enables object versioning
- grants `roles/storage.objectAdmin` on that bucket to the backend service account
