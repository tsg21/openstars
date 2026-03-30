# 26. The Guts of Minefields

## Types of Mines

### Standard Mines

- Effect: explodes on contact
- Maximum safe speed: Warp `4`
- Damage per ship: `100` per engine, or `125` per engine for ramscoops
- Minimum fleet damage: `500`, or `600` for ramscoops
- Chance to hit: `0.3%` per light year traveled for each Warp above the safe speed

Example: a fleet traveling at Warp `9` has a `1.5%` chance per light year traveled that turn. If it travels `10` light years through the field, it has a `10.5%` chance of triggering a mine.

### Heavy Mines

- Effect: explodes on contact
- Maximum safe speed: Warp `6`
- Damage per ship: `500`, or `600` for ramscoops
- Minimum fleet damage: `2000`, or `2500` for ramscoops
- Chance to hit: `1%` per light year traveled for each Warp above the safe speed

Example: a fleet traveling at Warp `9` has a `3%` chance per light year traveled that turn. If it travels `10` light years through the field, it has a `30%` chance of triggering a mine.

### Speed Trap Mines

- Effect: halts the fleet without causing damage
- Maximum safe speed: Warp `5`
- Damage per ship: none
- Minimum fleet damage: none
- Chance to hit: `3%` per light year traveled for each Warp above the safe speed

Example: a fleet traveling at Warp `9` has a `15%` chance per light year traveled that turn. If it travels `10` light years through the field, it is guaranteed to trigger a mine.

## Detecting Minefields

### Minefield Cloak Value

| Scanner type | Minefield cloak |
| --- | ---: |
| Penetrating scanners | `0%` |
| Non-penetrating scanners | `75%` |

### Conditions for Detecting an Opponent's Minefield

You can see both the center and radius of an opponent's minefield if any of the following is true:

1. The center of the minefield is in range of your penetrating scanner.
2. You have hit the minefield at least once, and the center is in range of your normal scanners.
3. You are inside the minefield.

## Ship Cloak Effectiveness in Minefields

When a ship is in a minefield and the mines are acting as scanners, the ship's cloak effectiveness is always treated as an absolute value. For example, `90%` cloak means a `10%` chance of detection.

Only races with the `Space Demolition` primary racial trait can use minefields as non-penetrating scanners.

## Race Traits and Minefields

### Special Capability

For `Space Demolition` races, minefields act as normal scanners, but they still do not detect fleets orbiting planets.

### Mine Dispensers Available by Race

#### Space Demolition

- `Mine Dispenser 40` (`40` mines per year)
- `Mine Dispenser 50` (`50` mines per year), available to all except `War Monger`
- `Mine Dispenser 80` (`80` mines per year)
- `Mine Dispenser 130` (`100` mines per year)
- `Heavy Dispenser 50` (`50` mines per year)
- `Heavy Dispenser 110` (`110` mines per year)
- `Heavy Dispenser 200` (`200` mines per year)
- `Speed Trap 20` (`20` mines per year), requires `Space Demolition` or `Inner Strength`
- `Speed Trap 30` (`30` mines per year)
- `Speed Trap 50` (`50` mines per year)

#### Inner Strength

- `Mine Dispenser 50`
- `Speed Trap 20`

#### War Monger

`War Monger` races cannot lay mines and have no mine dispensers of any type.
