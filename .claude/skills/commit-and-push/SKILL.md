---
name: commit-and-push
description: Commits local changes to git and pushes them to the remote GitHub repository.
---

## Commit Message Style

- Subject line: short imperative ("Add X", "Move Y", "Clarify Z"), capitalised first word, no trailing period, no Conventional Commits prefix (`feat:`, `fix:`), no scope tags.
- When the change targets a PRD, end the subject with `in PRD N` (e.g. `Store research progress per field in PRD 21`).
- For non-trivial changes, add a body explaining the *why*, not the *what* — the diff shows what changed.
- Keep `Co-Authored-By: <model>` trailer on agent-authored commits.

## Pre-commit checks

- Skip the `git log` inspection step. The style is fully specified above; recent commits are not a source of style guidance for this repo. Run `git status` and `git diff` only.