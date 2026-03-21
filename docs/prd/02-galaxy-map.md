# PRD 02 — Galaxy Map

## Coordinate System

All positions in the galaxy — stars, fleets, and any future objects — are defined as **(x, y)** coordinate pairs using **unsigned integers**, with the bit range determined by galaxy size.

| Galaxy Size | Bits | Max coordinate per axis | Relative area |
|-------------|------|-------------------------|---------------|
| Small       | 40   | 1,099,511,627,775       | 1×            |
| Medium      | 42   | 4,398,046,511,103       | 4×            |
| Large       | 44   | 17,592,186,044,415      | 16×           |
| Huge        | 46   | 70,368,744,177,663      | 64×           |

Each size step is 4× the area of the previous (2× per axis, +1 bit per axis).

The coordinate space is deliberately oversized relative to the number of stars. This gives fine-grained positioning for fleets in transit between stars, and leaves room for future mechanics (deep space objects, wormholes, etc.).

All coordinate values fit within JavaScript's safe integer range (53 bits), so no `BigInt` is required — plain `Number` is used throughout.

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
    x: 549755813888
    y: 549755813888

  - name: "Alpha Centauri"
    x: 550148141952
    y: 549755867136

  - name: "Sirius"
    x: 549311406080
    y: 549956141056

  - name: "Vega"
    x: 550540470272
    y: 549555486720

  - name: "Procyon"
    x: 549907809280
    y: 549453824000
```

Coordinates are written as plain integers in YAML.

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
| Size             | small (40-bit)       |
| Star count       | 50                   |
| Min separation   | ~0.5% of axis range  |
| Placement region | Middle 50% of range  |
