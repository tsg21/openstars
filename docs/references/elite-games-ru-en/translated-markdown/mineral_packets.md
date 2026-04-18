# Stars! Documentation - Mineral packages

Source URL: https://www.elite-games.ru/stars/doc/mineral_packets.shtml

Original title: Stars! Документация - Минеральные пакеты

Note: Automatically translated from Russian. Review against the source HTML before relying on subtle rules wording.

[Image:] Stars! Documentation - Mineral packages

Mineral packs

Mineral packets are independent objects in the game.

Example package:

The package is shown on the galaxy map as a green (friend) or red (alien) square.

This image shows 2 packages. Red is selected for consideration and the Stars interface! shows his direction of movement with risks at the flight points (points where the package is expected to be located next year if he is alive).

On the planet Winkle there is an orbital station with a packet engine and its sight is aimed in the direction of the southeast, but not at the planet Mundus. The created green package is also a penetrating scanner due to the fact that it was released by the PP race.

When selecting a package, you can see the following information:

The picture shows that this is a mineral pack. The image below shows which race the package belongs to. Its characteristics are also shown: speed, destination, mass and mineral composition. In addition to the above, any mineral package has such a characteristic as the rate of dispersion, which shows whether the package crumbles or not over time and, if so, at what speed.

Creating a package

They can be created by an orbital station that has an orbital device such as a packet driver. To do this, the colony needs to spend the appropriate amount of resources and minerals.

Costs of minerals and resources for different races:

Package type

PP bag

not PP bag

Mixed | 25 kt of each mineral, cost 5 resources | 44 kt of each mineral, cost 10 resources

I/B/G | 70 kt of selected mineral, cost 5 resources | 110 kt of selected mineral, cost 10 resources

As can be seen from the table, the cost of creating packages for the PP race is lower, and they have more ability to set a more accurate package mass.

At the same time, creating Mixed packages is cheaper than choosing a specific mineral.

When a packet is created, it can only be sent from a source planet (with a packet engine) to another planet (receiver planet). Moreover, in one year only one package can be released at one speed, that is, all packages produced by the colony in a year are issued in one package and fly into space.

All mineral packs can be launched at speeds from 5 to 16, flying from 25 to 256 ly annually. The speed of the launched package is limited by the type of package engines installed on the orbital station. This setting has a value from 5 to 13. If the orbital station has an N-class packet engine, this means that it is capable of launching packets at speeds from 5 to N+3.

Packages spilling

If the installation supports a nominal start at a speed of N, this means that the packet engine, when launching packets at speeds from 5 to N, will create a packet that will not crumble over time.

If 2 class N engines are installed at a starbase, then the station is the owner of a class N+ engine. This means that you can also run packets at speeds from 5 to N+3, but the packet will not crumble at speed N+1 and will crumble less at speeds N+2 and N+3. In this case, protecting the planet using an N+ engine will be equivalent to an N+1 class engine.

The presence of two engines of different classes does not give the '+' effect.

For each year of flight, the package crumbles into a certain number of kt of minerals, calculated as a percentage of the total mass of the package, and at the same time it crumbles into at least 10 kt of each mineral if scattering occurs.

Engine type

Packet speed

% spillage for PP

%-scattering for non-PP

N
N
0
0

N
N+1
5
10

N
N+2
12.5
25

N
N+3
25
50

N+
N
0
0

N+
N+1
0
0

N+
N+2
5
10

N+
N+3
12.5
25

If the package reaches the planet halfway (for example, the package flies 100 ly per year at 10th speed, and there are 50 ly left to the planet), then it will scatter in proportion to the distance (by 12.5% if the package scatters at a speed of 25% per year for our case).

Flight of packages

The movement of packets occurs strictly in a straight line from the source planet to the receiver planet.

In the first year, the packet flies exactly half the distance it should fly according to speed.

Any package can be intercepted by a transport ship of any race. This means that if a vehicle happens to be near the package, it can take minerals from the package in any quantity.

You will not be able to load more than the nominal value into the package (only exchange minerals).

If the mass of the package is reset to zero (due to scattering or interception), then the package disappears and will not be there next year.

PP races see all packages in the galaxy. Other races only see packets that are detected by their (standard) scanners.

Bags as a means of transporting minerals

It is used quite rarely, and mainly in the middle and final stages of the game.

This is due to the fact that at the beginning of the game, packets are slow and quite expensive (require resources). As development progresses, new speeds are mastered and delivery is possible faster than transports (up to 14th speed, 196 ly per year, which is ~2 times higher than the speed of transport, and in the case of transmission in 2 years, 3 times higher).

One of the features of the transfer of minerals is that the package is accepted before production (if it is not sent this year), and therefore the receiving party can count on the minerals arriving this year and use them in production.

Packets as a reconnaissance tool

The PP race can effectively use packages as scanners of other planets and outer space. PP races have a penetrating scanner built into their packages with a range equivalent to the distance that the package flies in 1 year (if the package moves at 9th speed, then it has a scanner of 81 ly).

In addition, PP packages have the following feature: if a package hits an enemy planet, and that planet has an orbital station with its own package engine, then in this case the design of the orbital station becomes known to the one who launched the package.

Packages as a means of terraforming

If a PP package reaches the surface of a planet, it has a chance to terraform it (detailed description).

In general, this pleasure is quite expensive in terms of minerals, so it is used in exceptional cases.

Packages as weapons

This is the most effective and player-favorite use of packages.

A decent mass rushing through space at great speed is capable of producing armageddon, from which there is simply no protection. The only thing that can stop an attacker is a lack of minerals or their inappropriate expenditure on such an event.

The result of a package impact depends on a number of parameters: the speed and mass of the package, the presence and class of the package engine of the receiving planet, as well as the quantity and quality of protective structures and the number of colonists on the planet.

First of all, the package, flying from the launch point to the receiver planet, loses part of its mass and only that part of the mass that remains is taken into account.

Next comes the reception of the packet using a packet driver located on the receiving planet. This can be shock absorption or full reception. If the packet flies at speed M, and the packet engine has class N, then in the case where M<=N, the packet is completely accepted by the packet driver and all minerals are absorbed by the colonists. If M>N or the package driver is missing, then the package will inevitably cause damage.

In the case of M>N, the packet driver absorbs the shock: part of the packet (N/M)^2 is accepted - all minerals from this part of the packet are absorbed and placed on the surface of the planet, only 1/3 of the rest of the (N/M)^2 is absorbed, the rest is lost. Part 1-(N/M)^2 continues to participate in the calculation.

Next, they try to protect the part of the package remaining after depreciation - they have % protection (standard) and a part of the package equal to this percentage is accepted by them. The missing part directly causes damage - it kills colonists and destroys defenses. The scale of destruction depends on the speed of the package (directly proportional) and the passed mass. When calculating, the package either destroys a certain minimum number of colonists, or a percentage of the colonists - the greater of the possible ones is considered. If there are a small number of colonists on the planet, then it can be destroyed by a smaller package. If the number is large, then there is such a mass of the package that will completely destroy all the colonists, regardless of their number.

If there is planet A shooting at planet B, and planet B shooting at A, and when firing in batches both planets take out colonists at once, then both planets will take out each other in such a salvo.

If there is planet A shooting at planet B. In the same year, planet C shoots at planet A, but at a safe speed. In this case, A cannot count on an increase in minerals from C. But it can count on incoming minerals that are now flying to A and will arrive next year.

The exact calculation of the use of packages as bombing means is described in the help to Stars! "Mineral Packet Bombardment" - "The Guts of Mass Drivers".
