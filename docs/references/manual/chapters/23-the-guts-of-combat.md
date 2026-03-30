# 23. The Guts of Combat

Here is background material on how fleets behave in battle. It is useful both for planning battle strategies and for understanding the smaller combat details behind Stars!.

## About the Battle Board

The battle board is the grid shown in the `Battle VCR`. Fleets appear on the board as tokens. Each token is a stack of identical ships from a single fleet. Tokens move around the board and target enemy tokens according to the tactics in their assigned battle plan. Any number of tokens can occupy the same location.

Battles last up to `16` rounds. One round consists of each token getting a chance to move and fire. A round is broken into phases, where one phase is a single token moving or firing.

Each round has three parts:

1. All tokens choose an enemy token that best matches their battle plan criteria.
2. All ships move, from heaviest to lightest. Ship weights are randomly adjusted by up to `15%` each turn, giving nearly identical ships a chance to alternate moving first. All ships that can move three squares this round move one square first, then all ships that can move two squares move one square, then all ships that can move at least one square move one square.
3. Weapons fire, from highest initiative to lowest.

## Armor, Shields, and Damage

Read this section together with the next section on weapon properties for a fuller understanding of how armor, shields, and specific weapon types interact in Stars!.

### Armor and Shields

Hulls have a base armor value. Additional armor is added to that value.

Shields absorb damage and fail before enemy weapons can attack armor. Within a token, shields overlap. For example, if your fleet has `20` scouts with shields valued at `20` each, the token has a shared pool of `400` shield points that must be destroyed before armor damage is applied, unless the attacker is using torpedoes. Torpedoes damage both shields and armor, taking shield points and armor points from the token with each successful hit.

Shields begin each battle at full strength. If you leave one battle and enter another on the next turn, your shields are restored. If you have the `Regenerating Shields` trait, your shields regenerate `10%` of their base value at the start of every round.

If a token using beam weapons can inflict more damage than is needed to destroy the primary enemy token, the extra damage can spill into additional enemy tokens in the same location. The number of additional tokens affected is limited only by the number of ships in the attacking token.

Example: one token inflicts `1000 dp` of beam damage. The primary target is destroyed after taking `500` damage. If there are `10` other single-ship tokens in the same location, each with `150 dp` of armor, three tokens are destroyed and a fourth takes `33%` damage.

If those same `10` ships had been combined into one token, they would still lose three ships, but the remaining seven ships would each take less than `5%` damage. If each ship had `100 dp` armor and `50 dp` shields, then the combined shields would absorb all `500 dp` and no ships would be lost. No combination of shields and armor would have saved those three ships if each ship had been in its own token.

### Damage

Damage is applied like this: if armor damage exceeds the remaining armor of one or more ships in the token, those ships are destroyed. Any remaining damage is then spread over the entire token, divided equally among the surviving ships.

Stars! stores a separate damage value for each token. It tracks the percentage of ships in the token that are damaged, along with the percentage of damage on each damaged ship.

Damage is displayed as `C @ P%`, where `C` is the count of damaged tokens in a fleet and `P` is the percentage of damage. For example, `10 @ 33%` means `10` tokens are one-third damaged.

For the types of damage caused by beam weapons and torpedoes, read the next section on weapons and battle devices.

## Weapons and Battle Devices

Read this section together with the previous section on armor, shields, and damage for a fuller understanding of how armor, shields, and specific weapon types interact in Stars!.

### Weapons and Starbases

All weapons mounted on starbases gain `+1` range.

### Beam Weapons

Beam weapons always hit, but their strength decays by `10%`, prorated over maximum range. For example, a beam that does `100 dp` at range `0` and has maximum range `3` will do only `94 dp` to a target two squares away.

All beam damage is applied to shields first. Any damage not absorbed by shields is applied to armor.

If an attacking token contains more than one ship and its beam strike destroys the target token, remaining damage can spill over to other tokens in range. The maximum number of tokens affected is the number of ships in the attacking token.

The following beam-weapon information is for comparison. See the `Beam Weapons` section of the `Technology Browser` for exact statistics.

#### Normal Beam Weapons

- Damage: `10` to `430 dp`
- Range: `1` to `3` squares
- Initiative: `5` to `9`

#### Range 0 Weapons

- Damage: `90` to `600 dp`
- Range: same square only
- Initiative: `10` to `11`

#### Gattling Weapons

- Damage: `13` to `200 dp`
- Range: `2` squares
- Initiative: `12` to `13`

Gattling weapons are extremely powerful and hit every enemy token in range each time they fire. They also sweep minefields as if they had range `4`.

#### Shield Sappers

- Damage: `82` to `541 dp`
- Range: `3`
- Initiative: `14`

These medium-range weapons are powerful against shields but useless against armor. Their initiative is higher than that of any other weapon, so they strip enemy shields before your other weapons fire.

Shield Sappers cannot sweep minefields.

### Minesweeping

Each beam weapon automatically sweeps up to:

```text
Damage x Range x Range
```

mines per year.

### Torpedoes

Each torpedo fired has its own chance to miss. For example, if a token has two ships and each ship has a weapon slot carrying two normal torpedoes, a single shot launches all four torpedoes. Each torpedo rolls separately against its accuracy value. Normal torpedoes have `75%` accuracy, so about three of the four are likely to hit. `Battle Computers` improve torpedo accuracy; `Jammers` reduce enemy torpedo accuracy.

Torpedoes that hit their primary target apply half their damage directly to armor. The other half is applied to shields, and any shield overflow is then applied to armor.

The maximum number of ships that can be killed by a torpedo strike is the number of torpedoes that hit. In the example above, at most three ships can be destroyed. If the target token contains only one ship and the hit damage exceeds what is needed to destroy it, the extra damage is applied to other tokens in the same square. That spillover damage hits shields first, then armor. In no case can the number of ships destroyed exceed the number of torpedoes that hit.

Torpedoes that miss do collateral damage only to the target token. Collateral damage is `1/8` of normal torpedo damage and behaves like a shield-buster beam: it affects shields only.

The following torpedo information is for comparison. See the `Torpedoes` section of the `Technology Browser` for exact statistics.

#### Normal Torpedoes

- Damage: `5` to `300 dp`
- Range: `4` to `5` squares
- Initiative: `0` to `4`
- Accuracy: `35%` to `80%`

#### Capital Ship Missiles

- Damage: `85` to `525 dp`
- Range: `5` to `6` squares
- Initiative: `0` to `3`
- Accuracy: `20%` to `30%`

These missiles do more damage than normal torpedoes and have longer range than any other weapon. Because of their poor accuracy and the fact that one torpedo can destroy at most one enemy ship, they work best on starbases and heavily computerized battleships. Their ideal targets are large ships and starbases.

Capital ship missiles do twice their stated damage if the enemy ship has no remaining shields.

See the `Electrical` section of the `Technology Browser` for descriptions of each `Jammer`.

### Jammers

Jammers reduce torpedo accuracy. `Jammer 10` and `Jammer 50` are available only to `Inner Strength` players. Jammer strength is additive in multiplicative steps. For example, a ship with three `20%` jammers reduces a normal torpedo's `75%` accuracy like this:

```text
75 x .8 x .8 x .8 = 38% torpedo accuracy
```

### Battle Computers

Battle Computers increase the initiative of all weapons on the ship. The three computer types add `+1`, `+2`, or `+3` initiative. They also reduce torpedo inaccuracy by `20%` to `50%`.

Reducing inaccuracy by a percentage is not the same as increasing accuracy by that percentage. The closer a torpedo is to `100%` accuracy, the harder it is to improve further.

Computing the effects of a battle computer:

Example 1: a normal `75%`-accurate torpedo fired with a `50%` battle computer.

```text
Incorrect: 75% x 1.5 = 112% accuracy
Correct:   100 - ((100 - 75) x .5) = 88% accuracy
```

Example 2: a normal torpedo's `75%` accuracy modified by two `30%` battle computers.

```text
100 - ((100 - 75) x .7 x .7) = 88% torpedo accuracy
```

If the attacker has battle computers and the target has jammers, the two effects cancel on a `1%`-for-`1%` basis.

Examples:

- Target jammers total a `50%` decrease in accuracy. The attacker's battle computers total a `45%` decrease in inaccuracy. Result: `5%` decrease in accuracy.
- Target jammers total a `30%` decrease in accuracy. The attacker's battle computers total a `40%` decrease in inaccuracy. Result: `10%` decrease in inaccuracy.

### Energy Dampener

This device slows all ships on the entire battle board by `1` square of movement per round for the duration of the battle. The effect remains even if the ship carrying the dampener is destroyed before the battle ends. The effect is not additive, so having more than one dampener in a battle gives no further benefit or penalty.

### Capacitors

Capacitors increase the damage of all beam weapons on the ship by a percentage. Capacitor values range from `10%` to `20%`. Multiple capacitors can increase beam damage by up to `250%`.

Example: a ship has a beam weapon that does `100 dp` and three `10%` capacitors:

```text
100 dp x 1.1 x 1.1 x 1.1 = 133 dp
```

## Damage Repair

If, after a battle, your fleet shows one or more ship types in red in the `Fleet Composition` tile, the fleet has taken damage. Click a red ship name to see how much damage it has suffered.

Ship repair restores armor at an annual rate based on ship location:

| Ship location | Annual repair rate |
| --- | --- |
| Moving through space | `1%` |
| Stopped in space | `2%` |
| Orbiting, but not bombing, an opponent's planet | `3%` |
| Orbiting your own planet with a space dock | `20%` |
| Orbiting your own planet with a starbase but not a space dock | `8%` |
| Orbiting your own planet without a starbase | `5%` |
| Orbiting a planet you're bombing | no repair |
| Stopped or orbiting, with at least one `Fuel Transport` hull in the fleet | additional `5%` |
| Stopped or orbiting, with at least one `Super Fuel Xport` hull in the fleet | additional `10%` |

Example: a ship has `25 dp` of base armor plus `75 dp` from armor components, for `100 dp` total armor. If it takes `10 dp` damage, it would need `2` years in deep space or `1` year in orbit to repair fully.

If you are orbiting an opponent's planet and your fleet has `Attack` orders, no repairs occur. Repairs also do not occur during a year in which a fleet uses a stargate.

If a starbase is under attack, fleets there are repaired as though the starbase were not present.

### Fuel Transport/Xport Hull Advantage

The table shows an extra advantage for `Fuel Transport` and `Super Fuel Xport` hulls: they help repair other ships in the fleet in addition to collecting fuel. You need only one `Fuel Transport` hull to gain the `5%` bonus, or one `Super Fuel Xport` hull to gain the `10%` bonus. Additional copies do not increase the bonus, and if both hull types are present you receive only the `10%` bonus from the `Super Fuel Xport`.

### Starbase Repair

For ordinary players, starbases repair at `10%` per year. Players with the `Inner Strength` trait repair starbases at `15%` per year.

## Movement, Initiative, and Firing in Battle

### Movement

Combat movement is always between `1/2` and `2 1/2` squares per round. Ship movement per round is computed in quarter-squares using this formula:

```text
Movement =
  ((Ideal_Speed_of_Engine - 4) * Number_of_Engines / 4)
  - (weight / 70)
  + (1/4 * Number_of_Maneuvering_Jets)
  + (1/2 * Num_Overthrusters)
```

When working this or any other formula, remember that multiplication and division happen before addition or subtraction.

### Movement in Squares per Round

| Movement | Round 1 | Round 2 | Round 3 | Round 4 | Round 5 | Round 6 | Round 7 | Round 8 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `1/2` | `0` | `1` | `0` | `1` | `0` | `1` | `0` | `1` |
| `3/4` | `1` | `0` | `1` | `1` | `1` | `0` | `1` | `1` |
| `1` | `1` | `1` | `1` | `1` | `1` | `1` | `1` | `1` |
| `1 1/4` | `1` | `1` | `1` | `2` | `1` | `1` | `1` | `2` |
| `1 1/2` | `1` | `2` | `1` | `2` | `1` | `2` | `1` | `2` |
| `1 3/4` | `2` | `1` | `2` | `2` | `2` | `1` | `2` | `2` |
| `2` | `2` | `2` | `2` | `2` | `2` | `2` | `2` | `2` |
| `2 1/4` | `2` | `2` | `2` | `3` | `2` | `2` | `2` | `3` |
| `2 1/2` | `2` | `3` | `2` | `3` | `2` | `3` | `2` | `3` |

### Order of Movement

Movement happens in three phases:

1. All tokens that can move `3` squares this round move `1` square.
2. All tokens that can move `2` or more squares this round move `1` square.
3. All tokens that can move this round move `1` square.

Within each phase, tokens move from heaviest to lightest, with a margin of `+/- 15%`.

Each token tries to move into the best square for its assigned tactic. For example, if you select `Maximize Net Damage` and your ship has a mix of range-`1` and range-`2` weapons, while the enemy also has range-`1` and range-`2` weapons but much stronger range-`1` weapons, your ship will stay at range `2` because that is where it can inflict the highest net damage.

### Overthrusters, Maneuvering Jets, and Movement

Multiple `Overthrusters` and `Maneuvering Jets` are additive.

- One `Overthruster` gives the token an extra `1/2` square of movement per round. Each additional `Overthruster` adds another `1/2` square.
- One `Maneuvering Jet` gives the token an extra `1/4` square of movement per round. Each additional jet adds another `1/4` square.

Maximum movement is `2 1/2` squares per round, regardless of how many `Overthrusters` and `Maneuvering Jets` the design has.

### Firing

Weapons fire from highest initiative to lowest. Weapons fire slot by slot, with the shortest-range weapons of a given initiative firing first. If the target token is destroyed, damage streams over to other tokens in range.

### Initiative

Initiative determines firing order in battle. All ships have an innate hull initiative ranging from `0` to `18`. Each battle computer adds `1`, `2`, or `3` initiative points. Final firing initiative is the sum of hull initiative, battle computers, race modifiers such as `War Monger`, and weapon initiative.

Highest initiative fires first. For example, if one ship has base initiative `11` and beam weapons with initiative `5`, its firing initiative is `16`. If another ship has base initiative `14` and a torpedo weapon with initiative `3`, its firing initiative is `17`, so it fires first. If that torpedo ship also has a second weapon with initiative `1`, the torpedo fires first, then the other ship's beams, then the torpedo ship's second weapon.
