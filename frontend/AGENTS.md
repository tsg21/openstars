# Frontend Instructions

These notes apply to frontend changes under `frontend/`.

## Working With The Frontend

- Frontend stack: React + TypeScript + Vite + Tailwind + shadcn/ui.
- The frontend is in the `frontend/` directory. All frontend npm commands must be run from that directory.
- Linting: `cd frontend && npm run lint`
- Type checking: `cd frontend && npm run typecheck`
- Dev server: `cd frontend && npm run dev`
- Tests: `cd frontend && npm test`
- The repo root does not have a `package.json`; only `frontend/` does.
- Frontend package management uses npm.
- Frontend tests use Vitest.
- Frontend linting uses ESLint with strict TypeScript rules.

## API Client

- The API client in `frontend/src/api/client.ts` converts backend response keys from `snake_case` to `camelCase` via `keysToCamel`.
- Outgoing command payloads are converted back via `keysToSnake`.
- TypeScript types should use camelCase consistently.
- Example mappings:
  - `mining_rate` → `miningRate`
  - `scan_level` → `scanLevel`

## App Responsibilities

- Keep `frontend/src/App.tsx` focused on app orchestration, selection, layout, and cross-cutting concerns.
- Avoid adding feature-specific command wiring to `App.tsx` when a shared mechanism will do.
- `App.tsx` may still coordinate truly cross-cutting UI behaviour, such as map interaction bridges or global keyboard handling.

## Command Flow

- Components that create player commands should use the shared game command access in `frontend/src/hooks/useGameCommands.ts`.
- Prefer generic command APIs over feature-specific command props.
- Use `addCommand(command)` when a feature emits a single command.
- Use `replaceCommands(scope, commands)` when a feature owns a scoped command set and needs to replace it atomically.

## Command Scoping

- Use fleet scope for fleet-owned command groups.
- Use planet scope for planet-owned command groups.
- Keep scope matching logic centralised rather than reimplementing it in feature components.

## Component Directory Structure

Components live under `frontend/src/components/` and are split into two subdirectories:

- **`ui/`** — reusable primitives with no game-domain knowledge. Use these as the building blocks for all UI. Available components:
  - `Button` — polymorphic button with variants: `primary`, `action`, `secondary`, `ghost`, `success`, `dangerGhost`, `dashed`
  - `PanelCard` — surface card. Use `variant="panel"` (default) for outer lobby/workspace cards (`bg-panel-bg`, `rounded-lg`). Use `variant="surface"` for inner elevated cards within a panel (`elevated-surface`, `rounded-md`, `p-3`). Supports `as="button"` and `interactive` prop for hover states.
  - `FormField` — label + input wrapper for forms
  - `TextInput` / `SelectInput` — full-width form inputs (`text-sm`, `px-3 py-1.5`)
  - `CompactInput` / `CompactSelect` — inline/compact form inputs (`text-xs`, `px-1.5 py-0.5`, `bg-black/30`). Use these inside panels and editors, not in full forms.
  - `ErrorBox` — red validation error container. Use for user-facing error messages. Accepts `className` for size overrides.
  - `StatusBadge` — rounded-pill badge for level/status indicators. Accepts `className` and `style` for colour overrides.
  - `MutedText` — polymorphic muted-colour text (`text-muted-foreground`). Supports `as` prop.
  - `DetailPanelLayout` — exports `DetailPanelContent` and `DetailPanelHeading` for the detail panel sidebar layout.
  - `ResourceBars` — canvas-based mineral/resource bar visualisation.
  - `DesktopGate` — viewport gate that blocks mobile-sized screens.

- **`panels/`** — feature views composed from `ui/` primitives. These are game-domain components. New feature panels go here.

- **`designer/`** — ship designer tools; self-contained.

All components are re-exported from `frontend/src/components/index.ts`.

### When to add a new `ui/` component

Before writing a raw Tailwind class combination more than once, check whether an existing `ui/` component covers it. If the same class string appears across three or more places, extract it into `ui/`. Do not add game-domain logic to `ui/` components.

## Detail Components

- `frontend/src/components/panels/FleetDetail.tsx` and `frontend/src/components/panels/PlanetDetail.tsx` should own their local transient edit state when that state is only relevant to that feature.
- `frontend/src/components/panels/DetailPanel.tsx` should stay a routing/layout component, not a command-construction layer.
- Avoid threading feature-specific command callbacks through `DetailPanel` unless there is a strong reason.

## Shared Helpers

- If multiple places need to build or transform the same command family, extract a shared helper instead of duplicating the logic.
- Keep command-building helpers pure and easy to test.

## Styling Tokens

- Define shared UI colours and theme values once in `frontend/src/index.css` as CSS custom properties.
- When a component reads a CSS custom property, do not duplicate that value as a hard-coded JavaScript or TypeScript fallback unless there is a specific runtime requirement and it is documented in the code.
