#!/usr/bin/env bash
# Run integration tests against the backend container.
# Usage: ./run.sh [test-name]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

COMPOSE_FILE="$SCRIPT_DIR/docker-compose.yaml"
LOG_DIR="$SCRIPT_DIR/logs"
LOG_FILE="$LOG_DIR/docker-compose.log"

cleanup() {
    mkdir -p "$LOG_DIR"
    echo "Writing container logs to $LOG_FILE..."
    docker compose -f "$COMPOSE_FILE" logs --no-color >"$LOG_FILE" 2>&1 || true
    echo "Tearing down containers..."
    docker compose -f "$COMPOSE_FILE" down -v --remove-orphans 2>/dev/null || true
}
trap cleanup EXIT

echo "Building and starting backend..."
docker compose -f "$COMPOSE_FILE" up -d --build --wait

echo "Running integration tests..."
cd "$SCRIPT_DIR/.."

if [[ $# -gt 0 ]]; then
    TEST_FILTER="$1"
    echo "Filtering tests with: $TEST_FILTER"
    uv run pytest int_tests/ -k "$TEST_FILTER" -v --tb=short
else
    uv run pytest int_tests/ -v --tb=short
fi

echo "All integration tests passed ✅"
echo "Container logs available at $LOG_FILE"
