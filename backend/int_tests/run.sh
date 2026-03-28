#!/usr/bin/env bash
# Run integration tests against the backend container.
# Usage: ./run.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

cleanup() {
    echo "Tearing down containers..."
    docker compose down -v --remove-orphans 2>/dev/null || true
}
trap cleanup EXIT

echo "Building and starting backend..."
docker compose up -d --build --wait

echo "Running integration tests..."
cd "$SCRIPT_DIR/.."
uv run pytest int_tests/ -v --tb=short

echo "All integration tests passed ✅"
