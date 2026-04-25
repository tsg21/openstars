#!/usr/bin/env bash
set -euo pipefail

if [[ $# -eq 0 ]]; then
  echo "Usage: $0 <npm-args...>"
  echo "Example: $0 run lint"
  exit 1
fi

env -u npm_config_http_proxy -u npm_config_https_proxy npm "$@"
