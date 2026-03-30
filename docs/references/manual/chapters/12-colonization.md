# 12. Colonization

Colonize planets that are immediately habitable for your race, or planets that currently have a negative value but can be terraformed into habitable worlds. You should colonize as many planets as possible in order to increase the rate at which you gain resources, which you need to build better technology and more fleets.

At the same time, do not pull people off your homeworld so quickly that you begin to lose significant resources. Try to find a balance between a planet's growth rate and the rate at which you send colonists off-planet.

## Choosing Planets to Colonize

Planets come in three basic flavors:

- Planets you can inhabit immediately. These have a positive value and appear green in Planet Value view in the Scanner. The better the planet, the higher the value, the larger the green dot, and the faster your colony will grow.
- Planets that have a negative value but can be terraformed by you. These planets appear yellow in Planet Value view. The larger the yellow dot, the better the planet will be after you finish terraforming.
- Planets that will just plain kill you. These have a negative value and appear red in Planet Value view. The bigger the red dot, the more deadly the planet. You do not currently have the ability to terraform these planets, although increasing your terraforming technology may change a red dot to yellow.

Two items in the Selection Summary pane can also help you decide which planets are good candidates for colonization:

- `Habitability Value`: Two numbers appear here if you have the technology to terraform the planet. The first number is the planet's current value. The second number, shown in parentheses, is the planet's potential value if terraformed to the extent your current technology allows. If the second number is negative, the planet will still kill you.
- `Environment Graph`: Click each of the three variables shown in the graph. A pop-up tells you the potential increase in planet value if you modify that variable to the limit allowed by your current technology.

If you do not see the value in parentheses, either you cannot terraform this planet or the Summary pane has been sized too small for the number to display.

Races based on the `Claim Adjuster` trait terraform automatically as they land.

## Colonizing an Uninhabited Planet

To colonize an uninhabited planet, you need a fleet containing at least one ship with a colonization module as part of the hull design. Most races start with at least one colonizer. If you do not have any colony ships, add one or more to your production queue.

To colonize an uninhabited planet:

1. Select the colony fleet into the Command pane. You can do this by double-clicking on its location in the Scanner, or, if more than one object is at the location, right-click and select the fleet from the list.
2. In the Fuel and Cargo tile, click in the Cargo gauge and transfer colonists from the planet into the fleet's holds.
3. `Shift`-click in the Scanner on the destination planet.
4. In the Waypoint Task tile, select `Colonize` as the waypoint task.

The colonists dismantle the colony ship when they land, using any leftover cargo and some of the minerals used in the ship's construction to help start the colony.

It is usually a good idea to minimize the number of ships in the colonization fleet. Once the colony is established you can transport additional colonists using a freighter. In that case, the colonists are unloaded and the freighter proceeds to its next waypoint.

## Finding a Fleet with a Colonization Module

The colonization module is pictured in the margin of the original manual. For a better picture, press `F2` to open the Technology Browser, then select the `Mechanical` category.

To learn which of your fleets has a colonization module:

1. Double-click on locations in the Scanner where your ships are present, starting logically with the location from which you plan to launch the colonizing force. If a planet is also present, right-click on the location and select a ship in the pop-up list.
2. Right-click in the Fleet Composition tile to display the hull schematic. When a picture of the colonization module appears, you know you have found your fleet.

Click `Next` in the Fleet tile to display additional fleets.

## Shuttling Colonists with Freighters

You can use freighters to shuttle colonists to your established colonies. If you are heading for a planet owned by an opponent, expect a fight and carry enough colonists to overwhelm your foe. Use as many freighters as necessary, setting their orders to unload colonists as soon as they reach the waypoint.

### Loading Colonists

1. Select your transport fleet into the Command pane.
2. `Shift`-click in the Scanner on the planet or fleet from which you will load colonists.
3. In the Waypoint Task tile, specify `Transport` as the action and `Colonists` as the cargo, then specify the amount you wish to load.

You can create custom transport zip orders to help automate common load and unload orders.

### Unloading Colonists

1. `Shift`-click in the Scanner on the destination colony or colonies.
2. For each waypoint where you wish to unload colonists, specify `Transport` as the action and `Colonists` as the cargo, then specify the amount you wish to unload.

Be sure not to unload more colonists than the planet can support.

## Already-Inhabited Planets

You cannot colonize a planet already inhabited by another race. If you transfer colonists using Transport orders, you automatically initiate ground combat with the current inhabitants. At that point your colonists become ground troops.

If more than one player lands ground troops on the planet during the same year or turn, everyone fights until only one side is left.

You cannot invade any planet that has a starbase in orbit. This means you must destroy the starbase with your war fleet before you can beam down.

## Alternate Reality Notes

### Transporting Alternate Reality Colonists

Alternate Reality races can take damage while traveling in space. Interstellar travel kills `3%` of any colonists in the fleet per year.

### Alternate Reality Races and Invasion

Since Alternate Reality races inhabit starbases and not planets, destroying their starbase makes the planet open for colonization. Alternate Reality races also cannot transfer troops down to other players' worlds.
