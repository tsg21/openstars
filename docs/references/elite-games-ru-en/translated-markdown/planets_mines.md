# Stars! Documentation - Mines

Source URL: https://www.elite-games.ru/stars/doc/planets_mines.shtml

Original title: Stars! Документация - Шахты

Note: Automatically translated from Russian. Review against the source HTML before relying on subtle rules wording.

[Image:] Stars! Documentation - Mines

Mines and remote digging

Mines are one of the types of planetary buildings and are intended for the extraction of minerals on the planet where they are installed. These are stationary buildings, that is, they cannot be picked up and taken to another planet.

Construction of mines

Mines are only built by non-AR races. For AR races, the orbital station automatically digs into a certain mine capacity, depending on the number of population.

To build mines, the colony needs to spend a certain amount of resources. If the mine is built this year, then next year it can be put into operation.

If colonists leave the planet, the mines remain intact.

It is impossible to build more mines than you can theoretically control given the current climate of the planet. If for some reason the number of mines exceeds this limit (capture of an alien planet, climate change), then the mines will not disappear anywhere, there will simply be more of them than the limit.

Extraction using mines

The mine digs automatically if there are enough colonists to control it.

In one year, the mine excavates each of the minerals depending on its concentration. If there are 100 mines on the planet, their efficiency is 10 kt per 10 mines, and the concentration of minerals is X/Y/Z, then X,Y,Z kt of each mineral will be dug, respectively.

The minerals dug up by the mine this year can immediately be used to build ships or planetary structures on that planet.

The amount of minerals mined each year is not rounded up to 1 kt. That is, if there is 1 mine on the planet with an efficiency of 10 kt per 10 mines, the mineral concentration is 1, then in 100 years 1 kt of mineral will be excavated.

Mining with robots

You can mine minerals on uninhabited planets using robots. These are large, heavy ships equipped with devices for digging for minerals. Their use is effective if it is necessary to mine in conditions unsuitable for life.

Digging with robots can only be done on uninhabited planets. For this process, the ship must be given the “Remote Mining” order.

There are different types of robots, but each of them, from a digging point of view, is characterized by a productivity in kt/year (kt per year). This is the equivalent of mines - that is, the robot works the same as a mine, the only difference being that the mine efficiency parameter does not apply to it - regardless of it, the robot digs 10 kt per 10 equivalent mines.

When groups of robots united in fleets are used in the extraction of minerals, there is a limit to the digging power in the squadron - 4000 mines. This means that if a fleet has a combined number of robots of more than 4,000 mines, then they will dig with a power equal to 4,000. To eliminate the problem, it is necessary to divide the fleet into squadrons, each of which should not have more than 4,000 mines.

Robots used by AR dig at the arrival point during gateing if they are given the “Remote Mining” order at point wp1.

Drop in mineral concentration

Over time, if minerals are mined on the planet, the concentration of minerals decreases. The drop in concentration depends on the number of mines completed on the planet (both by robots and by mines).

The difference in planetary reserves between concentrations by 1 point is calculated using the formula:

12500/N

where N is the concentration of minerals on the planet.

This means that if for a planet with a concentration of 100, you dig 125 mines (dig 125 kt with standard mine efficiency), then the concentration will drop by 1 point.

Accordingly, mineral concentrations fall more slowly over time, and more minerals are mined between concentration levels.

The concentration below 1 never decreases.

For AR races on the home world, the concentration visually drops below 30, but the effectiveness is equal to the value at a concentration of 30.

For non-AR races, the minimum concentration is taken to be 30 if the planet is inhabited and mining is carried out by mines. If such a planet is liberated and dug by robots, then the concentration will lose the HW property.
