#!/bin/sh

export STORAGE_BACKEND=local
export GAME_DATA_PATH=../local-data
uv run uvicorn openstars.server.main:app --host 0.0.0.0 --port 8080