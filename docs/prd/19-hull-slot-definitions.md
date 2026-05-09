# PRD 19 — Hull Slot Definitions (Structured Reference)

## Overview

This document captures ship and starbase hull slot definitions from `docs/references/Design.pdf` as structured bullet lists.

The goal is to provide a practical, versioned reference for implementation work in OpenStars! (designer UI layout, validation, and fitting rules), without relying on visual hull-shape diagrams.

## Source and fidelity

- Source: `docs/references/Design.pdf` (15 pages).
- Method: extracted from the PDF text stream and normalised into slot-by-slot structured lists.
- This is the canonical slot reference for slot IDs, slot types, capacities, requirements, and grid-positioned designer layout. It is not a pixel-perfect silhouette-shape reference.
- OCR ambiguities are called out where needed.

### Layout schema

Hull layout data lives in `backend/openstars/data/hulls.yaml` and is exposed through the component catalogue / designer reference-data API.

- `layout_grid: {w, h}` defines the integer-cell grid for the hull canvas.
- Each slot may define `position: {x, y}` and `size: {w, h}`. Coordinates are integer cells, with `(0, 0)` at the top-left of the hull grid. Missing `size` defaults to one cell wide by one cell high in the UI.
- Hull-level `cargo_layout: {x, y, w, h}` and `dock_layout: {x, y, w, h}` define non-slot rectangles for cargo space and starbase docks.
- Slot legality remains defined by the slot category list; layout rectangles only control visual placement.

## Notation

- `SNN` = slot number (`S01`, `S02`, ...).
- `needs N` = mandatory slot fill count (for engine slots).
- `up to N` = maximum items supported in that slot.
- `A or B` = either category is legal for the slot.
- `A / B / C` = any of these categories is legal for the slot.
- Cargo and dock capacity are listed as hull properties, not slots.

---

## Ship hull slot definitions

### Small Freighter (0)
- Cargo: `70 kt`
- `S01`: `Engine` (`needs 1`)
- `S02`: `Scanner / Electrical / Mechanical` (`up to 1`)
- `S03`: `Shield or Armour` (`up to 1`)

### Medium Freighter (1)
- Cargo: `210 kt`
- `S01`: `Engine` (`needs 1`)
- `S02`: `Scanner / Electrical / Mechanical` (`up to 1`)
- `S03`: `Shield or Armour` (`up to 1`)

### Large Freighter (2)
- Cargo: `1200 kt`
- `S01`: `Engine` (`needs 2`)
- `S02`: `Scanner / Electrical / Mechanical` (`up to 2`)
- `S03`: `Shield or Armour` (`up to 2`)

### Super Freighter (3)
- Cargo: `3000 kt`
- `S01`: `Engine` (`needs 3`)
- `S02`: `Scanner / Electrical / Mechanical` (`up to 3`)
- `S03`: `Shield or Armour` (`up to 5`)
- `S04`: `Electrical` (`up to 2`)

### Scout (4)
- `S01`: `Engine` (`needs 1`)
- `S02`: `Scanner` (`up to 1`)
- `S03`: `General Purpose` (`up to 1`)

### Frigate (5)
- `S01`: `Engine` (`needs 1`)
- `S02`: `Scanner` (`up to 1`)
- `S03`: `General Purpose` (`up to 3`)
- `S04`: `Shield or Armour` (`up to 2`)

### Destroyer (6)
- `S01`: `Engine` (`needs 1`)
- `S02`: `Weapon` (`up to 1`)
- `S03`: `Weapon` (`up to 1`)
- `S04`: `General Purpose` (`up to 1`)
- `S05`: `Armour` (`up to 2`)
- `S06`: `Mechanical` (`up to 1`)
- `S07`: `Electrical` (`up to 1`)

### Cruiser (7)
- `S01`: `Engine` (`needs 2`)
- `S02`: `Shield / Electrical / Mechanical` (`up to 1`)
- `S03`: `Shield / Electrical / Mechanical` (`up to 1`)
- `S04`: `Weapon` (`up to 2`)
- `S05`: `Weapon` (`up to 2`)
- `S06`: `General Purpose` (`up to 2`)
- `S07`: `Shield or Armour` (`up to 2`)

### Battle Cruiser (8)
- `S01`: `Engine` (`needs 2`)
- `S02`: `Shield / Electrical / Mechanical` (`up to 2`)
- `S03`: `Shield / Electrical / Mechanical` (`up to 2`)
- `S04`: `Weapon` (`up to 3`)
- `S05`: `Weapon` (`up to 3`)
- `S06`: `General Purpose` (`up to 3`)
- `S07`: `Shield or Armour` (`up to 4`)

### Battleship (9)
- `S01`: `Engine` (`needs 4`)
- `S02`: `Scanner / Electrical / Mechanical` (`up to 1`)
- `S03`: `Shield` (`up to 8`)
- `S04`: `Weapon` (`up to 6`)
- `S05`: `Weapon` (`up to 6`)
- `S06`: `Weapon` (`up to 2`)
- `S07`: `Weapon` (`up to 2`)
- `S08`: `Weapon` (`up to 4`)
- `S09`: `Armour` (`up to 6`)
- `S10`: `Electrical` (`up to 3`)
- `S11`: `Electrical` (`up to 3`)

### Dreadnaught (10)
- `S01`: `Engine` (`needs 5`)
- `S02`: `Shield or Armour` (`up to 4`)
- `S03`: `Shield or Armour` (`up to 4`)
- `S04`: `Weapon` (`up to 6`)
- `S05`: `Weapon` (`up to 6`)
- `S06`: `Electrical` (`up to 4`)
- `S07`: `Electrical` (`up to 4`)
- `S08`: `Weapon` (`up to 8`)
- `S09`: `Weapon` (`up to 8`)
- `S10`: `Armour` (`up to 8`)
- `S11`: `Weapon or Shield` (`up to 5`)
- `S12`: `Weapon or Shield` (`up to 5`)
- `S13`: `General Purpose` (`up to 2`)

### Privateer (11)
- Cargo: `250 kt`
- `S01`: `Engine` (`needs 1`)
- `S02`: `Shield or Armour` (`up to 2`)
- `S03`: `Scanner / Electrical / Mechanical` (`up to 1`)
- `S04`: `General Purpose` (`up to 1`)
- `S05`: `General Purpose` (`up to 1`)

### Rogue (12)
- Cargo: `500 kt`
- `S01`: `Engine` (`needs 2`)
- `S02`: `Shield or Armour` (`up to 3`)
- `S03`: `Mine Layer / Electrical / Mechanical` (`up to 2`)
- `S04`: `Scanner` (`up to 1`)
- `S05`: `General Purpose` (`up to 2`)
- `S06`: `General Purpose` (`up to 2`)
- `S07`: `Mine Layer / Electrical / Mechanical` (`up to 2`)
- `S08`: `Electrical` (`up to 1`)
- `S09`: `Electrical` (`up to 1`)

### Galleon (13)
- Cargo: `1000 kt`
- `S01`: `Engine` (`needs 4`)
- `S02`: `Shield or Armour` (`up to 2`)
- `S03`: `Shield or Armour` (`up to 2`)
- `S04`: `General Purpose` (`up to 3`)
- `S05`: `General Purpose` (`up to 3`)
- `S06`: `Mine Layer / Electrical / Mechanical` (`up to 2`)
- `S07`: `Mine Layer / Electrical / Mechanical` (`up to 2`)
- `S08`: `Scanner` (`up to 2`)

### Mini Colony Ship (14)
- Cargo: `10 kt`
- `S01`: `Engine` (`needs 1`)
- `S02`: `Mechanical` (`up to 1`)

### Colony Ship (15)
- Cargo: `25 kt`
- `S01`: `Engine` (`needs 1`)
- `S02`: `Mechanical` (`up to 1`)

### Mini Bomber (16)
- `S01`: `Engine` (`needs 1`)
- `S02`: `Bomb` (`up to 2`)

### B-17 Bomber (17)
- `S01`: `Engine` (`needs 2`)
- `S02`: `Bomb` (`up to 4`)
- `S03`: `Bomb` (`up to 4`)
- `S04`: `Scanner / Electrical / Mechanical` (`up to 1`)

### Stealth Bomber (18)
- `S01`: `Engine` (`needs 2`)
- `S02`: `Bomb` (`up to 4`)
- `S03`: `Bomb` (`up to 4`)
- `S04`: `Scanner / Electrical / Mechanical` (`up to 1`)
- `S05`: `Electrical` (`up to 1`)

### B-52 Bomber (19)
- `S01`: `Engine` (`needs 3`)
- `S02`: `Bomb` (`up to 4`)
- `S03`: `Bomb` (`up to 4`)
- `S04`: `Bomb` (`up to 4`)
- `S05`: `Bomb` (`up to 4`)
- `S06`: `Scanner / Electrical / Mechanical` (`up to 2`)
- `S07`: `Shield` (`up to 2`)

### Midget Miner (20)
- `S01`: `Engine` (`needs 1`)
- `S02`: `Robot Miner` (`up to 2`)

### Mini Miner (21)
- `S01`: `Engine` (`needs 1`)
- `S02`: `Scanner / Electrical / Mechanical` (`up to 1`)
- `S03`: `Robot Miner` (`up to 1`)
- `S04`: `Robot Miner` (`up to 1`)

### Miner (22)
- `S01`: `Engine` (`needs 2`)
- `S02`: `Armour / Scanner / Electrical / Mechanical` (`up to 2`)
- `S03`: `Robot Miner` (`up to 2`)
- `S04`: `Robot Miner` (`up to 1`)
- `S05`: `Robot Miner` (`up to 2`)
- `S06`: `Robot Miner` (`up to 1`)

### Maxi Miner (23)
- `S01`: `Engine` (`needs 3`)
- `S02`: `Armour / Scanner / Electrical / Mechanical` (`up to 2`)
- `S03`: `Robot Miner` (`up to 4`)
- `S04`: `Robot Miner` (`up to 1`)
- `S05`: `Robot Miner` (`up to 4`)
- `S06`: `Robot Miner` (`up to 1`)

### Ultra Miner (24)
- `S01`: `Engine` (`needs 2`)
- `S02`: `Armour / Scanner / Electrical / Mechanical` (`up to 3`)
- `S03`: `Robot Miner` (`up to 4`)
- `S04`: `Robot Miner` (`up to 2`)
- `S05`: `Robot Miner` (`up to 4`)
- `S06`: `Robot Miner` (`up to 2`)

### Fuel Transport (25)
- `S01`: `Engine` (`needs 1`)
- `S02`: `Shield` (`up to 1`)

### Super Fuel Transport (26)
- `S01`: `Engine` (`needs 2`)
- `S02`: `Shield` (`up to 2`)
- `S03`: `Scanner` (`up to 1`)

### Mini Mine Layer (27)
- `S01`: `Engine` (`needs 1`)
- `S02`: `Mine Layer` (`up to 2`)
- `S03`: `Mine Layer` (`up to 2`)
- `S04`: `Scanner / Electrical / Mechanical` (`up to 1`)

### Super Mine Layer (28)
- `S01`: `Engine` (`needs 3`)
- `S02`: `Mine Layer` (`up to 8`)
- `S03`: `Mine Layer` (`up to 8`)
- `S04`: `Shield or Armour` (`up to 3`)
- `S05`: `Scanner / Electrical / Mechanical` (`up to 3`)
- `S06`: `Mine Layer / Electrical / Mechanical` (`up to 3`)

### Nubian (29)
- `S01`: `Engine` (`needs 3`)
- `S02`: `General Purpose` (`up to 3`)
- `S03`: `General Purpose` (`up to 3`)
- `S04`: `General Purpose` (`up to 3`)
- `S05`: `General Purpose` (`up to 3`)
- `S06`: `General Purpose` (`up to 3`)
- `S07`: `General Purpose` (`up to 3`)
- `S10`: `General Purpose` (`up to 3`)
- `S11`: `General Purpose` (`up to 3`)
- `S12`: `General Purpose` (`up to 3`)
- `S13`: `General Purpose` (`up to 3`)
- Note: OCR on this hull includes duplicate slot labels; verify exact slot numbering against raw PDF page before implementation.

### Mini Morph (30)
- Cargo: `300 kt`
- `S01`: `Engine` (`needs 3`)
- `S02`: `General Purpose` (`up to 8`)
- `S03`: `General Purpose` (`up to 2`)
- `S04`: `General Purpose` (`up to 2`)
- `S05`: `General Purpose` (`up to 1`)
- `S06`: `General Purpose` (`up to 2`)
- `S07`: `General Purpose` (`up to 2`)

### Meta Morph (31)
- Cargo: `300 kt`
- `S01`: `Engine` (`needs 3`)
- `S02`: `General Purpose` (`up to 8`)
- `S03`: `General Purpose` (`up to 2`)
- `S04`: `General Purpose` (`up to 2`)
- `S05`: `General Purpose` (`up to 1`)
- `S06`: `General Purpose` (`up to 2`)
- `S07`: `General Purpose` (`up to 2`)

---

## Starbase hull slot definitions

### Orbital Fort (32)
- `S01`: `Orbital or Electrical` (`up to 1`)
- `S02`: `Weapon` (`up to 12`)
- `S03`: `Shield or Armour` (`up to 12`)
- `S04`: `Weapon` (`up to 12`)
- `S05`: `Shield or Armour` (`up to 12`)

### Space Dock (33)
- Dock capacity: `200 kt`
- `S01`: `Orbital or Electrical` (`up to 1`)
- `S02`: `Weapon` (`up to 16`)
- `S03`: `Shield or Armour` (`up to 24`)
- `S04`: `Weapon` (`up to 16`)
- `S05`: `Shield` (`up to 24`)
- `S06`: `Electrical` (`up to 2`)
- `S07`: `Electrical` (`up to 2`)
- `S08`: `Weapon` (`up to 16`)

### Space Station (34)
- Dock capacity: `unlimited`
- `S01`: `Orbital or Electrical` (`up to 1`)
- `S02`: `Weapon` (`up to 16`)
- `S03`: `Shield` (`up to 16`)
- `S04`: `Weapon` (`up to 16`)
- `S05`: `Shield or Armour` (`up to 16`)
- `S06`: `Shield` (`up to 16`)
- `S07`: `Electrical` (`up to 3`)
- `S08`: `Weapon` (`up to 16`)
- `S09`: `Electrical` (`up to 3`)
- `S10`: `Weapon` (`up to 16`)
- `S11`: `Orbital or Electrical` (`up to 1`)
- `S12`: `Shield or Armour` (`up to 16`)

### Ultra Station (35)
- Dock capacity: `unlimited`
- `S01`: `Orbital or Electrical` (`up to 1`)
- `S02`: `Weapon` (`up to 16`)
- `S03`: `Electrical` (`up to 3`)
- `S04`: `Weapon` (`up to 16`)
- `S05`: `Shield` (`up to 20`)
- `S06`: `Shield` (`up to 20`)
- `S07`: `Electrical` (`up to 3`)
- `S08`: `Weapon` (`up to 16`)
- `S09`: `Electrical` (`up to 3`)
- `S10`: `Weapon` (`up to 16`)
- `S11`: `Orbital or Electrical` (`up to 1`)
- `S12`: `Shield or Armour` (`up to 20`)
- `S13`: `Weapon` (`up to 16`)
- `S14`: `Shield or Armour` (`up to 20`)
- `S15`: `Electrical` (`up to 3`)
- `S16`: `Weapon` (`up to 16`)

### Death Star
- Dock capacity: `unlimited`
- `S01`: `Orbital or Electrical` (`up to 1`)
- `S02`: `Weapon` (`up to 32`)
- `S03`: `Electrical` (`up to 4`)
- `S04`: `Electrical` (`up to 4`)
- `S05`: `Shield` (`up to 20`)
- `S06`: `Shield` (`up to 20`)
- `S07`: `Electrical` (`up to 4`)
- `S08`: `Weapon` (`up to 32`)
- `S09`: `Electrical` (`up to 4`)
- `S10`: `Weapon` (`up to 32`)
- `S11`: `Orbital or Electrical` (`up to 1`)
- `S12`: `Shield or Armour` (`up to 20`)
- `S13`: `Electrical` (`up to 4`)
- `S14`: `Shield or Armour` (`up to 20`)
- `S15`: `Electrical` (`up to 4`)
- `S16`: `Weapon` (`up to 32`)

---

## Follow-ups

- Cross-check OCR ambiguities (especially Nubian and Death Star labels) against raw PDF pages.
- Define canonical slot-category enum values for backend validation in PRD 18 implementation.
