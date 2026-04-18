# Stars! Races - Hab

Source URL: https://www.elite-games.ru/stars/doc/race/hab.shtml

Original title: Stars! Расы - Hab

Note: Automatically translated from Russian. Review against the source HTML before relying on subtle rules wording.

[Image:] Stars! Races - Hab

Living conditions of the race - Habitation (Hab)

The ability to live on various planets is selected at the 4th step of creating a race.

Each planet has its own gravity (Grav), temperature (Temp) and radiation (Rad) values. If your race fits into the parameters of the planet, then it reproduces successfully and can live comfortably on this planet. If it does not fit into the parameters, then the colony will drag out a miserable existence.

Planets as habitats

Planets as habitats are characterized in terms of gravity (Grav), temperature (Temp) and radiation (Rad). Each of these parameters has a native and current value. At the beginning of the game, all planets have the same native and current values. During the game, the current and in some cases the original value may change.

When you look at the planet, you see this picture:

In this case, it is the weather on the planet “Charity”. The blue-red-green stripes show the life ranges of the race. The current parameters are shown against their background. The cross indicates the original meaning, and the diamond the current meaning. The horizontal bar shows how the value can be changed using terraforming, with the horizontal line going in the direction favorable to your race.

On the planet in question, the gravity level is 0.69 g and can be changed by 1 point upward. To do this, you need to terraform the planet and spend the appropriate amount of resources. Now the temperature on Charity is 40 Celsius and it coincides with the native value. The radiation was beyond the permissible limit and after terraforming the planet became habitable.

Habitat for the race

The "Value" indicates how suitable the planet is for settlement. In this case it is 41%, that is, 41% of the maximum for the race. 43% - how much the planet can be terraformed with the current development of technology.

From the point of view of habitat, each of the planets differs from the other only in the parameters described above. The current “Value” determines the rate of growth/extinction of colonists and the maximum permissible number of colonists living on the planet. It can take values ​​from -45% to 100%.

100% - the planet is completely suitable for your race. This is possible if the current values ​​for Grav, Temp and Rad are exactly in the middle of the residence range, or any value if the race is immune.

If a parameter goes outside the range, then “Value” becomes negative and decreases by 1% for each deletion point, but not more than 15% for one parameter.

Maximum allowed number of colonists on the planet

Depending on the current conditions on the planet, the maximum permissible number of colonists that can be on this planet also changes. This value depends on the race settings and the current “Value”.

The algorithm for calculating this parameter is as follows:

We determine the maximum permissible value of the number of colonists in the case of ideal conditions. If HE, then it is 500 thousand colonists, if JOAT, then 1200 thousand colonists, if another PRT, then 1000 thousand colonists. Next, this number must be multiplied by 1.1 if OBRM is selected. As a result, we get the table:

Maximum number of colonists on the planet, thousand pieces

PRT

Without OBRM

OBRM selected

HE | 500 | 550

JOAT | 1200 | 1320

Other | 1000 | 1100

If the planet is uninhabitable (red or yellow) or the planet is green, but the “Value” is less than 5%, then the maximum number of colonists will be 5% of the value calculated above.

The maximum number of colonists on the planet is an important parameter. If the planet is populated to the level specified by the parameter, then all the colonists work at full capacity - they give exactly as many resources as were specified in the 5th step of creating a race. At the same time, Stars! do not allow the construction of more mines and factories than the maximum possible for control.

The rate of reproduction of colonists on the planet

Colonists reproduce only if the planet is green. The highest relative reproduction rate is achieved when "Value" is 100% and the population size is small enough (~25% of the maximum number). In this case, the reproduction rate is exactly the value that was selected at the 4th step of creating a race (the “Growth Rate” value).

As the population increases, the growth rate steadily decreases. The maximum level of growth is maintained if the population is in the range of 25% -40%. This is the most favorable level for breeding and transporting colonists throughout the empire.

As the number of colonists approaches the maximum level, the reproduction rate decreases to 0, and the number of colonists never reaches 100%.

There are the following heuristic formulas for calculating the reproduction rate:

1

If there are less than 25% of colonists, then the increase will be:

Pop * Growth * Hab_value

If the colonists are more than 25% of the capacity, then the above calculated value must be multiplied by the following:

16/9 * (1-Capacity)^2

where Pop is the population of the planet;

Growth - percentage growth of the race;

Hab_value - the “Value” value described above;

Capacity - the capacity of the planet, that is, the maximum number of colonists for living.

This formula was published by Jason Cawley, who owes it to Bill Butler.

2

If the colonists are more than 25% of the capacity, then the formula is as follows:

Here:

Pmax - the maximum number of colonists on the planet.

P% – planetary value “Value”.

R%—percentage growth of a race.

P1 is the current population on the planet.
