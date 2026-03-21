# PRD 02 — Galaxy Map

## Coordinate System

All positions in the galaxy — stars, fleets, and any future objects — are defined as **(x, y)** coordinate pairs using **64-bit unsigned integers**.

Galaxy sizes use a subset of the 64-bit space:

| Galaxy Size | Bits Used | Coordinate Range            |
|-------------|-----------|------------------------------|
| Small       | 48        | 0 to 281,474,976,710,655     |
| Medium      | 52        | 0 to 4,503,599,627,370,495   |
| Large       | 56        | 0 to 72,057,594,037,927,935  |
| Huge        | 64        | 0 to 18,446,744,073,709,551,615 |

The coordinate space is deliberately oversized relative to the number of stars. This gives fine-grained positioning for fleets in transit between stars, and leaves room for future mechanics (deep space objects, wormholes, etc.).

> **Note:** JavaScript does not natively support 64-bit unsigned integers. Coordinates must be handled as `BigInt` in the engine, or serialised as strings in JSON/YAML to avoid precision loss.

## Stars

Each star has:

- **name** — unique display name
- **x** — x coordinate (unsigned 64-bit integer)
- **y** — y coordinate (unsigned 64-bit integer)

Future additions (not yet defined): mineral concentrations, habitability values, gravity, temperature, radiation.

## Fleets

Each fleet has a coordinate pair in the same space. A fleet at a star shares that star's coordinates. A fleet in transit has coordinates somewhere between its origin and destination.

## Galaxy Definition File

A galaxy is defined in a `galaxy.yaml` file. This is the authoritative source for the star map — the server loads it when creating a new game.

### Format

```yaml
# galaxy.yaml
galaxy:
  name: "Alpha Sector"
  size: small            # determines coordinate bit range
  seed: 42               # generation seed (for reproducibility)

stars:
  - name: "Sol"
    x: 140737488355328
    y: 140737488355328

  - name: "Alpha Centauri"
    x: 140738491277312
    y: 140737622573056

  - name: "Sirius"
    x: 140736351510528
    y: 140738088919040

  - name: "Vega"
    x: 140739494199296
    y: 140736619945984

  - name: "Procyon"
    x: 140737890983936
    y: 140736888381440
```

Coordinates are written as plain integers in YAML (YAML natively supports arbitrary-precision integers, so no quoting needed).

### Constraints

- Star names must be unique within a galaxy
- No two stars may share the same coordinates
- All coordinates must be within the range defined by the galaxy size

## Galaxy Generation (MVP)

For Phase 1, galaxy generation is deliberately simple — just enough to produce a playable map.

### Algorithm: Uniform Random with Minimum Separation

1. **Inputs:**
   - `size` — galaxy size (determines coordinate bit range, e.g. 48 bits for small)
   - `starCount` — number of stars to place (e.g. 50 for small)
   - `minSeparation` — minimum distance between any two stars (prevents clumping)
   - `seed` — random seed for deterministic generation

2. **Define a placement region** within the coordinate space. Rather than scattering across the full 48-bit range, define a square "habitable zone" centred in the coordinate space. For example, use the middle 50% of the range on each axis — this leaves room at the edges and avoids stars clustered against the boundaries.

3. **Place stars using rejection sampling:**
   - Generate a random (x, y) within the placement region using the seeded RNG
   - Check the Euclidean distance to all previously placed stars
   - If all distances ≥ `minSeparation`, accept the star; otherwise reject and retry
   - Repeat until `starCount` stars are placed

4. **Assign names** from a predefined list of star names (real star names, mythological names, etc.). Shuffle the list with the same seed for deterministic assignment.

5. **Output** the `galaxy.yaml` file.

### Why This Approach

- **Simple to implement** — no Poisson disc sampling, no Voronoi, no clustering algorithms
- **Deterministic** — same seed always produces the same galaxy
- **Good enough** — uniform random with minimum separation produces reasonable-looking star maps for an MVP
- **Easy to replace** — the generation algorithm is independent of the file format, so we can swap in something more sophisticated later (spiral arms, clusters, density gradients) without changing anything downstream

### Suggested MVP Defaults (Small Galaxy)

| Parameter        | Value                |
|------------------|----------------------|
| Size             | small (48-bit)       |
| Star count       | 50                   |
| Min separation   | ~0.5% of axis range  |
| Placement region | Middle 50% of range  |
