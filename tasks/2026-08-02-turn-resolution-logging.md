# Turn resolution logging: sub-phase timing + game_id/turn context

**Date:** 2026-08-02

**Goal:** Turn resolution logging was all at `DEBUG` and gave no visibility into how long each sub-phase takes. Add INFO-level duration logging for each phase of both the engine pipeline (`resolve_turn`) and the server-side orchestration (`resolve_current_turn`), and make sure `game_id`/`turn` are always present as structured context for the full resolution, not just inside the engine call.

Investigation found the contextvar + `ContextFilter` infrastructure for `game_id`/`turn` already existed (`openstars/server/log_context.py`, `openstars/server/logging.py`), but `turn` was only set inside `resolve_turn`, leaving the surrounding load/persist/derive-player-state/notify phases in `resolution.py` without turn context. A couple of log calls also duplicated `game_id`/`turn` into the message string instead of relying on the filter.

---

## Step 1 — Add `log_duration` timing helper

- [x] Add `log_duration(logger, phase)` context manager to `backend/openstars/server/log_context.py` — logs `"<phase> done in X.Xms"` at INFO on exit (including on exception). Relies on the existing `game_id`/`turn` contextvars + `ContextFilter` for structured context, no `extra=` needed at call sites.
- [x] Unit tests in `backend/tests/server/test_log_context.py`:
  - `log_duration` logs elapsed time on normal exit
  - `log_duration` logs elapsed time even when the wrapped block raises
  - `ContextFilter` attaches `game_id`/`turn` onto the record when the contextvars are set
  - `ContextFilter` leaves `game_id`/`turn` unset on the record when the contextvars are unset

Relevant checks:
- `cd backend && uv run pytest tests/server/test_log_context.py`

---

## Step 2 — Instrument the engine pipeline (`resolve_turn`)

- [x] `backend/openstars/engine/resolve.py` — replace the `log.debug("resolve turn: ...")` markers with `log_duration(log, "resolve_turn.<phase>")` wrapping each step: `turn_zero`, `apply_commands`, `move_fleets`, `combat`, `mining`, `resources` (previously had no log line at all), `production`, `research`, `population`.

Relevant checks:
- `cd backend && uv run pytest tests/engine/test_resolve.py tests/engine/test_resolve_combat.py tests/engine/test_economy.py tests/engine/test_population.py tests/engine/race/test_turn_zero_resolution.py`

---

## Step 3 — Instrument server-side orchestration (`resolve_current_turn`) and fix `turn` context gap

- [x] `backend/openstars/server/resolution.py`:
  - Set the `turn` contextvar for the whole `resolve_current_turn` call (using `current_turn`), not just inside the nested `resolve_turn` call, so every log line in this function now carries `turn` context.
  - Wrap phases in `log_duration`: `resolution.load_state` (global state + galaxy + designs + commands), `resolution.engine` (the `resolve_turn` call), `resolution.persist_global_state`, `resolution.derive_player_states`, `resolution.turn_resolved_notify`.
  - Drop the redundant manual `game_id=%s` interpolation in the `resolution.turn_already_exists` warning now that the filter supplies it.
- [x] `backend/openstars/server/routes/play.py` — drop the same redundant `game_id=%s` interpolation from the `resolution.failed` error log.

Relevant checks:
- `cd backend && uv run pytest tests/server/test_submit_auto_resolve.py`
- `cd backend && uv run ruff check . && uv run ruff format --check .`
- Manual check: ran `setup_logging()` in both text and JSON mode with `game_id`/`turn` contextvars set and confirmed both formatters render the context correctly.
