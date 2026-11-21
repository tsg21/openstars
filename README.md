# OpenStars!

A modern web reimagining of [Stars!](https://en.wikipedia.org/wiki/Stars!) — the legendary 1995 turn-based 4X space strategy game.

The deployed version lives at [https://openstars.timgage.co.uk/](openstars.timgage.co.uk)

## What is this?

Stars! was a deeply complex, turn-based, play-by-email space strategy game that kept a devoted community playing for decades. It featured intricate race design, ship customisation, a detailed economic model, and a simultaneous-turn multiplayer system perfectly suited to asynchronous play.

OpenStars! aims to bring those mechanics to a modern web platform — faithful to the depth of the original, but with a contemporary UI and native browser-based multiplayer.

## Project Structure

<pre>
openstars/
├── <a href="frontend/">frontend/</a>                   # React + Vite SPA (TypeScript, Tailwind, shadcn/ui)
│   └── src/
│       ├── components/         # UI components (galaxy map, planet detail, fleet panels…)
│       ├── contexts/           # React contexts (game state, auth)
│       ├── hooks/              # Custom hooks
│       ├── api/                # Typed API client layer
│       └── types/              # Shared TypeScript types
│
├── <a href="backend/">backend/</a>                    # Python API server (FastAPI, Pydantic, pytest)
│   └── openstars/
│       ├── server/             # FastAPI routes and request handling
│       ├── engine/             # Turn resolution engine (pure, stateless, fully testable)
│       └── models/             # Pydantic game-state models
│
├── <a href="docs/">docs/</a>
│   ├── <a href="docs/prd/README.md">docs/prd/</a>               # Product requirement documents (canonical game spec)
│   │   ├── <a href="docs/prd/01-overview.md">01-overview.md</a>
│   │   ├── <a href="docs/prd/02-galaxy-map.md">02-galaxy-map.md</a>
│   │   ├── <a href="docs/prd/03-turn-lifecycle.md">03-turn-lifecycle.md</a>
│   │   ├── <a href="docs/prd/10-fleet-movement.md">10-fleet-movement.md</a>
│   │   ├── <a href="docs/prd/12-economy-and-resources.md">12-economy-and-resources.md</a>
│   │   ├── <a href="docs/prd/80-combat-fundamentals.md">80-combat-fundamentals.md</a>
│   │   └── …
│   └── <a href="docs/references/README.md">docs/references/</a>        # Original Stars! manual, battle engine notes, terminology
│       └── <a href="docs/references/manual/README.md">manual/</a>             # Extracted Stars! manual
│
├── <a href="infra/">infra/</a>                      # Terraform for GCP infrastructure (Cloud Run, Artifact Registry, IAM)
├── <a href="tasks/README.md">tasks/</a>                      # Dated task files tracking in-progress and completed work
└── <a href="docker-compose.yaml">docker-compose.yaml</a>
</pre>

### Architecture at a glance

The project follows a strict **command-and-resolve** model:

- The **frontend** is a pure order editor — it never runs game logic. Players issue commands (move fleet, set waypoints, queue production) which are collected and sent to the server.
- The **backend engine** receives all players' orders simultaneously and resolves them in a deterministic pipeline: `(previousState, allOrders) → newState`. The engine is entirely stateless and has no knowledge of HTTP.
- Clients receive fog-of-war-filtered state — the server is authoritative.

This keeps the engine independently testable and faithful to the original Stars! simultaneous-turn multiplayer model.

### Running locally

| Service | Command | Port |
|---------|---------|------|
| Backend API | `cd backend && ./run.sh` | 8080 |
| Frontend | `cd frontend && npm run dev` | 5173 |

Sign-in uses the **real** `openstars` Firebase project, so first-time setup is:

```sh
cp frontend/.env.example frontend/.env.local   # then set the real project values
gcloud auth application-default login          # backend verifies tokens with ADC
gcloud auth application-default set-quota-project openstars
```

The real values for `.env.local` come from the Firebase web app config — the same
call CI makes in [build-frontend.yml](.github/workflows/build-frontend.yml):

```sh
TOKEN=$(gcloud auth print-access-token)
APP_ID=$(curl -s -H "Authorization: Bearer $TOKEN" -H "X-Goog-User-Project: openstars" \
  "https://firebase.googleapis.com/v1beta1/projects/openstars/webApps" | jq -r '.apps[0].appId')
curl -s -H "Authorization: Bearer $TOKEN" -H "X-Goog-User-Project: openstars" \
  "https://firebase.googleapis.com/v1beta1/projects/openstars/webApps/$APP_ID/config"
```

Only *identity* is shared with production. The game directory is in-memory and
turn state is written to `local-data/`, so local play never reads or writes
production games — with the trade-off that the game list is empty again after
every backend restart, and realtime turn notifications stay silent (the browser
subscribes to Firestore documents that a local backend never writes).

### Running locally against the emulators

`docker compose up` runs the whole stack — frontend, backend and the Firebase
auth/Firestore emulators — against the throwaway `openstars-local` project. No
GCP credentials needed, and realtime notifications work end to end, but sign-in
is emulator-only rather than a real Google account.

## Licence

MIT License — see [LICENSE](LICENSE).
