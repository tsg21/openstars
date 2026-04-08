# PRD 19 — Hull Slot Layouts (ASCII Reference)

## Overview

This document captures ship and starbase hull slot layouts from `docs/references/Design.pdf` as ASCII schematics.

The goal is to provide a practical, versioned reference for implementation work in OpenStars! (designer UI, validation, and fitting rules), without needing to open the PDF during routine development.

## Source and fidelity

- Source: `docs/references/Design.pdf` (15 pages).
- Method: extracted from PDF text stream and normalised into slot-by-slot schematics.
- This is a **logical slot layout reference** (slot IDs, slot types, capacities, requirements), not a pixel-perfect reproduction of original artwork silhouettes.
- Any OCR ambiguities are called out explicitly.

## Notation

- `SNN` = slot number (`S01`, `S02`, ...).
- `needs N` = mandatory slot fill count (for engines).
- `up to N` = maximum items supported in that slot.
- `A or B` = either category is legal for the slot.
- `A/B/C` = any of these categories is legal for the slot.
- Cargo and dock capacity are listed as hull properties, not slots.

---

## Ship hull layouts

### Small Freighter (0)

+--------------------------------------------------------------+
| Hull: Small Freighter (0)                                   |
| Cargo: 70 kt                                                 |
| S01: ENGINE                              (needs 1)           |
| S02: SCANNER / ELECTRICAL / MECHANICAL  (up to 1)           |
| S03: SHIELD or ARMOUR                    (up to 1)           |
+--------------------------------------------------------------+

### Medium Freighter (1)

+--------------------------------------------------------------+
| Hull: Medium Freighter (1)                                  |
| Cargo: 210 kt                                                |
| S01: ENGINE                              (needs 1)           |
| S02: SCANNER / ELECTRICAL / MECHANICAL  (up to 1)           |
| S03: SHIELD or ARMOUR                    (up to 1)           |
+--------------------------------------------------------------+

### Large Freighter (2)

+--------------------------------------------------------------+
| Hull: Large Freighter (2)                                   |
| Cargo: 1200 kt                                               |
| S01: ENGINE                              (needs 2)           |
| S02: SCANNER / ELECTRICAL / MECHANICAL  (up to 2)           |
| S03: SHIELD or ARMOUR                    (up to 2)           |
+--------------------------------------------------------------+

### Super Freighter (3)

+--------------------------------------------------------------+
| Hull: Super Freighter (3)                                   |
| Cargo: 3000 kt                                               |
| S01: ENGINE                              (needs 3)           |
| S02: SCANNER / ELECTRICAL / MECHANICAL  (up to 3)           |
| S03: SHIELD or ARMOUR                    (up to 5)           |
| S04: ELECTRICAL                          (up to 2)           |
+--------------------------------------------------------------+

### Scout (4)

+--------------------------------------------------------------+
| Hull: Scout (4)                                              |
| S01: ENGINE                              (needs 1)           |
| S02: SCANNER                             (up to 1)           |
| S03: GENERAL PURPOSE                     (up to 1)           |
+--------------------------------------------------------------+

### Frigate (5)

+--------------------------------------------------------------+
| Hull: Frigate (5)                                            |
| S01: ENGINE                              (needs 1)           |
| S02: SCANNER                             (up to 1)           |
| S03: GENERAL PURPOSE                     (up to 3)           |
| S04: SHIELD or ARMOUR                    (up to 2)           |
+--------------------------------------------------------------+

### Destroyer (6)

+--------------------------------------------------------------+
| Hull: Destroyer (6)                                          |
| S01: ENGINE                              (needs 1)           |
| S02: WEAPON                              (up to 1)           |
| S03: WEAPON                              (up to 1)           |
| S04: GENERAL PURPOSE                     (up to 1)           |
| S05: ARMOUR                              (up to 2)           |
| S06: MECHANICAL                          (up to 1)           |
| S07: ELECTRICAL                          (up to 1)           |
+--------------------------------------------------------------+

### Cruiser (7)

+--------------------------------------------------------------+
| Hull: Cruiser (7)                                            |
| S01: ENGINE                              (needs 2)           |
| S02: SHIELD / ELECTRICAL / MECHANICAL    (up to 1)          |
| S03: SHIELD / ELECTRICAL / MECHANICAL    (up to 1)          |
| S04: WEAPON                              (up to 2)           |
| S05: WEAPON                              (up to 2)           |
| S06: GENERAL PURPOSE                     (up to 2)           |
| S07: SHIELD or ARMOUR                    (up to 2)           |
+--------------------------------------------------------------+

### Battle Cruiser (8)

+--------------------------------------------------------------+
| Hull: Battle Cruiser (8)                                     |
| S01: ENGINE                              (needs 2)           |
| S02: SHIELD / ELECTRICAL / MECHANICAL    (up to 2)          |
| S03: SHIELD / ELECTRICAL / MECHANICAL    (up to 2)          |
| S04: WEAPON                              (up to 3)           |
| S05: WEAPON                              (up to 3)           |
| S06: GENERAL PURPOSE                     (up to 3)           |
| S07: SHIELD or ARMOUR                    (up to 4)           |
+--------------------------------------------------------------+

### Battleship (9)

+--------------------------------------------------------------+
| Hull: Battleship (9)                                         |
| S01: ENGINE                              (needs 4)           |
| S02: SCANNER / ELECTRICAL / MECHANICAL   (up to 1)          |
| S03: SHIELD                              (up to 8)           |
| S04: WEAPON                              (up to 6)           |
| S05: WEAPON                              (up to 6)           |
| S06: WEAPON                              (up to 2)           |
| S07: WEAPON                              (up to 2)           |
| S08: WEAPON                              (up to 4)           |
| S09: ARMOUR                              (up to 6)           |
| S10: ELECTRICAL                          (up to 3)           |
| S11: ELECTRICAL                          (up to 3)           |
+--------------------------------------------------------------+

### Dreadnaught (10)

+--------------------------------------------------------------+
| Hull: Dreadnaught (10)                                       |
| S01: ENGINE                              (needs 5)           |
| S02: SHIELD or ARMOUR                    (up to 4)           |
| S03: SHIELD or ARMOUR                    (up to 4)           |
| S04: WEAPON                              (up to 6)           |
| S05: WEAPON                              (up to 6)           |
| S06: ELECTRICAL                          (up to 4)           |
| S07: ELECTRICAL                          (up to 4)           |
| S08: WEAPON                              (up to 8)           |
| S09: WEAPON                              (up to 8)           |
| S10: ARMOUR                              (up to 8)           |
| S11: WEAPON or SHIELD                    (up to 5)           |
| S12: WEAPON or SHIELD                    (up to 5)           |
| S13: GENERAL PURPOSE                     (up to 2)           |
+--------------------------------------------------------------+

### Privateer (11)

+--------------------------------------------------------------+
| Hull: Privateer (11)                                         |
| Cargo: 250 kt                                                |
| S01: ENGINE                              (needs 1)           |
| S02: SHIELD or ARMOUR                    (up to 2)           |
| S03: SCANNER / ELECTRICAL / MECHANICAL  (up to 1)           |
| S04: GENERAL PURPOSE                     (up to 1)           |
| S05: GENERAL PURPOSE                     (up to 1)           |
+--------------------------------------------------------------+

### Rogue (12)

+--------------------------------------------------------------+
| Hull: Rogue (12)                                             |
| Cargo: 500 kt                                                |
| S01: ENGINE                              (needs 2)           |
| S02: SHIELD or ARMOUR                    (up to 3)           |
| S03: MINE LAYER / ELECTRICAL / MECHANICAL (up to 2)         |
| S04: SCANNER                             (up to 1)           |
| S05: GENERAL PURPOSE                     (up to 2)           |
| S06: GENERAL PURPOSE                     (up to 2)           |
| S07: MINE LAYER / ELECTRICAL / MECHANICAL (up to 2)         |
| S08: ELECTRICAL                          (up to 1)           |
| S09: ELECTRICAL                          (up to 1)           |
+--------------------------------------------------------------+

### Galleon (13)

+--------------------------------------------------------------+
| Hull: Galleon (13)                                           |
| Cargo: 1000 kt                                               |
| S01: ENGINE                              (needs 4)           |
| S02: SHIELD or ARMOUR                    (up to 2)           |
| S03: SHIELD or ARMOUR                    (up to 2)           |
| S04: GENERAL PURPOSE                     (up to 3)           |
| S05: GENERAL PURPOSE                     (up to 3)           |
| S06: MINE LAYER / ELECTRICAL / MECHANICAL (up to 2)         |
| S07: MINE LAYER / ELECTRICAL / MECHANICAL (up to 2)         |
| S08: SCANNER                             (up to 2)           |
+--------------------------------------------------------------+

### Mini Colony Ship (14)

+--------------------------------------------------------------+
| Hull: Mini Colony Ship (14)                                  |
| Cargo: 10 kt                                                 |
| S01: ENGINE                              (needs 1)           |
| S02: MECHANICAL                          (up to 1)           |
+--------------------------------------------------------------+

### Colony Ship (15)

+--------------------------------------------------------------+
| Hull: Colony Ship (15)                                       |
| Cargo: 25 kt                                                 |
| S01: ENGINE                              (needs 1)           |
| S02: MECHANICAL                          (up to 1)           |
+--------------------------------------------------------------+

### Mini Bomber (16)

+--------------------------------------------------------------+
| Hull: Mini Bomber (16)                                       |
| S01: ENGINE                              (needs 1)           |
| S02: BOMB                                (up to 2)           |
+--------------------------------------------------------------+

### B-17 Bomber (17)

+--------------------------------------------------------------+
| Hull: B-17 Bomber (17)                                       |
| S01: ENGINE                              (needs 2)           |
| S02: BOMB                                (up to 4)           |
| S03: BOMB                                (up to 4)           |
| S04: SCANNER / ELECTRICAL / MECHANICAL  (up to 1)           |
+--------------------------------------------------------------+

### Stealth Bomber (18)

+--------------------------------------------------------------+
| Hull: Stealth Bomber (18)                                    |
| S01: ENGINE                              (needs 2)           |
| S02: BOMB                                (up to 4)           |
| S03: BOMB                                (up to 4)           |
| S04: SCANNER / ELECTRICAL / MECHANICAL  (up to 1)           |
| S05: ELECTRICAL                          (up to 1)           |
+--------------------------------------------------------------+

### B-52 Bomber (19)

+--------------------------------------------------------------+
| Hull: B-52 Bomber (19)                                       |
| S01: ENGINE                              (needs 3)           |
| S02: BOMB                                (up to 4)           |
| S03: BOMB                                (up to 4)           |
| S04: BOMB                                (up to 4)           |
| S05: BOMB                                (up to 4)           |
| S06: SCANNER / ELECTRICAL / MECHANICAL  (up to 2)           |
| S07: SHIELD                              (up to 2)           |
+--------------------------------------------------------------+

### Midget Miner (20)

+--------------------------------------------------------------+
| Hull: Midget Miner (20)                                      |
| S01: ENGINE                              (needs 1)           |
| S02: ROBOT MINER                          (up to 2)          |
+--------------------------------------------------------------+

### Mini Miner (21)

+--------------------------------------------------------------+
| Hull: Mini Miner (21)                                        |
| S01: ENGINE                              (needs 1)           |
| S02: SCANNER / ELECTRICAL / MECHANICAL  (up to 1)           |
| S03: ROBOT MINER                          (up to 1)          |
| S04: ROBOT MINER                          (up to 1)          |
+--------------------------------------------------------------+

### Miner (22)

+--------------------------------------------------------------+
| Hull: Miner (22)                                             |
| S01: ENGINE                              (needs 2)           |
| S02: ARMOUR / SCANNER / ELECTRICAL / MECHANICAL (up to 2)   |
| S03: ROBOT MINER                          (up to 2)          |
| S04: ROBOT MINER                          (up to 1)          |
| S05: ROBOT MINER                          (up to 2)          |
| S06: ROBOT MINER                          (up to 1)          |
+--------------------------------------------------------------+

### Maxi Miner (23)

+--------------------------------------------------------------+
| Hull: Maxi Miner (23)                                        |
| S01: ENGINE                              (needs 3)           |
| S02: ARMOUR / SCANNER / ELECTRICAL / MECHANICAL (up to 2)   |
| S03: ROBOT MINER                          (up to 4)          |
| S04: ROBOT MINER                          (up to 1)          |
| S05: ROBOT MINER                          (up to 4)          |
| S06: ROBOT MINER                          (up to 1)          |
+--------------------------------------------------------------+

### Ultra Miner (24)

+--------------------------------------------------------------+
| Hull: Ultra Miner (24)                                       |
| S01: ENGINE                              (needs 2)           |
| S02: ARMOUR / SCANNER / ELECTRICAL / MECHANICAL (up to 3)   |
| S03: ROBOT MINER                          (up to 4)          |
| S04: ROBOT MINER                          (up to 2)          |
| S05: ROBOT MINER                          (up to 4)          |
| S06: ROBOT MINER                          (up to 2)          |
+--------------------------------------------------------------+

### Fuel Transport (25)

+--------------------------------------------------------------+
| Hull: Fuel Transport (25)                                    |
| S01: ENGINE                              (needs 1)           |
| S02: SHIELD                              (up to 1)           |
+--------------------------------------------------------------+

### Super Fuel Transport (26)

+--------------------------------------------------------------+
| Hull: Super Fuel Transport (26)                              |
| S01: ENGINE                              (needs 2)           |
| S02: SHIELD                              (up to 2)           |
| S03: SCANNER                             (up to 1)           |
+--------------------------------------------------------------+

### Mini Mine Layer (27)

+--------------------------------------------------------------+
| Hull: Mini Mine Layer (27)                                   |
| S01: ENGINE                              (needs 1)           |
| S02: MINE LAYER                          (up to 2)           |
| S03: MINE LAYER                          (up to 2)           |
| S04: SCANNER / ELECTRICAL / MECHANICAL  (up to 1)           |
+--------------------------------------------------------------+

### Super Mine Layer (28)

+--------------------------------------------------------------+
| Hull: Super Mine Layer (28)                                  |
| S01: ENGINE                              (needs 3)           |
| S02: MINE LAYER                          (up to 8)           |
| S03: MINE LAYER                          (up to 8)           |
| S04: SHIELD or ARMOUR                    (up to 3)           |
| S05: SCANNER / ELECTRICAL / MECHANICAL  (up to 3)           |
| S06: MINE LAYER / ELECTRICAL / MECHANICAL (up to 3)         |
+--------------------------------------------------------------+

### Nubian (29)

+--------------------------------------------------------------+
| Hull: Nubian (29)                                            |
| S01: ENGINE                              (needs 3)           |
| S02: GENERAL PURPOSE                     (up to 3)           |
| S03: GENERAL PURPOSE                     (up to 3)           |
| S04: GENERAL PURPOSE                     (up to 3)           |
| S05: GENERAL PURPOSE                     (up to 3)           |
| S06: GENERAL PURPOSE                     (up to 3)           |
| S07: GENERAL PURPOSE                     (up to 3)           |
| S10: GENERAL PURPOSE                     (up to 3)           |
| S11: GENERAL PURPOSE                     (up to 3)           |
| S12: GENERAL PURPOSE                     (up to 3)           |
| S13: GENERAL PURPOSE                     (up to 3)           |
| NOTE: OCR on this hull includes duplicate slot labels;       |
|       verify exact slot numbering against the PDF page.      |
+--------------------------------------------------------------+

### Mini Morph (30)

+--------------------------------------------------------------+
| Hull: Mini Morph (30)                                        |
| Cargo: 300 kt                                                |
| S01: ENGINE                              (needs 3)           |
| S02: GENERAL PURPOSE                     (up to 8)           |
| S03: GENERAL PURPOSE                     (up to 2)           |
| S04: GENERAL PURPOSE                     (up to 2)           |
| S05: GENERAL PURPOSE                     (up to 1)           |
| S06: GENERAL PURPOSE                     (up to 2)           |
| S07: GENERAL PURPOSE                     (up to 2)           |
+--------------------------------------------------------------+

### Meta Morph (31)

+--------------------------------------------------------------+
| Hull: Meta Morph (31)                                        |
| Cargo: 300 kt                                                |
| S01: ENGINE                              (needs 3)           |
| S02: GENERAL PURPOSE                     (up to 8)           |
| S03: GENERAL PURPOSE                     (up to 2)           |
| S04: GENERAL PURPOSE                     (up to 2)           |
| S05: GENERAL PURPOSE                     (up to 1)           |
| S06: GENERAL PURPOSE                     (up to 2)           |
| S07: GENERAL PURPOSE                     (up to 2)           |
+--------------------------------------------------------------+

---

## Starbase hull layouts

### Orbital Fort (32)

+--------------------------------------------------------------+
| Hull: Orbital Fort (32)                                      |
| S01: ORBITAL or ELECTRICAL               (up to 1)           |
| S02: WEAPON                              (up to 12)          |
| S03: SHIELD or ARMOUR                    (up to 12)          |
| S04: WEAPON                              (up to 12)          |
| S05: SHIELD or ARMOUR                    (up to 12)          |
+--------------------------------------------------------------+

### Space Dock (33)

+--------------------------------------------------------------+
| Hull: Space Dock (33)                                        |
| Dock capacity: 200 kt                                        |
| S01: ORBITAL or ELECTRICAL               (up to 1)           |
| S02: WEAPON                              (up to 16)          |
| S03: SHIELD or ARMOUR                    (up to 24)          |
| S04: WEAPON                              (up to 16)          |
| S05: SHIELD                              (up to 24)          |
| S06: ELECTRICAL                          (up to 2)           |
| S07: ELECTRICAL                          (up to 2)           |
| S08: WEAPON                              (up to 16)          |
+--------------------------------------------------------------+

### Space Station (34)

+--------------------------------------------------------------+
| Hull: Space Station (34)                                     |
| Dock capacity: unlimited                                     |
| S01: ORBITAL or ELECTRICAL               (up to 1)           |
| S02: WEAPON                              (up to 16)          |
| S03: SHIELD                              (up to 16)          |
| S04: WEAPON                              (up to 16)          |
| S05: SHIELD or ARMOUR                    (up to 16)          |
| S06: SHIELD                              (up to 16)          |
| S07: ELECTRICAL                          (up to 3)           |
| S08: WEAPON                              (up to 16)          |
| S09: ELECTRICAL                          (up to 3)           |
| S10: WEAPON                              (up to 16)          |
| S11: ORBITAL or ELECTRICAL               (up to 1)           |
| S12: SHIELD or ARMOUR                    (up to 16)          |
+--------------------------------------------------------------+

### Ultra Station (35)

+--------------------------------------------------------------+
| Hull: Ultra Station (35)                                     |
| Dock capacity: unlimited                                     |
| S01: ORBITAL or ELECTRICAL               (up to 1)           |
| S02: WEAPON                              (up to 16)          |
| S03: ELECTRICAL                          (up to 3)           |
| S04: WEAPON                              (up to 16)          |
| S05: SHIELD                              (up to 20)          |
| S06: SHIELD                              (up to 20)          |
| S07: ELECTRICAL                          (up to 3)           |
| S08: WEAPON                              (up to 16)          |
| S09: ELECTRICAL                          (up to 3)           |
| S10: WEAPON                              (up to 16)          |
| S11: ORBITAL or ELECTRICAL               (up to 1)           |
| S12: SHIELD or ARMOUR                    (up to 20)          |
| S13: WEAPON                              (up to 16)          |
| S14: SHIELD or ARMOUR                    (up to 20)          |
| S15: ELECTRICAL                          (up to 3)           |
| S16: WEAPON                              (up to 16)          |
+--------------------------------------------------------------+

### Death Star

+--------------------------------------------------------------+
| Hull: Death Star                                             |
| Dock capacity: unlimited                                     |
| S01: ORBITAL or ELECTRICAL               (up to 1)           |
| S02: WEAPON                              (up to 32)          |
| S03: ELECTRICAL                          (up to 4)           |
| S04: ELECTRICAL                          (up to 4)           |
| S05: SHIELD                              (up to 20)          |
| S06: SHIELD                              (up to 20)          |
| S07: ELECTRICAL                          (up to 4)           |
| S08: WEAPON                              (up to 32)          |
| S09: ELECTRICAL                          (up to 4)           |
| S10: WEAPON                              (up to 32)          |
| S11: ORBITAL or ELECTRICAL               (up to 1)           |
| S12: SHIELD or ARMOUR                    (up to 20)          |
| S13: ELECTRICAL                          (up to 4)           |
| S14: SHIELD or ARMOUR                    (up to 20)          |
| S15: ELECTRICAL                          (up to 4)           |
| S16: WEAPON                              (up to 32)          |
+--------------------------------------------------------------+

---

## Follow-ups

- Add page-image-backed coordinate extraction for true silhouette-position ASCII if needed.
- Cross-check OCR ambiguities (especially Nubian and Death Star labels) against the raw PDF pages.
- Define canonical slot-category enum values for backend validation in PRD 18 implementation.
