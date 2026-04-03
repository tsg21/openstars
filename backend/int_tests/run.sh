#!/usr/bin/env bash
# Run integration tests against a locally launched backend process.
# Usage: ./run.sh [test-name]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$SCRIPT_DIR"

LOG_DIR="$SCRIPT_DIR/logs"
LOG_FILE="$LOG_DIR/backend.log"
PID_FILE="$LOG_DIR/backend.pid"
API_URL="${API_URL:-http://127.0.0.1:8080}"

cleanup() {
    mkdir -p "$LOG_DIR"

    if [[ -f "$PID_FILE" ]]; then
        BACKEND_PID="$(cat "$PID_FILE")"
        if kill -0 "$BACKEND_PID" 2>/dev/null; then
            echo "Stopping backend process ($BACKEND_PID)..."
            kill "$BACKEND_PID" 2>/dev/null || true
            wait "$BACKEND_PID" 2>/dev/null || true
        fi
        rm -f "$PID_FILE"
    fi

    echo "Backend logs available at $LOG_FILE"
}
trap cleanup EXIT

mkdir -p "$LOG_DIR"

export STORAGE_BACKEND="memory"
export LOG_LEVEL="debug"

echo "Starting backend on $API_URL ..."
cd "$BACKEND_DIR"
uv run --all-extras uvicorn openstars.server.main:app --host 127.0.0.1 --port 8080 >"$LOG_FILE" 2>&1 &
BACKEND_PID=$!
echo "$BACKEND_PID" >"$PID_FILE"

export API_URL

# Wait for service readiness (up to 30s).
uv run --all-extras python - <<'PY'
import os
import time

import requests

base_url = os.environ["API_URL"]
health_url = f"{base_url}/api/v1/health"

deadline = time.time() + 30
while time.time() < deadline:
    try:
        response = requests.get(health_url, timeout=2)
        if response.status_code == 200:
            print(f"Backend is ready at {health_url}")
            raise SystemExit(0)
    except requests.RequestException:
        pass
    time.sleep(0.5)

raise SystemExit(f"Backend not ready after 30s: {health_url}")
PY

echo "Running integration tests..."
if [[ $# -gt 0 ]]; then
    TEST_FILTER="$1"
    echo "Filtering tests with: $TEST_FILTER"
    uv run --all-extras pytest int_tests/ -k "$TEST_FILTER" -v --tb=short
else
    uv run --all-extras pytest int_tests/ -v --tb=short
fi

echo "All integration tests passed ✅"
