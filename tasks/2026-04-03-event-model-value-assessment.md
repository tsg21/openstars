# Value Assessment: Generic Event `code` + `values` Model

Date: 2026-04-03
Related task: `tasks/2026-04-03-simplify-event-model.md`

## Executive summary

This change is high-value if the team expects to add many event types over time and wants localisation-ready UI messaging. It shifts complexity from backend schema churn to frontend message rendering, which lowers long-term coupling and improves iteration speed.

Recommended approach: proceed with guardrails.

- Keep `code` as a stable, versioned API surface.
- Keep `values` as positional for payload size, but enforce per-code value-count tests.
- Add explicit fallback rendering for unknown codes.
- Add migration coverage in integration tests before removing any legacy assumptions.

## What value this change creates

### 1) Lower schema churn and faster feature delivery

Today, each new event shape forces backend model updates, serializer changes, frontend type additions, and UI rendering branches. A generic envelope (`owner`, `source_id`, `code`, `values`, `turn`) converts those into mostly data additions (new `code` + template), which is materially faster and less error-prone.

Expected impact:
- Fewer cross-layer PRs for routine event additions.
- Reduced boilerplate in engine models and frontend event unions.
- Smaller blast radius when extending mechanics.

### 2) Better separation of concerns

Backend remains authoritative for game outcomes and event semantics (`code`, `values`), while frontend owns presentation and localisation text. This aligns with existing command-and-resolve architecture and keeps deterministic engine outputs decoupled from UI wording.

### 3) Localisation and UX flexibility

Moving message text to the UI enables language-specific templates and tone changes without backend releases. It also allows per-platform/event-log formatting choices while preserving a stable backend contract.

### 4) Backward-compatible extensibility

Unknown `code` pass-through plus a frontend fallback message means newer backend events can degrade gracefully in older clients (and vice versa), if rollout is managed carefully.

## Costs and risks to account for

### 1) Contract fragility if `code`/`values` are under-specified

Risk: positional `values` can be hard to reason about if not documented per `code`.
Mitigation:
- Maintain a canonical event-code reference in PRD/API docs.
- Add tests asserting exact value order/count for each emitted code.

### 2) Potential frontend/backend drift

Risk: backend emits a code before frontend has template mapping.
Mitigation:
- Enforce unknown-code fallback rendering.
- Optionally track unknown code telemetry in frontend logs during rollout.

### 3) Type safety tradeoff

Risk: replacing discriminated unions with generic shape reduces compile-time guarantees about per-event fields.
Mitigation:
- Use strict code constants and formatter tests.
- Centralize dictionary and formatter logic with exhaustive checks where practical.

### 4) Migration complexity

Risk: existing tests/assertions and UI behavior may rely on typed fields.
Mitigation:
- Update integration assertions first for generic envelope.
- Keep deterministic ordering and fog-of-war unchanged.

## Recommendation

Proceed. The long-term maintainability gains outweigh short-term migration cost, provided the team treats event `code` definitions as first-class API contract and adds strong tests around `values` ordering.

## Acceptance criteria for "value realized"

- Adding a new event requires no backend schema/type expansion beyond emitting `code` + `values`.
- Frontend renders known codes via templates and unknown codes via stable fallback.
- Integration tests verify end-to-end event payload shape for mining/production/population families.
- Docs clearly define code stability and per-code value semantics.
