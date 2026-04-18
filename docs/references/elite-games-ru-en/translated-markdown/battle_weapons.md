# Stars! Documentation - Using Weapons

Source URL: https://www.elite-games.ru/stars/doc/battle_weapons.shtml

Original title: Stars! Документация - Использование оружия

Note: Automatically translated from Russian. Review against the source HTML before relying on subtle rules wording.

[Image:] Stars! Documentation - Using Weapons

Use of weapons in battle

All means of destruction are activated at the end of the round, after moving.

Initiative and firing order

The firing order is determined based on the ship's initiative and the weapon used. In general, each ship has a certain base initiative (depending on the type of hull), weapons have initiative, and the ship may also have devices that increase initiative - only computers can do this.

The three numbers described are simply summed up - the initiative of the weapon is the sum of the initiative of the corps, the initiative of the weapon itself and the sum of the initiatives of all installed computers. As a result, we get a value that should not exceed 63, that is, if initiative is greater than 63, then it is considered equal to 63.

As a result, the shot initiative for each ship component has a value from 0 to 63.

The firing order goes from higher initiatives to lower ones, regardless of weapon type. The greater the initiative, the sooner the weapon fires. The weapon with lower initiative will fire (if not destroyed) - later, but in this round. Moreover, each weapon fires only once in a round.

If the initiative is equal, then the weapon with the smaller damage radius fires first. If the damage radius is the same, then the order is determined randomly. In this case, shooting is calculated by groups, that is, all weapons with the same initiative from one group shoot atomically.

Damage range

The damage range depends entirely on the type of weapon for which the maximum firing range is determined (the Range parameter). If a weapon is installed on an orbital station, the maximum firing range increases by 1.

Dependence on distance

The amount of damage for torpedoes and missiles does not depend on the firing range.

For beam weapons, the amount of damage decreases as the distance to the target increases. This reduction occurs up to 90% at the longest distance and follows a linear relationship. That is, if a weapon has a power of 100 and a distance of 2 cells, then when shooting at 2 cells there will be 90 damage, at 1 cell - 95, in the same cell - 100.

For orbital stations the same calculation applies, only their maximum is not 10% attenuation, but more (about 11-12%) and this is performed only for Range+1, for a shorter distance the above calculation.

Atomicity of shots

Shots are fired for the Stars! have atomicity. This means that they are produced not one weapon per ship slot, but in certain groups, and each group has its own separate calculation.

For beam weapons, the crew group is a group of ships. That is, all weapons in the group that have the same initiative and type fire at all possible opponents at once and no longer participate in the round. For beam weapons, grouping only affects the order of shots with the same initiative.

For missiles and torpedoes the situation of atomicity is different. The visible salvo of torpedoes and missiles is shown as a beam weapon - a single atomic operation, even if the salvo is fired at multiple groups of ships. But from the point of view of calculations, missiles and torpedoes are counted one by one. That is, each slot is fired separately, possible damage is calculated for it/ships are destroyed, and only then the next slot is fired. Thus, 2+2 slots of torpedoes or missiles are less effective than one slot of 4.

Causing damage

Any weapon first tries to damage more preferable targets based on a given tactical scheme. Next, the weapon selects a target based on “taste” (Stars! has an internal cunning algorithm for determining “taste”, but in general, the more dangerous the target (has greater power capabilities and is more easily destroyed), the more “tasty” it is) and tries to point the weapon at them.

Gatling systems fire indiscriminately, dealing one level of damage (damage reduced only by distance) to all ships within the radius. Other means of destruction first try to destroy (or remove shields for sapper-class weapons) ships in accordance with the tactical scheme, and then there is a selection based on tastyness.

If some ships are not specified in the tactical scheme, then they will not be attacked at all (for example, if Starbase and Armed Ships are specified, transports will not be destroyed).

Beam weapons are guaranteed to cause specified damage, which is determined by the power of the weapon, the distance to the target, and the presence of deflectors at the receiver.

Missiles and torpedoes have a hit probability property. If a torpedo hits a target, it deals damage equal to its nominal value. If the enemy has a shield, then half of the damage goes to the shield, and the other half to the armor. If there is no shield, then everything goes into armor. Missiles have the same properties, only when they hit a ship without shields, they cause double damage.

If a torpedo or missile misses the target, it either does no damage (if there are no shields), or 1/8 of its value damages the shield.

The probability of a torpedo or missile hitting a target is determined based on the type of torpedo or missile, the presence of guidance devices, and the presence of deflection devices at the target being attacked.

You can read more about the calculation formulas in the Stars help in the section “The Guts of Combat” → “Weapons and Battle Devices”.
