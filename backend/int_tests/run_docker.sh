#!/usr/bin/env bash
# Mirrors the "integration" job in .github/workflows/backend-ci.yml locally.
set -euo pipefail

cd "$(dirname "$0")/.."

cleanup() {
    echo "--- Tearing down containers ---"
    docker compose -f int_tests/docker-compose.yaml down -v --remove-orphans
}
trap cleanup EXIT

echo "--- Install dependencies ---"
uv sync --locked --extra dev --group dev

echo "--- Start backend container ---"
docker compose -f int_tests/docker-compose.yaml up -d --build --wait

echo "--- Run integration tests ---"
if ! uv run pytest int_tests/ -v --tb=short; then
    echo "--- Show container logs on failure ---"
    docker compose -f int_tests/docker-compose.yaml logs --no-color
    exit 1
fi
