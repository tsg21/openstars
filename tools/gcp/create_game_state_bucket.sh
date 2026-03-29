#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Create the GCS bucket used for OpenStars game state and grant access to the
backend Cloud Run runtime service account.

Required environment variables:
  PROJECT_ID            GCP project id
  BUCKET_NAME           Name of the bucket to create

Optional environment variables:
  BUCKET_LOCATION       Bucket location (default: europe-west1)
  RUN_REGION            Cloud Run region for the backend service (default: europe-west1)
  STORAGE_CLASS         Bucket storage class (default: STANDARD)
  BACKEND_SERVICE       Cloud Run backend service name to inspect (default: backend)
  BACKEND_SERVICE_ACCOUNT
                        Runtime service account email. If unset, the script
                        reads it from the Cloud Run service.

Examples:
  PROJECT_ID=openstars \
  BUCKET_NAME=openstars-games \
  ./tools/gcp/create_game_state_bucket.sh

  PROJECT_ID=openstars \
  BUCKET_NAME=openstars-games \
  BACKEND_SERVICE_ACCOUNT=backend@openstars.iam.gserviceaccount.com \
  ./tools/gcp/create_game_state_bucket.sh
EOF
}

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

PROJECT_ID="${PROJECT_ID:-}"
BUCKET_NAME="${BUCKET_NAME:-}"
BUCKET_LOCATION="${BUCKET_LOCATION:-europe-west1}"
RUN_REGION="${RUN_REGION:-europe-west1}"
STORAGE_CLASS="${STORAGE_CLASS:-STANDARD}"
BACKEND_SERVICE="${BACKEND_SERVICE:-backend}"
BACKEND_SERVICE_ACCOUNT="${BACKEND_SERVICE_ACCOUNT:-}"

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if [[ -z "${PROJECT_ID}" || -z "${BUCKET_NAME}" ]]; then
  usage >&2
  exit 1
fi

require_cmd gcloud

BUCKET_URL="gs://${BUCKET_NAME}"

echo "Using project: ${PROJECT_ID}"
echo "Using bucket: ${BUCKET_URL}"

if ! gcloud storage buckets describe "${BUCKET_URL}" --project "${PROJECT_ID}" >/dev/null 2>&1; then
  echo "Creating bucket ${BUCKET_URL} in ${BUCKET_LOCATION}..."
  gcloud storage buckets create "${BUCKET_URL}" \
    --project "${PROJECT_ID}" \
    --location "${BUCKET_LOCATION}" \
    --default-storage-class "${STORAGE_CLASS}" \
    --uniform-bucket-level-access \
    --public-access-prevention
else
  echo "Bucket already exists: ${BUCKET_URL}"
fi

echo "Enabling object versioning..."
gcloud storage buckets update "${BUCKET_URL}" \
  --project "${PROJECT_ID}" \
  --versioning

if [[ -z "${BACKEND_SERVICE_ACCOUNT}" ]]; then
  echo "Resolving runtime service account from Cloud Run service ${BACKEND_SERVICE}..."
  BACKEND_SERVICE_ACCOUNT="$(
    gcloud run services describe "${BACKEND_SERVICE}" \
      --project "${PROJECT_ID}" \
      --region "${RUN_REGION}" \
      --format="value(spec.template.spec.serviceAccountName)"
  )"
fi

if [[ -z "${BACKEND_SERVICE_ACCOUNT}" ]]; then
  echo "Could not determine backend service account." >&2
  echo "Set BACKEND_SERVICE_ACCOUNT explicitly or deploy the backend service first." >&2
  exit 1
fi

echo "Granting bucket-scoped Storage Object Admin to ${BACKEND_SERVICE_ACCOUNT}..."
gcloud storage buckets add-iam-policy-binding "${BUCKET_URL}" \
  --project "${PROJECT_ID}" \
  --member "serviceAccount:${BACKEND_SERVICE_ACCOUNT}" \
  --role "roles/storage.objectAdmin"

cat <<EOF

Bucket setup complete.

Next steps:
  1. Set STORAGE_BACKEND=gcs on the backend Cloud Run service.
  2. Set GCS_BUCKET_NAME=${BUCKET_NAME} on the backend Cloud Run service.
  3. Redeploy the backend if needed.
EOF
