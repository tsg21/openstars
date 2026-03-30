#!/usr/bin/env bash
set -euo pipefail

cd /Users/tim/code/openstars

PROMPT='In tasks/2026-03-30-stars-manual-chapter-cleanup.md, cleanup the next incomplete chapter and mark it done. Just do one chapter'

for _ in {1..1}; do
  codex exec "$PROMPT"
  sleep 1
done
