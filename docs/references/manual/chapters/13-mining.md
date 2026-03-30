# 13. Mining

Most of a planet's minerals lie under the surface, unavailable for use until your colonists mine them. You can build mines on your own worlds, or use robot miners to mine uninhabited worlds.

The mineral content and concentrations for a planet are shown in the Selection Summary pane and the Minerals on Hand tile. The number of mines that have been built and can be operated appears in the Minerals on Hand tile.

## Mining Colonized Worlds

To build a mine, add it to the production queue. You can do this manually or by using the auto-build feature of the Production dialog. These mines will be built, and the minerals within will be mined and made available immediately to the locals.

To build mines:

1. Shift-click in the Scanner on the planet where you will build mines.
2. In the Production tile, click on `Change`.
3. In the Production dialog, add either `Mine` or `Mines (Auto-build)`.

To determine how much more of a mineral a new mine will produce:

1. Use the `View (Race...)` menu item, then turn to page 5 of the dialog and see how efficient your race is at building and using mines and factories. Cancel when you've finished.
2. Look at the mineral concentration information in the Selection Summary pane and the Minerals on Hand tile. Click on the mineral name or value in either location to display information on the density of each mineral under the surface.
3. Calculate productivity using this formula:

```text
potential productivity x mineral concentration = actual productivity
```

For example, you learn from the View Race dialog that 10 mines produce up to 10 kT per year, and from the Mineral Content graph in the Selection Summary that Germanium concentration is 50. This means 100 mines will produce 50 kT of Germanium in the next year. In this case, you would have to add two mines for every additional kT of Germanium you want each year.

Alternate Reality races live on starbases and can only perform a small amount of innate mining, so they always remote mine their own worlds.

## Calculating the Rate of Decrease in Mineral Concentration

The decrease in mineral concentration is related solely to the number of mines operating on a planet and the number of years the mines have been in operation. For two players with the same number of mines operating over the same number of years, the decrease in concentration will be the same for each.

Think about it in terms of mine-years: one mine-year means the operation of one mine on a planet in a year. If you are operating 50 mines per year on a planet, that equates to 50 mine-years.

To calculate approximately how many mine-years must pass to reduce a mineral's concentration by one, divide `12,500` by the current mineral concentration.

## Mineral Concentration and Mining Efficiency

The rate at which mineral concentration is reduced is not related to how efficient a player is at mining. When the concentration reaches 1 both on your planet and an opponent's planet, the player who has more mines but is less efficient at mining can extract as many kTs as a very efficient player operating fewer mines.

## Remote Mining

Remote mining is the use of robot miners to remove minerals from uninhabited planets for transfer to your needy, inhabited worlds. You can only perform remote mining on uninhabited worlds, using mining ships that carry robot mining modules.

You need to research the technology to create both the hulls and the modules, then design the ships using a miner hull. Place mining modules in the Mining slots when you design the hull. When you're ready to mine, add mining ships to your production queue.

Remote mining fleets actively engaged in mining report annually on the planet's environment and mineral situation. These ships do not need scanners, unless you want them to be able to detect enemy fleets as well.

Use the Technology Browser to learn the research and production requirements for remote miners:

- Look in the `Hulls` category for the miner hulls.
- Look in the `Mining Robots` category for the modules.

To learn how many colonists you need to operate a mine and how efficient the mine is at extraction, choose the `View (Race)` menu item, and turn to page 5 of the View Race dialog.

Alternate Reality races mine their own planets using remote mining technology. Read more about the Alternators in chapter 22.

### Creating a Robot Mining Fleet

A robot mining ship can't carry much fuel, which means it won't go far by itself unless it's outfitted with a ramscoop engine.

To assemble and launch a robot mining fleet:

1. If your mining ships don't have ramscoop engines, merge them into a fleet with at least one freighter. The freighter typically will be able to carry enough fuel for the fleet to reach its destination.
2. Assign the planet to be mined as the waypoint, with orders to carry out remote mining.
3. When the fleet reaches the planet to be mined, split the miners and freighters back into separate fleets.
4. Select the freighter fleet and assign a circuitous route with waypoints at the planet or planets to receive the minerals, ending with the mining fleet as the last waypoint.
5. At the mining fleet waypoint, assign a transport order that causes the minerals to be loaded from the miner to the freighter in the most optimum way possible.

When you set the mining fleet as the waypoint instead of the planet the mining fleet is orbiting, the freighter will automatically follow the mining fleet wherever you send it.

### Joint Ventures in Remote Mining

You can join with other players to remote mine a planet, each player using their own remote mining fleet and freighters or, since minerals can be transferred between different players' fleets and planets, one player may mine then manually transfer the minerals to the other player's holds for transport to the agreed ports of call.

Any Super Stealth race can automate transferring cargo from another player's mining fleet as a waypoint task. If the other player agrees, it's diplomacy; otherwise, it's piracy.
