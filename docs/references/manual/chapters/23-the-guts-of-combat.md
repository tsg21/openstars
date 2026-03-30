# 23. The Guts of Combat

### THE GUTS OF COMBAT

Here’s some information to help you understand the behavior of fleets in battle. You may find it useful in planning battle strategies. It may also help satisfy your drive to collect Stars! military trivia.

### ABOUT THE BATTLE BOARD

The battle board is the grid you see in the Battle VCR. The fleets are distributed on the board as tokens. Each token is a stack of identical ships from a single fleet. The individual tokens move around the board targeting enemy tokens, following the tactics specified in their battle plan. Each location can contain any number of tokens.

Battles last up to 16 rounds. One round of battle is each token getting a chance to move and fire. A round is broken into phases, where one phase is a single token moving or firing.

Each round has three parts:

First, all tokens target an enemy token that best meets their battle plan criteria.

Second, all ships move, in order from heaviest to lightest. Ships’weights are randomly adjusted by up to 15% each turn, giving ships that are nearly identical a chance to alternate going first. All ships that can move three squares this round move one square first, then all ships that can move two squares move one square, then all ships that can move at least one square move a square.

Third, weapons fire, in order from highest initiative to lowest.

### ARMOR, SHIELDS AND DAMAGE

Read this section with the following section on Weapon Properties for a fuller understanding of how armor, shields and specific weapon types interact in Stars!.

Armor and Shields

Hulls have a base armor value. Additional armor is added to this value.

Shields will take damage and fail before enemy weapons attack your armor. In a token the shields overlap. For example, if your fleet has 20 scouts with shields valued at 20 each, you have a pool of 400 shields points that must be destroyed before the armor on any of those ships is damaged—unless your opponent is using torpedoes. Torpedoes damage both shields and armor, taking shield points and armor points from the token with each successful attack..

Shields are at full strength at the start of each battle. This means if you leave a battle one turn and enter a battle the next turn, your shields will be back at full strength. If you have the Regenerating Shields trait then your shields will regenerate 10% of their base value at the start of every round.

If you are using beam weapons and the damage your token can inflict on an enemy’s token is more than enough to destroy the enemy token, the remainder is used on additional enemy tokens in the same location, limited only by the number of ships in the attacking token.

For example, one token does a total of 1000 dp of beam weapon damage. The primary target is destroyed after taking 500 damage. If there are 10 other tokens at the same location, each consisting of a single ship with 150 dp of armor, three tokens would be destroyed and one would take 33% damage.

If those 10 tokens had been a single token of 10 ships they would have still lost three ships, but each of the remaining seven ships would have taken less than 5% damage. If the ships had 100 dp armor and 50 dp shields each, then stacked together the shields would have absorbed all 500dp and no ships would have been lost. No combination of shields and armor would have saved those three ships with each ship in a separate token.

Damage

Damage is applied as follows: If the damage applied to a token’s armor exceeds the remaining armor of one or more of the ships in the token, then those ships are destroyed. Any remaining damage is spread over the ENTIRE token, with the damage being divided up equally among the remaining ships.

A separate damage value is stored for each token in the battle. Stars! stores the percentage of ships in the token that are damaged, along with the percentage of damage to each ship.

Damage is displayed as C @ P%, where C is the count of damaged tokens in a fleet and P is the percentage of damage inflicted. For example, 10@33% says that 10 tokens are one-third damaged.

For the type of damage inflicted by beam weapons and torpedoes, read the following description of Weapons and Battle Devices.

### WEAPONS AND BATTLE DEVICES

Read this section with the preceding section on Armor, Shields and Damage for a fuller understanding of how armor, shields and specific weapon types interact in Stars!.

Weapons and Starbases

All weapons mounted on Starbases get a +1 added to their range.

Beam Weapons

Beam weapons always hit their target, but decay in strength at a rate of 10% pro-rated over their maximum range. For example, a weapon that will do 100 dp to a target in the same square and has a maximum range of 3 will only do 94 dp to a target two squares away. All damage from beam weapons is applied to shields first. Any damage not absorbed by the shields is applied to armor.

If an attacking token has more than one ship and its beam weapon strike destroys the target token, then the remaining damage is applied to other tokens in range. The maximum number of tokens targeted is the number of ships in the attacking token.

The following beam weapon information is provided for comparison purposes. See the Beam Weapons section of the Technology Browser for the exact statistics of a specific weapon.

Normal Beam Weapons

Damage: From 10 to 430 damage points Range: From 1 to 3 squares Initiative: From 5 to 9

Range 0 Weapons

Damage: From 90 to 600 damage points Range: Same square only Initiative: 10 to 11

Gattling Weapons

Damage: From 13 to 200 damage points Range: 2 squares Initiative: 12 to 13

These are extremely powerful weapons that hit every enemy token in their range each time they fire. They also sweep minefields as if they were range 4.

Shield Sappers

Damage: From 82 to 541 damage points Range: 3 Initiative: 14

These medium range weapons are very powerful but are only useful against shields. They have no effect on armor. They do have a higher initiative than any other weapon. This means that they will take out the enemy shields before your other weapons fire.

Shield Sappers cannot perform minesweeping.

Minesweeping

Each beam weapon automatically sweep up to (Damage x Range x Range) mines per year.

Torpedoes

Each torpedo fired has a chance of missing. For example: If a token has two ships, each with a weapon slot holding two normal torpedoes, then a single shot fires all four torpedoes. Each torpedo has a chance to hit or miss

according to its accuracy value. Normal torpedoes have an accuracy of 75%, which means that it is likely that three of the four torpedoes would hit. Torpedo accuracy can be improved using Battle Computers. Jammers can decrease the accuracy of enemy torpedoes.

Torpedoes that hit their primary target apply half of their damage directly to the armor of the target token. The other half of the damage is applied to the shields. Any damage that isn’t absorbed by the shields is applied to the armor.

The maximum number of ships that can be killed by a torpedo strike is the number of torpedoes that hit. So in the preceding example the strike can kill up to 3 ships. If the target token has one ship in it and the hits caused more damage than was necessary to destroy it, then the damage is applied to other tokens in the same square. This type of damage is applied first to the shields; any damage not absorbed by the shields is applied to the armor. In no case can the number of ships destroyed exceed the number of torpedoes that hit.

Torpedoes that miss do collateral damage to the target token only. Collateral damage is 1/8th of the normal damage of the torpedo and works much like a Shield Buster beam weapon. In other words it only affects shields.

The following torpedo information is provided for comparison purposes. See the Torpedoes section of the Technology Browser for the exact statistics of a specific weapon.

Normal Torpedoes

Damage: From 5 to 300 damage points Range: From 4 to 5 squares Initiative: from 0 to 4 Accuracy: 35% to 80%

Capital Ship Missiles

Damage: From 85 to 525 damage points Range: From 5 to 6 squares Initiative: From 0 to 3 Accuracy: 20% to 30%

These powerful torpedoes do more damage than normal torpedoes and have a longer range than any other weapon. Due to their poor accuracy and the fact that a single torpedo can take out at most one enemy ship, these missiles are best mounted on starbases and battleships with a lot of Battle Computers. Their ideal use is against large ships and starbases.

Capital ship missiles do twice the stated damage if the enemy ship has no remaining shields.

See the Electrical section of the Technology Browser for a descriptions of each Jammer.

Jammers

Jammers decrease torpedo accuracy. The Jammer 10 and 50 are available to Inner Strength players only. Jammer strength is additive. For example, a ship with three 20% Jammers reduces a normal torpedo’s 75% accuracy by 20% three times:

75 x.8 x.8 x.8 = 38% torpedo accuracy

Battle Computers

These devices increase the initiative of all weapons on the ship. The three different devices range from +1 to +3 initiative. They also decrease torpedo inaccuracy by 20 to 50%.

Decreasing the inaccuracy of a torpedo by a percentage is not the same as increasing the accuracy by that percentage. As torpedo accuracy becomes higher it becomes harder to improve it.

Computing the effects of a battle computer:

Example 1: A normal 75% accurate torpedo fired using a 50% battle computer.

Incorrect calculation: 75% x 1.5 = 112% accuracy.

Correct calculation: 100 - ((100 - 75) x.5) = 88% accuracy.

Example 2: A normal torpedo’s 75% accuracy is modified by two 30% battle computers by decreasing its inaccuracy 30% twice. 100 - ((100 - 75) x.7 x.7) = %88 torpedo accuracy.

If the attacking token has battle computers and the target has jammers the devices cancel each other out on a 1% to 1% basis.

Examples:

Target token has Jammers totaling a 50% decrease in accuracy. Attacker’s battle computers add up to a 45% decrease in inaccuracy. Result: 5% decrease in accuracy.

Target token has Jammers totaling a 30% decrease in accuracy. Attacker’s battle computers add up to a 40% decrease in inaccuracy. Result: 10% decrease in inaccuracy.

Energy Dampener

This device slows down ALL ships in the entire battle board by 1 square of movement per round, for the duration of the battle. This is true even if the ship carrying the Dampener is destroyed before the end of the battle (the device has a lasting affect). The effect is not additive, so there is no advantage or penalty for having more than one Dampener in a battle.

Capacitors

Increase the damage caused by all beam weapons on board by a percentage. Capacitor values run from 10% to 20%. The maximum additional percentage increase in damage caused by multiple capacitors is 250%.

In this example, a ship has a beam weapon capable of 100 damage and three 10% capacitors:

100dp x 1.1 x 1.1 x 1.1 = 133dp

### DAMAGE REPAIR

If after a battle your fleet has one or more ship types listed in red in the Fleet Composition tile, then you have taken damage. Click on a red ship name to display how much damage has been done.

Ship repair restores the armor value at an annual rate based on the ship’s location:

Ship location

Moving through space

Stopped in space

Orbiting but not bombing an opponent’s planet

Annual rate

1%

2%

3%

Orbiting a planet you own that has a space dock

20%

Orbiting a planet you own that has a starbase but 8% not a space dock

Orbiting a planet you own that does not have a starbase

5%

Orbiting a planet you’re bombing

no repair (continued)

Ship location (cont)

Stopped or orbiting, with at least one Fuel Transport hull in the fleet

Annual rate (cont)

additional 5%

Stopped or orbiting, with at least one Super Fuel Xport hull in the fleet

additional 10%

For example, a ship with a base of 25 damage points (dp) plus armor with a value of 75 dp has a maximum armor value of 100 dp. It takes 10 dp of damage, it would take 2 years in deep space, or one year in orbit, to fully repair the armor.

If you’re orbiting an opponent’s planet and your fleet has Attack orders, repairs will not happen. Repairs also do not happen during the year a fleet is using a stargate.

During the years the starbase is under attack, the fleet will be repaired as if the starbase was not present.

Fuel Transport/XPort Hull Advantage

Notice that the table shows an advantage of using the Fuel Transport and Xport hulls: they repair other ships in the fleet, as well as collecting fuel. You only need one Fuel Transport hull in the fleet to gain the 5% increase in the repair rate, or one Super Fuel Xport to see a 10% increase. Adding extra Transport or Xport hulls doesn’t increase the rate. And you always see the gain provided by the more advanced hull. Thus, if you have both Fuel Transport and Super Fuel Xport hulls in the same fleet, you gain only the 10% increase provided by the Super Fuel Xport hull.

Starbase Repair

For ordinary players, starbases are repaired at a rate of 10% a year. For players with the Inner Strength race trait, starbases are repaired at 15% a year.

### MOVEMENT, INITIATIVE AND FIRING IN BATTLE

Movement

Movement is always between ship can move per round is computed in formula:

and 2

squares per round. The distance a

squares, using the following

When you calculate the formula for movement and other formulas, remember that all multiplies and divides happen before any addition or subtraction.

The Formula for Movement

Movement = (Ideal_Speed_of_Engine - 4)

### 4

### 70

- weight
+ ⁄ x Number_of_Maneuvering_Jets

+

x Num_Overthrusters

### 4

Number_of_Engines

Movement in Squares per Round

Movement

### 1

### 1

### 1

### 1

### 2

### 2

### 2

Round

### 4

### 0

### 1

### 1

### 1

### 1

### 2

### 2

### 2

### 2

### 5

### 1

### 1

### 1

### 2

### 2

### 2

### 2

### 3

### 3

### 3

### 1

### 0

### 1

### 1

### 2

### 1

### 2

### 2

### 3

### 1

### 1

### 1

### 1

### 2

### 2

### 2

### 2

### 3

### 3

### 2

### 0

### 1

### 1

### 1

### 1

### 2

### 2

### 2

### 2

### 6

### 0

### 1

### 1

### 1

### 1

### 2

### 2

### 2

### 2

### 7

### 1

### 0

### 1

### 1

### 2

### 1

### 2

### 2

### 3

### 8

### 0

### 1

### 1

### 1

### 1

### 2

### 2

### 2

### 2

Order of Movement

Movement happens in three phases:

Phase 1: All tokens that can move 3 squares this round get to move 1 square.

Phase 2: All tokens that can move 2 or more squares this round get to move 1 square.

Phase 3: All tokens that can move this round get to move 1 square.

In each phase tokens move in order from heaviest to lightest, with a margin of

+

- 15%.
Each token attempts to find the best square to move into that matches the tactic they’ve been assigned. For example, you have selected Maximize Net Damage and have a ship with a combination of range 1 and 2 weapons. Your enemy has a ship with a combination of range 1 and 2 weapons also, but

their range 1 weapons are much better than yours. You will stay at range 2 because that is where you will do the highest net damage.

Overthrusters, Maneuvering Jets and Movement

Multiple Overthrusters and Maneuvering Jets are additive. One Overthruster gives the token a speed bonus of each extra Overthruster adding

square of movement per round, with

square.

A Maneuvering Jet gives the token an extra of battle, with each extra Jet adding

square.

square of movement per round

Maximum movement is 2 Overthrusters and Maneuvering Jets the design may have.

squares per round, regardless of how many

Firing

Weapons fire in order from highest to lowest initiative. Weapons fire on a weapon slot-by-weapon slot basis, the shortest range weapons of a given initiative firing first. If the target token is destroyed, damage will stream over to other tokens in range.

Initiative

Initiative determines the firing order in battle. All ships have an innate hull initiative value, ranging from 0 to 18. Each battle computer increases initiative by 1, 2 or 3 points. Firing initiative is the sum of the hull initiative, battle computers, race modifiers (if you have the War Monger trait) and the weapon’s initiative.

Highest initiative fires first. If a ship has a base initiative of 11 and beam weapons with an initiative of 5 for a total initiative of 16, and a second ship has a base initiative of 14 and a torpedo weapon with an initiative of 3 for a total initiative of 17, the second ship fires first. If the torpedo ship also had a second weapon with an initiative of 1 then the torpedo would fire first, the other ship’s beams would fire, followed by the torpedo ship’s second weapon.
