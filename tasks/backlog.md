# Backlog — Non-urgent improvements & tech debt

Items that aren't blocking current work but should be done at some point.
Add new items at the bottom. Check off when done.

---

## Infrastructure / Tooling

- [ ] **Upgrade Node to 24** — Dockerfile (`node:22-alpine`), CI workflow (`node-version: 22`), and any `.nvmrc` / `engines` in package.json. Node 22 works fine but 24 is current LTS.
- [ ] **Use `tsc -b` locally, not just `tsc --noEmit`** — CI runs `tsc -b` (via `npm run build`) which enforces `erasableSyntaxOnly` from tsconfig.app.json. Local `tsc --noEmit` doesn't catch this. Consider adding a `npm run typecheck` script that runs `tsc -b --noEmit`.
- [ ] **Backend CI workflow** — currently only frontend has a GitHub Actions workflow. Add one for the backend (ruff check, ruff format --check, pytest).
- [ ] **Clean up old local branches** — dozens of stale branches from merged PRs (e.g. `prd-01-overview`, `scaffold-project-structure`, `step-5-pan-and-zoom`, etc.). Run `git branch -d` on merged ones.

## Frontend

- [ ] **Remove mock data files when no longer needed** — `mocks/galaxy.ts`, `mocks/playerState.ts` are still used by some tests (GalaxyMap, mock-data). Decide whether to keep them for testing or replace with lighter fixtures.
- [ ] **Add loading/error states to GameLobby** — e.g. retry button on game list failure, better create-game validation.

## Backend

- [ ] **GCS storage adapter** — `storage/gcs.py` implementing `GameStorage` for production. Currently only `LocalStorage` exists.
