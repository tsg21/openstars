# Stars! Documentation - Battlefield and Fleet Movements

Source URL: https://www.elite-games.ru/stars/doc/battle_field.shtml

Original title: Stars! Документация - Поле сражения и перемещение флотов

Note: Automatically translated from Russian. Review against the source HTML before relying on subtle rules wording.

[Image:] Stars! Documentation - Battlefield and Fleet Movements

Battlefield and Fleet Movements

The battle takes place on a field measuring 10x10 cells. At the start of the battle, each ship is in a cell of its own race. Further, during the battle, the ship is either in some cell, or is destroyed or leaves the battle.

Players do not control ships in battle. The battle takes place automatically, in which ships act in accordance with tactical schemes (battle plans) predetermined for them by the players.

If before the battle the ships were united into a fleet, then the ships of the same type in this fleet represent an independent group that acts as a single whole (they move across the field together, shoot simultaneously (for weapons of the same type), are impenetrable with beam weapons until the shields are completely removed, and have the same level of armor damage).

Order of events during the battle

A battle can last up to 16 rounds, after which the battle ends (even if everyone is alive and wants to fight). In each round, ships move and shoot.

During each round the following happens:

*1. Ships that move 3 spaces this round move 1 space.

*2. Ships that move 2 or 3 spaces this round move 1 space.

*3. Ships that move 1, 2, or 3 spaces this round move 1 space.

4. All types of weapons fire volleys in descending order of initiatives.* *

5. RS races restore shields by 10%. If a race ship has lost its shields, they are not restored. 10% is considered from the initial value of shields.

*When moving, ships that are lighter in mass move later within one point. This condition is met with an error of 15% by weight.

* * If the initiative is the same, then the order is random. Initiative is an integer from 0 to 63 (it cannot be more than 63 even if there are devices that increase it).

After passing all the points, if there is someone to fight with, then the next round begins (up to 16). If the opponents are all destroyed or left the battlefield, then the battle ends.

Speed of maneuvering in battle

The speed of maneuvering (movement) in battle is calculated for each group of ships individually.

The maneuvering speed is a fractional discrete value, it can vary from 0.5 to 2.5 in increments of 0.25 for ships and is equal to 0 for orbital stations (they are stationary in battle).

In case Stars! does not correctly display the fractional parts of the speed 1/4, 1/2 and 3/4, then for them they are shown as the letters j, S and s, respectively:

0.5 | 0.75 | 1 | 1.25 | 1.5 | 1.75 | 2 | 2.25 | 2.5

S | s | 1 | 1j | 1S | 1s | 2 | 2j | 2S

The maneuvering speed depends on the mass of the ship, the type of engine, and the presence of additional maneuvering devices. The calculation formula is:

({ideal engine speed} - 4) / 4 - {mass of the ship in kT} / 70 / 4 / {number of engines in the ship} + 1/4*MJ number + 1/2*OT number

If the race is WM, then 1/2 must be added to the result.

The final number cannot exceed 2.5, and anything over 2.5 is reduced to 2.5.

The resulting number is rounded to the nearest 0.25.

The maneuvering speed shows how many squares the ship will move on average each round.

For each maneuvering speed value, it is predetermined how many cells the ship will move:

Speed

Round 1

Round 2

Round 3

Round 4

Round 5

Round 6

Round 7

Round 8

Rounds to leave the battlefield*

0.5
1
0
1
0
1
0
1
0
13

0.75
1
1
0
1
1
1
0
1
9

1
1
1
1
1
1
1
1
1
7

1.25
2
1
1
1
2
1
1
1
5

1.5
2
1
2
1
2
1
2
1
5

1.75
2
2
1
2
2
2
1
2
4

2
2
2
2
2
2
2
2
2
4

2.25
3
2
2
2
3
2
2
2
3

2.5
3
2
3
2
3
2
3
2
3

* - the last round of presence, at the end his ship is no longer there.

After completing 8 rounds, the sequence repeats again.

Leaving the battlefield

If a ship is given a battle plan, according to which it must escape from an attack, then the ship must make 7 movements across cells with such a battle plan to leave the battlefield. All unarmed ships, despite their battle plan, perform the maneuver of leaving the battlefield. Thus, if the ship moves 7 random cells, it leaves the battlefield and will not appear on the field until the end of the battle. If 7 cells are passed in a round, then at the end of the round the ship is no longer on the battlefield and it is no longer possible to destroy it this year.
