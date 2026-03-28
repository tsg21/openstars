#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="openstars"
REGION="europe-west1"
REGISTRY="europe-west1-docker.pkg.dev"
REPOSITORY="openstars-frontend"
IMAGE_NAME="frontend"
SERVICE="openstars-frontend"

# Get the latest image tag from Artifact Registry
LATEST_TAG=$(gcloud artifacts docker tags list \
"${REGISTRY}/${PROJECT_ID}/${REPOSITORY}/${IMAGE_NAME}" \
--sort-by="~tag" \
--limit=1 \
--format="value(tag)" \
| head -1)

IMAGE="${REGISTRY}/${PROJECT_ID}/${REPOSITORY}/${IMAGE_NAME}:${LATEST_TAG}"
echo "Deploying: ${IMAGE}"

gcloud run deploy "${SERVICE}" \
--image "${IMAGE}" \
--region "${REGION}" \
--project "${PROJECT_ID}"