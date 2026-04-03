# Single-Player Game Creation

Allow creating a game with a single human player to speed up local testing.

## Step 1: Update API contract and validation

- [x] Allow `CreateGameRequest.players` to contain a single username
- [x] Update create-game route validation to accept one player
- [x] Update API docs to reflect minimum player count of 1

Unit tests:
- [x] Update schema tests for single-player create requests
- [x] Update API tests to assert single-player game creation succeeds

Validation:
- [x] `cd backend && uv run pytest backend/tests/server/test_schemas.py backend/tests/server/test_api.py`

## Step 2: Update lobby create-game UX

- [x] Allow the frontend create-game form to submit with a single username
- [x] Default the testing-friendly player input to a single player

Unit tests:
- [x] No additional frontend tests added for this small validation change

Validation:
- [x] `cd frontend && npm run lint`

## Step 3: Final quality gate

- [x] Backend lint: `cd backend && uv run ruff check .`
- [x] Frontend lint: `cd frontend && npm run lint`
