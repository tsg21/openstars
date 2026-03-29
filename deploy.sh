#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="openstars"
REGION="europe-west1"
REGISTRY="europe-west1-docker.pkg.dev"
REPOSITORY="openstars-frontend"

if [[ "${1:-}" == "frontend" ]]; then
  IMAGE_NAME="frontend"
  SERVICE="openstars-frontend"
else
  IMAGE_NAME="backend"
  SERVICE="backend"
fi

# Get the latest image tag from Artifact Registry
LATEST_TAG=$(gcloud artifacts docker tags list \
"${REGISTRY}/${PROJECT_ID}/${REPOSITORY}/${IMAGE_NAME}" \
--sort-by="~tag" \
--limit=1 \
--format="value(tag)" \
| head -1)

IMAGE="${REGISTRY}/${PROJECT_ID}/${REPOSITORY}/${IMAGE_NAME}:${LATEST_TAG}"

# Check currently deployed image
CURRENT_IMAGE=$(gcloud run services describe "${SERVICE}" \
  --region "${REGION}" \
  --project "${PROJECT_ID}" \
  --format="value(spec.template.spec.containers[0].image)" 2>/dev/null || echo "")

if [[ "${CURRENT_IMAGE}" == "${IMAGE}" ]]; then
  echo "No-op: ${SERVICE} is already running ${IMAGE}"
  exit 0
fi

echo "Deploying: ${IMAGE}"

gcloud run deploy "${SERVICE}" \
  --image "${IMAGE}" \
  --region "${REGION}" \
  --project "${PROJECT_ID}"