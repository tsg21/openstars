# Stars! Documentation - Science and Technology

Source URL: https://www.elite-games.ru/stars/doc/science.shtml

Original title: Stars! Документация - Наука и технологии

Note: Automatically translated from Russian. Review against the source HTML before relying on subtle rules wording.

[Image:] Stars! Documentation - Science and Technology

Science and technology

In Stars! There are 6 branches of technology, each of which is independent of the other: Energy, Weapons, Propulsion, Construction, Electronics, Biotechnology.

In each direction there are 26 levels (or 27, if you count 0 as a level), that is, the technology at any time can be from the 0th to the 26th level. When a race reaches a new level, technological innovations may become available to them: components for ships, types of hulls, planetary defense systems, planetary scanners, expanded capabilities for terraforming planets. In addition, there are positive effects: miniaturization of existing components (what you already know becomes cheaper), increasing the efficiency of the race (AR receives more resources with the development of the Energy direction, JoAT receives better scanners with the development of Electronics).

Getting new technologies

Receipt occurs in one of the following ways:

The expenditure of a certain amount of resources by a race.

Every year the race provides a certain non-negative number of resources for the development of technology. The calculation is based on the sum of the costs of all planets on technology.

The player sets a %, which indicates what part of the planet’s resources will definitely be spent on technology. That is, if 10% is set, then 10% will definitely go to technology, and 90% can be used in production. If the queue is empty, or not completely filled, or an element under construction requires minerals and there are none, then free resources go into the development of technology.

Gaining technology by receiving high-tech junk from other races.

If a ship was dismantled or shot down over a planet with a starbase, and it contained a component that requires higher technology to produce, then one of these technologies can be obtained (level 1 only). The event is triggered with a 50% probability.

Obtaining technologies as a result of destroying more high-tech ships.

If at least one enemy ship with more high-tech components inside it (or the hull itself) was destroyed in the battle, and the race’s ship took part in the battle and survived (not necessarily a combat one), then there is a chance of obtaining the corresponding technology (level 1). The event is triggered with a 50% probability.

Obtaining technologies as a result of capturing enemy planets.

If, as a result of landing on an enemy planet, a race occupied it, and the defeated race had some more advanced technology than the attacking one, then the attacking one has a chance to gain 1 level in the lagging technology. The event is triggered with a 50% probability.

Obtaining resources in technology through espionage.

SS races have the espionage property, which means that the race receives 50% of the total average costs of each player in each technology tree. That is, if there are N active (currently alive, including the SS race itself) players, and someone spends R resources, then espionage will give R/(2*N) resources, rounded down. Moreover, this property also works in relation to the SS race itself. In this case, espionage only counts for resources invested by races in science. Technology transfers and MT are not included in this calculation.

If someone spends R resources, but some of them go to one research field, and some to another (for example, when setting “next field”), then all espionage resources are counted as in the starting field, that is, R/(2*N) will be received in the starting field.

Receiving technologies from MT.

When meeting with MT, 1 or more levels in technology can be gained.

Obtaining resources in technologies when finding an artifact.

This is a random event during initial colonization that can bring resources to one of the technology branches.

Technology transfer

If a race has technology higher than another, then it can specifically transfer it as an ally or use it as a commodity in a trade deal.

In one year, a race can only gain 1 level from all races in the game. Regardless of how this was done - landing, dismantling the giver, destroying enemy fleets and orbital stations.

Transfer can occur in the following ways:

Exchange of technologies as a result of alternating landings on planets.

A red or low-mineral planet (generally unusable) is selected and populated with 100-200 colonists. Transports with colonists of both races are placed above it and in turn they capture this planet. As a result, level 1 transmission occurs with a 50% probability.

The main advantage of this method is that any technology can be transferred. A secondary advantage is that the technology can be acquired in the same year that another race discovers the technology. Disadvantages - any technology is transferred, but not the necessary one, planets are required, the speed of technology transfer is low, few colonists are required.

Creation, transfer and analysis of giver.

Miniature ships are created that are as cheap as possible, but contain a component with a higher technology. Then they are transferred to a planet of another race (by a gate or on their own), where there is a starbase. Scrapping occurs there, as a result the race receives technology with a 50% probability per giver.

The advantage is the focus (you can select the component and the technology being transferred accordingly) and the speed of transfer (almost 100% per year of the same level). Disadvantages - There is not always a transfer component for the technology being transferred. Plus, this method will not work if the races are at enmity or are neutral. And at the same time there is a long delay - construction, transfer and disassembly require 3 years.

Creation of givers and transfer to the enemy for destruction.

Miniature ships are created that are as cheap as possible, but contain a component with a higher technology. Then they are transferred to the point where they are shot down by ships of another race, as a result the race receives technology with a 50% probability per giver.

Another advantage is the focus (you can select the component and the technology being transferred accordingly) and the speed of transfer (almost 100% per year of the same level). Moreover, the speed is 1 year faster than in the previous method. Disadvantages - There is not always a transfer component for the technology being transferred. Plus, this method will not work if the races are in an alliance. The delay time is shorter - construction and deployment into battle are possible within 2 years.

If technology is transferred from another race, then exactly as many resources are transferred as needed to be spent on obtaining level N+1 from N. For example, a race has level 3 technology. Up to the 4th level there are 1000 resources, up to the 5th level another 2000 resources (in total up to the 5th level - 3000). If, after receiving the 3rd level, a race spent 500 resources in the branch (it has 500 left until the 4th level) and then received the 4th level as a result of technology transfer, then the race reaches the 4th level +500 resources, that is, it has 1500 resources left until the 5th level.

Miniaturization

As a result of technological developments, existing components and housings are being miniaturized. Miniaturization refers to the reduction in cost (both in resources and minerals) as a result of the level of technology exceeding the required level.

The reduction in price occurs based on the number of levels exceeded in technologies. An excess of N levels for a component/hull is considered if the current level of technology development exceeds all the required levels for building the component/hull by N levels. If the presence of any technologies is not important for a component, then miniaturization by N levels requires exceeding level 0 by N in all 6 directions.

For example:

1. To build a Battleship, level 13 in Construction is required. When a race reaches level 14 in Construction and higher, the hull is miniaturized (it is cheaper to build, when disassembled, fewer minerals will remain from it and fewer resources will be released). At level 14 there will be 1 level of miniaturization, at 15 there will be level 2, etc. up to 13 (science cannot be raised above level 26).

2. To use one Jihad missile, you need to be level 12 in Weapons and level 6 in Propulsion. Level 1 miniaturization requires level 13 in Weapons and level 7 in Propulsion. If a race is level 16 in Weapons and only level 8 in Propulsion, then the miniaturization will only count for 2 levels.

3. To build the Space Station starbase, the development of any technologies is not required. But to miniaturize one level, you need to raise all technology branches by 1. That is, if a race has E10, W16, P11, C13, E11, B4, then miniaturization will be only 4 levels. If you increase Bio level to 10, miniaturization will improve to level 10.

Level 1 of miniaturization implies a reduction in the cost in resources and minerals by 4% (5%), but with a final cost of no more than 25% (20%) - without BET (with BET). The calculation is made in relative terms for the initial cost, that is, if the 4th level of miniaturization, then the component/case will cost 84% without BET and 80% with BET of the initial cost.
