#!/bin/sh
#
# Local dev server: real Firebase auth, local game data.
#
# ID tokens are verified against the real `openstars` Firebase project, so the
# frontend signs in with a real Google account (see frontend/.env.local).
# Everything else stays on this machine — the game directory is in-memory and
# turn state is written to ../local-data, so nothing here touches production
# games in Firestore or the openstars-games bucket.
#
# Requires Application Default Credentials:
#   gcloud auth application-default login
#   gcloud auth application-default set-quota-project openstars

export STORAGE_BACKEND=local
export GAME_DATA_PATH=../local-data

# Token verification and the `games` custom claim both target the real project.
export FIREBASE_PROJECT_ID=${FIREBASE_PROJECT_ID:-openstars}
# ADC carries no default project; without this google-auth logs a warning on
# every credential refresh.
export GOOGLE_CLOUD_PROJECT=${GOOGLE_CLOUD_PROJECT:-$FIREBASE_PROJECT_ID}

# The directory is the one piece that must NOT be firestore: pointing it at the
# real project would list production games whose state files live only here.
export GAME_DIRECTORY_BACKEND=${GAME_DIRECTORY_BACKEND:-memory}

uv run uvicorn openstars.server.main:app --host 0.0.0.0 --port 8080
