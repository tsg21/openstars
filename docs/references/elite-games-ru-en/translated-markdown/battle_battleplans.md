# Stars! Documentation - Battleplans

Source URL: https://www.elite-games.ru/stars/doc/battle_battleplans.shtml

Original title: Stars! Документация - Батлпланы

Note: Automatically translated from Russian. Review against the source HTML before relying on subtle rules wording.

[Image:] Stars! Documentation - Battleplans

Battleplans

Battleplans (tactical battle plans) are a predetermined description of the behavior of a ship in battle, which is given to the ship before the battle and in accordance with which the ship will act during the entire battle.

The battle plan determines by what principle the ship will take up positions while moving, how it will select targets to hit, and whether or not it will drop its cargo before the battle.

The battleplan is given to the fleet. If it is necessary to assign different battle plans to individual ships of the fleet, then for this it is necessary to divide the ships into separate fleets and give the fleets different tactical schemes.

The player has the opportunity to create his own tactical schemes, for each of which there are a number of points (which will be discussed separately). In addition, players are given as an example a number of standard tactical schemes that may be suitable.

Primary & Secondary Target

Primary Target - the primary target to kill. Secondary Target - a secondary target to kill.

These points are valid only if the ship is combat, that is, capable of causing damage to someone. Accordingly, in this case, if there are primary targets on the battlefield, then the ship considers them as its only targets when maneuvering, and when firing, it first hits the primary, and if the primary is out of reach or destroyed, then it switches to secondary.

If there is no primary on the field, then the ship takes a position to hit the secondary, and if the secondary is in the damage radius, then salvos are fired at them.

If there are no primary and secondary targets, then the ship is in a stupor, it does not hit anyone and moves only if it is necessary from a tactical point of view (for example, if a minimum of damage is required, then the ship will try not to come under attack).

If the enemy ship is not included in the set of primary and secondary, then his ship will not attack.

The selection set of primary and secondary groups are groups according to the classification of combat functionality.

Tactical

Tactics determine the algorithm for changing position in battle and the need to exit the battle:

Disengage

Unconditional exit from the battle. Make 7 random movements and exit the battle. All non-combat ships receive this tactic, even if the fleet chooses another.

Disengage if challenged

Attack with "Maximize damage ratio" until all targets are destroyed. Next, change the tactics to “Disengage”.

Minimize damage to self

Actions are focused on minimal damage to oneself. The ship will conduct the entire battle, but will not go into the thick of it - try to stay at a sufficient distance from the enemy’s destructive weapons.

Maximize net damage

The determining factor is the difference between the damage inflicted by the ship and the damage inflicted on the ship.

Maximize damage ratio

Move to where the ratio of damage dealt to damage dealt is maximum.

Maximize damage

The ship moves to the point where it can inflict maximum damage on the enemy, despite the possible damage it may inflict on it.

The tactics rule is calculated every time you try to move 1 cell. This does not take into account:

1. Long-term perspective (possible movement of 2 or more cells).

2. Initiative for weapons of ships (not taking into account the fact that as a result of rapprochement, the ship will simply be destroyed first).

3. Possible movements of enemy ships (that they will find the target faster as a result of the maneuver chosen by the ship).

Moreover, if the choice among two cells is not determined, then a random one of these cells is selected.

Attack Who

At this point you can determine who the ships will attack. A specific race can be selected, or one of Nobody (do not touch anyone), Enemies (those races that are marked as “Enemy” in “Player Relations”), Neutrals & Enemies (those races that are marked as “Enemy” or “Neutral”), Everyone (everyone, including allies, but not your own).

Dump Cargo

This item can either be selected or cleared. In the first case, if a ship has cargo, and a battle occurs, then it drops the cargo into outer space or onto a planet. If these are minerals, then they will be located on the planet or in the form of Salvage in outer space. If these are colonists, then they will be doomed to death.
