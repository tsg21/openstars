# Light-year terminology migration

**Date:** 2026-04-25
**Goal:** Replace active game terminology that currently refers to parsecs with light-years, while preserving the existing coordinate scale and movement mechanics.

## Step 1 — PRD terminology updates
- [x] Update PRDs that define or reference distance/scanner units to use light-year wording and `ly` abbreviation.
- [x] Keep the numeric conversion unchanged (`1 light-year = 2^29 coordinate units`).

## Step 2 — Backend terminology updates
- [x] Rename distance unit constant and related identifiers from parsec to light-year in engine modules.
- [x] Update comments/docstrings/model field comments to light-year wording.

## Step 3 — Frontend terminology updates
- [x] Rename shared unit constant and related helpers from parsec to light-year.
- [x] Update user-facing and developer-facing comments/test names for the new unit wording.

## Step 4 — Test and fixture alignment
- [x] Update backend and frontend tests to use renamed constants/identifiers and light-year wording.

## Step 5 — Validation
- [x] Run backend lint + format check + tests.
- [x] Run frontend lint + typecheck + tests.
- [x] Confirm there are no remaining parsec/`PARSEC` references in active code/PRDs.

## Notes
- Historical task records are left unchanged unless specifically requested.
- Reference material under `docs/references/` is left unchanged because it documents the original game terminology.
