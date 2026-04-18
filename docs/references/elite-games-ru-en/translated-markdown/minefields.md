# Stars! Documentation - Minefields

Source URL: https://www.elite-games.ru/stars/doc/minefields.shtml

Original title: Stars! Документация - Минные поля

Note: Automatically translated from Russian. Review against the source HTML before relying on subtle rules wording.

[Image:] Stars! Documentation - Minefields

Minefields

Minefields are separate objects in the game. At any given time, a minefield has its own center (a point with exact coordinates), a radius (depending on the number of mines), belongs to one of the players and belongs to one of the types of minefields (standard, heavy mines and booby traps).

Fields of various types and accessories are shown here.

First of all, they differ in color. Red ones are enemy minefields, yellow ones are allied minefields, blue ones are your own minefields.

Fields marked in purple are set to detonation mode. That is, next year they will detonate themselves (this is possible if an order to detonate is given, and only SD races with their standard type fields can do this). Other races see fields that have been undermined in the current year as purple.

When displayed, fields of different types are drawn in different patterns - the standard ones are a diamond grid (around the Quick Lick planet), heavy mines are inscribed in arc squares (a large field around Penzance), anti-velocity mines are a dotted grid (a small field around Penzance).

If the center of the field is on a planet, it is not displayed. If outside the planet, then this is a filled-in small square of the corresponding race color (field next to Turing's World).

Each minefield has a center and a radius and occupies a circular area.

Characteristics of various types of mines

Min type

Image

Safe speed*

Chance of detonation per 1 ly field

Minimal damage (standard/for frame engines)

Damage per engine

Description

Standard

4
0.3%
500/600
100/125
Standard minefields can be built by all races except WM. SD can forcefully detonate its own minefields, and in this case, all ships that are in this minefield or come into contact with it receive additional damage. Installed by ships with standard mine installation devices.

Heavy

6
1%
2000/2500
500/600
Can only be built by SD races. They are characterized by increased damage power and ease of installation. Installed by ships equipped with heavy mine laying devices.

Booby traps

5
3.5%
0/0
0/0
Can only be built by SD or IS races. These mines do no damage, but are more effective at stopping fleet movements. Such minefields are more difficult to clear, more expensive economically (they require I and are more difficult to fill space with). Installed by ships equipped with booby trap installation devices.

* - for SD races the safe speed is 2 more, for SS races - 1 more.

Setting min

Installation is carried out using ships that have devices for installing mines. If such a ship is given an order to lay a minefield, and the ship is stationary, it will lay the number of mines at a given point, specified by the on-board devices. If there are several types of mines on board, then each type will be installed separately.

When stationary, minelayer ships place double the number of mines, and when moving, if an order is given to lay a minefield at the arrival point (wp1), but there is no order for wp0, then the standard number of mines are placed at the arrival point.

Laying mines means that new mines will appear in space at the ship's position. If at that point at the time of installation there is no player minefield of the corresponding type, then a new field will be created. If the field is already present, then the number of mines in it will be increased by the specified number, while the center of the minefield will shift towards the installation point in proportion to the number of mines placed.

Detection of minefields

Minefields are 82% hidden from regular scanners and 0% hidden from penetration scanners.

Detection occurs if the center of the minefield falls within the radius of the penetrating scanner or if the fleet is on the edge of the field or inside it. And also if the field has already been detected earlier, then scanning the center of the field with any scanner is sufficient.

Detonation of minefields

The SD race can detonate their standard minefields. In this case, all ships, except minelayers (including our own), receive damage from the explosion. Those fleets that are inside the minefield are exposed to the explosion - those outside or at the very edge are not damaged.

Minelayers are not immune to the detonation of fields belonging to races with a lower number.

When minefields are detonated, the number of mines is further reduced by 25%.

Damage from minefields

Damage from minefields is calculated based on the type of mine.

If there was a detonation of a minefield or hit the field at a speed higher than safe, then the fleet receives damage either minimally or based on the number of engines present (the maximum of the damage is selected). Next, this number of damage is applied evenly to each ship in the squadron. If the ship has shields, then they take half the damage (if there are enough of them to do this, otherwise the rest goes to the armor). Accordingly, those ships that could not withstand the blow (the armor value became negative) are destroyed.

The maximum that threatens the fleet when moving in minefields is to hit one of the types of mines lying along the course and suffer once from the detonation of the fields of each of the races.

As a result of receiving damage, players receive a message indicating the damage inflicted. This number is difficult to determine the meaning of the value, but it very closely describes how much total damage was inflicted on the ships (both to shields and to armor), not including any damage that could be inflicted in excess of what was necessary (more than the armor reserve for ships destroyed by the explosion).

If there are less than 5 ships in a group, damage is calculated as follows. The total number of damage is determined based on the ship that has the largest number of engines in the hull. That is, the maximum number of engines is multiplied by the minimum damage per squadron. Next, these damages are distributed to ships. All damage is divided into 5 equal portions. Each ship gets one portion. If there are less than 5 ships in the squadron, then all remaining portions are given to the ship that has a lower design number.

The amount of damage does not depend on the speed at which the ship was moving in the minefield.

Movement in a minefield

If the fleet moves in a minefield at a speed equal to or less than safe, then the fleet cannot run into mines as a result of its movement. If the speed exceeds the safe one by one, then the chance of being blown up is equal to that indicated in the table for each ly flying across the field. If the speed exceeds by more than 1, then the chance of getting blown up increases with each unit of speeding by a specified percentage.

If an explosion occurs, the fleet stops at the point of explosion. For heavy and standard mines, damage occurs; booby traps only stop ships.

Flight through your own fields and the fields of your allies occurs unhindered.

Clearing minefields

Ships with beam weapons on board, as well as orbital stations with beam weapons, clear enemy minefields automatically if they are inside them. For each of them, a parameter is shown, how many mines of a standard type they can clear based on on-board weapons (boom traps are cleared 3 times slower than this value). These values ​​are summarized for the entire fleet.

As a result of clearing, the field decreases in radius to a value determined by the position of the fleet in the minefield (it ends up at the edge of the field) or simply decreases in radius according to how many mines the fleet cleared.

Natural reduction of the minefield

The number of mines in a minefield decreases due to natural reasons every year. The reduction rate is the % by which the number of mines in a minefield is reduced each year. % depends on the number of planets covered by the minefield and whether the field belongs to an SD or non-SD race. For SD races, the minefield is reduced by 1% plus 1% for each planet present in the field. For other races 2% plus 4% for each planet.

The rate of reduction of mines cannot be more than 50% of mines per year.

Mines as scanners

For SD races, their minefields are also scanners of the appropriate radius, but not penetrating.

Setting limits min

In Stars! it is possible to create minefields of up to 1,000,000 units with a installation/reduction rate of 32,000 units per year.

There is a limit on the number of minefields per player - 256 pieces, while when approaching 240+, glitches begin - some fields are not placed.

Bugs while moving in a minefield

Using the bugs immunity from minefields when flying North-South and immunity from high-speed minefields when flying West-East is cheating.
