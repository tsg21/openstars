# PRD 04 — Determinism

## Principle

OpenStars! is **fully deterministic**. Given the same inputs, the game always produces the same outputs — every time, on every platform. There is no hidden randomness, no timing-dependent behaviour, no floating-point ambiguity.

This is not just a nice property — it is a core design constraint that shapes the engine, the RNG system, and the testing strategy.

## Why Determinism Matters

### Testability

This is the primary motivation. Every test can specify a seed and assert exact outcomes. No flaky tests, no "usually passes", no statistical assertions where exact ones should work. A combat between two fleets with a given seed produces the same damage rolls, the same ships destroyed, the same survivors — every run.

This means:

- Unit tests for individual mechanics are fully reproducible
- Integration tests for full turn resolution produce identical game states
- Bug reports can include a seed and turn number, and the issue is exactly reproducible
- Regression tests catch any change to game logic, no matter how subtle

### Replay & Debugging

Since every turn's resolution is deterministic, the entire game history can be replayed from the initial state and the sequence of player commands. This enables:

- **Game replay** — watch a completed game unfold turn by turn
- **Bug reproduction** — replay up to the problematic turn with identical results
- **Auditing** — verify that the server resolved a turn correctly

### Fairness

All players are subject to the same deterministic rules. The server cannot fudge outcomes. Given the game state and commands, there is exactly one valid next state.

## The Game Seed

Each game has a single **game seed** — an integer assigned at game creation. It is the root of all randomness in the game from turn 0 onwards.

- The game seed is **secret** — it is stored only in the global state file, which is private to the server. Players never see it.
- If a player knew the seed, they could predict random outcomes (combat rolls, etc.). Keeping it server-side prevents this.
- The seed is carried in `global-state-T{N}.yaml` so it flows through the turn lifecycle naturally.

### Galaxy Seed vs Game Seed

Galaxy generation uses its own seed (defined in `galaxy.yaml` — see PRD 02). This is a separate process that happens before the game starts.

The game seed governs all randomness from turn 0 onwards: initial player placement, combat rolls, random events, and any other mechanic that involves chance.

## RNG Architecture

### Seeded PRNG

The engine uses a single deterministic pseudo-random number generator algorithm (e.g. xoshiro256). The specific algorithm choice is an implementation detail, but it must:

- Be seedable from an integer
- Produce identical sequences across platforms (no reliance on platform-native RNG)
- Be fast enough for bulk use during turn resolution

### Derived Keys

Rather than maintaining a single sequential PRNG stream (where adding a mechanic shifts all downstream random outcomes), the engine uses **derived random streams** based on context.

Each random stream is seeded by hashing the game seed with contextual identifiers:

```
streamSeed = hash(gameSeed, turn, context, identifier)
```

Examples:

| Context | Derived seed |
|---------|-------------|
| Combat between fleets 3 and 7, turn 12 | `hash(gameSeed, 12, "combat", 3, 7)` |
| Mineral packet accuracy, turn 5 | `hash(gameSeed, 5, "packet", packetId)` |
| Random event roll, turn 20 | `hash(gameSeed, 20, "event")` |

This approach means:

- **Isolation** — adding fleet scanning in a future phase doesn't change combat outcomes for the same seed
- **Testability** — a test for combat can derive its stream independently without simulating the entire turn pipeline
- **Reproducibility** — given the game seed, turn number, and context, any individual random stream can be recreated

### RNG State

The current RNG state is stored in the global state file. Since derived keys regenerate streams from the game seed + context, the state that needs persisting is minimal — essentially just the game seed itself.

## Rules for Engine Code

To maintain determinism, all engine code must follow these rules:

1. **No `Math.random()`** — all randomness must come from the seeded PRNG with derived keys
2. **No `Date.now()` or timestamps** in game logic — time-dependent behaviour breaks reproducibility
3. **No reliance on object iteration order** unless using ordered structures — `Map` iteration order is insertion-order in JS, but be explicit about sorting when order matters
4. **No floating-point arithmetic for game state** — use integers for all game values (coordinates, resources, damage, etc.). Floating-point rounding varies across platforms and optimisation levels
5. **Resolution pipeline order is fixed** — the order in which mechanics are processed must be defined and deterministic (see PRD 01 for the reference order)
6. **Derived key contexts must be stable** — the context strings and identifier schemes used to derive random streams must not change between versions, or save compatibility breaks

## Testing Implications

### Seed-Based Test Fixtures

Tests specify a seed and assert exact outcomes:

```typescript
// Deterministic: same seed, same result, every time
const rng = createRNG(deriveKey(gameSeed, turn, "combat", fleetA, fleetB));
const result = resolveCombat(fleetA, fleetB, rng);
expect(result.damage).toBe(42);
expect(result.destroyed).toEqual(["Destroyer Mark II"]);
```

### Snapshot Testing

Full turn resolution can be snapshot-tested: run `resolve(state, commands)` with a fixed seed and compare the output state byte-for-byte (or field-by-field) against a stored expected result. Any change to game logic that alters outcomes will be caught.

### Cross-Platform Verification

Because the PRNG algorithm is implemented in-engine (not platform-native), the same seed must produce the same sequence regardless of where the code runs (Node.js, browser, different OS). This should be verified with a cross-platform test that asserts a known sequence from a known seed.

## What's Out of Scope

- **Specific PRNG algorithm choice** — implementation decision, not a design one
- **Hash function choice for derived keys** — any deterministic hash that distributes well is fine
- **Replay tooling** — determinism enables it, but the viewer/tools are future work
- **Save format versioning** — important for long-running games, but a separate concern
