# Stars! Documentation - Moving Objects

Source URL: https://www.elite-games.ru/stars/doc/navigation.shtml

Original title: Stars! Документация - Перемещение объектов

Note: Automatically translated from Russian. Review against the source HTML before relying on subtle rules wording.

[Image:] Stars! Documentation - Moving Objects

Navigation and moving objects

All objects have integer coordinates

In Stars! any object is located at one of the points of the galaxy, represented as grid nodes. The planets are constantly at the same point with their orbital stations; ships, moving in space, move from point to point; minefields have their centers at nodal points; Mineral packets and MT, when moving, change their position from year to year along the coordinate grid nodes. Each of these objects at the moment of movement is located at one of the points, which is represented as integer coordinates horizontally and vertically. Moreover, every year the coordinate is rounded, regardless of the trajectory of movement or the order given.

Speed concept

In Stars! If all objects move, they do so at different speeds. A total of 16 speeds are possible, and if an object moves at a speed (warp) N, then it moves a distance of up to N^2 light years.

With the help of their engines, ships are capable of reaching speeds of up to 10, that is, moving a distance of up to 100 ly per year. This is the maximum speed for them; you can only move faster with the help of planetary gates. But this is not really a movement, this is a teleport - here no one sees where the teleport came from and when gating, it does not matter whether there are obstacles in the way of gating. Moving through spatial holes has similar properties.

A number of engines are not able to operate correctly at 10th speed. All engines support safe operation at speeds up to 9th, but a few support safe 10th speed. If a ship has engines that do not support 10th speed, and at the same time it is given an order to move at 10th speed, then the ship with a 10% probability will be annihilated and disappear. This 10% calculation is calculated for each ship in the squadron.

If the race has CE, then when using the engine at speeds above 6th they have a 10% chance of not starting. This means that there is a 10% chance that ships will not move. This probability is already calculated for the entire fleet.

If the distance between two points can be flown at a speed of N per year, then the same distance can be flown at a higher speed (N+1 for example if N<10). But at the same time there will be higher fuel consumption, a greater likelihood of hitting mines, ... - that is, all the properties of moving at higher speeds are inherent, but when moving over a shorter distance. Sometimes this can be useful - for example, for greater fuel intake using ramscoups, or for clearing mines.

If the distance between points is less than N^2+1, then it can be covered at speed N. For example, if the distance between points is 9.99 ly, then it can be covered at 3rd speed.

Above speed 10, MT and mineral packs can move. MT up to 13th speed (up to 169 ly per year), packages up to 16th speed (256 ly per year).

Start and end point of movement

When moving, the starting point (wp0) and ending point (wp1) are indicated. In each of them it is possible to set an order. For example, you can give an order to transport to load cargo before moving, and unload it at the final point.

Each point has its own set of possible orders, for example, for point wp1 it is impossible to make “Scrap Fleet”. There are also orders that are executed only if the object is stationary (for example, “Lay Minefield” if the hull is not a minelayer).

If the object does not have an order to move, then the order wp0 is combined with wp1 and executed at the moment wp0.

Fuel consumption

When ships move, fuel is naturally consumed. The higher the speed, the higher the specific consumption per 1 ly. Specific consumption is calculated based on the schedule of the engine used.

Thus, if the engine has a consumption of 100% at the 5th speed, and 300% at the 6th speed, then covering any distance at the 5th speed will cost 3 times more economically than at the 6th.

The greater the weight of the ship, the more fuel is needed to move it (directly proportional). Therefore, the delivery of cargo and the design of heavy ships leads to increased attention to fuel use.

Obtaining fuel from outer space

Conventional and trans engines produce fuel from space only at 1st speed, and receive 1 mg per year when moving.

Ramscoop class engines allow you to generate large amounts of fuel far from starbases. For them the following calculation:

For each ramscoop engine there is (max free speed) - the maximum speed at which fuel is taken. If a ship has N engines and has flown L ly, then it will receive N*L*k mg of fuel, where k is a number equal to 1 when moving at maximum free speed, 3 at maximum free speed - 1, 6 at maximum free speed - 2, 10 at all lower speeds.

Based on what has been described, for various engines the fuel production is as follows:

Engine

warp 9

warp 8

warp 7

warp 6

warp 5

warp 4

warp 3

warp 2

warp 1

Fuel Mizer | - | - | - | - | - | 16 | 27 | 24 | 10

Rad-Hydro Ram | - | - | - | 36 | 75 | 96 | 90 | 40 | 10

Sub Gal Scoop | - | - | - | - | 25 | 48 | 54 | 40 | 10

Trans-Gal Scoop | - | - | - | 36 | 75 | 96 | 90 | 40 | 10

Trans Gal Super Scoop | - | - | 49 | 108 | 150 | 160 | 90 | 40 | 10

Trans Gal Mizer Scoop | - | 64 | 147 | 216 | 250 | 160 | 90 | 40 | 10

Galaxy Scoop | 81 | 192 | 294 | 360 | 250 | 160 | 90 | 40 | 10

Enigma Pulsar | - | - | - | - | 25 | 48 | 54 | 40 | 10

Orders to the fleets

The fleet can receive an order at each of the movement points. That is, if a certain route is given to the fleet, then at each of the points of change in the route (including the initial and last) a special order can be given.

The following orders are available:

(no task here)

No order. The fleet will not do any specific actions.

Transport

An order to perform an operation with cargo or fuel. That is, you can load/unload cargo or fuel. If the ship is a cargo ship (can carry at least 1kT of cargo), then orders can be given to load and unload colonists, fuel and three types of minerals. If the ship is not a cargo ship, then operations only with fuel are possible.

There are the following operations within the framework of this order:

(no action)

No actions are performed with this type of cargo.

Load All Available

Try to load as much as possible (until the ship is fully loaded or until the source is depleted).

Unload All

Unload everything. If unloading occurs, it is unloaded as much as possible to fill. That is, for example, if ship A has 100 mg of fuel, and ship B has room for 50 mg, and unloads from A to B, then 50 mg will be transferred to B and 50 will remain in tank A.

Load Excatly...

Load exactly a specific size of cargo. If the cargo does not fit, then it is loaded as much as possible. If the cargo is not available, then as much as there is is loaded. There is no wait until the specified value occurs.

Unload Excatly...

Unload exactly the specified size of cargo.

Fill up to %...

Load exactly to the specified percentage level. After attempting to load, without waiting for the % level, the fleet flies if there is a route to the next point.

Wait up to %...

Wait for the cargo to reach the specified % fill level of the hold. % is calculated based on the specific selected field. If the percentage is reached, then the order is canceled (changed to (no action)) and if there is a route, then only next year after filling the ship will fly along the route. If you specify an order at the point of arrival, and the required cargo is available, then the wait will be canceled immediately after arrival and loading.

Load dunnage/optimal

Load cargo as much as possible.

Set amount to...

Waiting for the cargo to reach the value specified in kT/mg/hundreds of colonists. You can select a value from 1 to 4000 kT/mg/hundreds of colonists, respectively. The behavior is similar to Wait for %....

Set waitpoint to... Leave a specified number of minerals at a point (from 1 to 4000). That is, if you specify 100kT, then the transport will leave 100kT, and try to pick up everything else. Action happens without expectation.

All orders of the same type are processed from top to bottom. That is, first loading/unloading fuel, then Germanium, .. and at the end the colonists.
