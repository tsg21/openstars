# Firebase Local Emulator Config

This directory contains configuration for the [Firebase Local Emulator Suite](https://firebase.google.com/docs/emulator-suite), used for local development and integration tests.

## Files

- **`firebase.json`** — tells `firebase emulators:start` which emulators to run and what ports to bind
- **`.firebaserc`** — sets the default project alias (`openstars-local`) for local CLI use

## Emulators

| Emulator | Port |
|----------|------|
| Auth | 9099 |
| Firestore | 8085 |
| Emulator UI | 4001 |

## Usage

The emulators are started automatically by Docker Compose:

```bash
docker compose up firebase-emulators
# or the full stack:
docker compose up
```

The emulator UI is available at http://localhost:4001 when running.

These emulators are **not used in production** — they are purely a local dev/test tool.
