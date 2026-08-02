#!/bin/bash
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

# Load nvm and install Node 24
export NVM_DIR="/opt/nvm"
# shellcheck source=/dev/null
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh" --no-use
nvm install 24 --no-progress
nvm use 24

# Frontend dependencies
cd "$CLAUDE_PROJECT_DIR/frontend"
npm install

# Backend dependencies
cd "$CLAUDE_PROJECT_DIR/backend"
uv sync --all-extras
