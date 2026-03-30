# 10. Managing Fleets

### 10 MANAGING FLEETS

A fleet is a distinct group of one or more ships, and can be any mix of ship types. Fleets can be created, merged, and split at any point in the game. You design the ship types, add them to production queues, create fleets, then assign waypoints and tasks. Fleets can be used for exploration, defense and offense, colonizing, remote mining, and transporting minerals and people.

### ASSEMBLING FLEETS

Each player can have up to 32,000 ships of each design in a fleet, with up to 16 different designs, and up to 512 fleets.

For some tasks a fleet with a single ship is sufficient. For example, exploration or colonization usually only requires one ship outfitted with the appropriate technology. However, for moving large quantities of minerals around, for defending your planets and for attacking other players it’s very useful to have large groups of ships in a single fleet.

You can merge and split fleets as you wish, using the Merge Fleets waypoint task or the Merge and Split buttons in the Command pane. The affected ships must be in the same location.

### WARP SPEED

A fleet’s warp speed determines the number of years it takes to reach a waypoint, as well as fuel usage. Actual distance traveled is the square of the warp speed. For example, a fleet traveling at Warp 8 will move up to 64 light years each turn.

The Fleet Waypoints tile always suggest an optimum speed to reach the waypoint, using the least amount of fuel to deliver the fleet in the shortest amount of time. If a stargate is present and safe to use for travel between waypoints, it is automatically selected. If the next waypoint is a friendly

Learn more about

Navigation Using

- Stargates, p
starbase or the fleet has Scrap Fleet or Colonize orders, or includes a hull with a colony pod, the fleet travels at the maximum possible speed for its engine and fuel supply.

Maximum Speed

All engines have an absolute maximum speed, a maximum safe speed, a maximum free speed and an optimum speed.

The absolute maximum speed for all engines is warp 10. The maximum safe speed for most ships is warp 9. You can push your fleet to warp 10, but you’ll have a 10% chance of losing each ship in the fleet at that speed. Only ships using warp 10 capable engines can travel safely at warp 10. You can tell if an engine is warp 10 capable by viewing it in the Technology Browser and seeing if the area between warp 9 and 10 is covered with a yellow warning pattern or not.

For most standard engines the maximum free speed is warp 1. This means that you can travel at warp 1 using no fuel.

For standard engines the optimum or best warp speed is the maximum speed at less than 120% fuel usage. For Ramscoop engines the best warp speed is the maximum speed that the engine can travel using no fuel. To learn the best speed for a specific engine, visit the Engines section of the Technology Browser. The Fuel Usage vs. Warp Speed graphs in the Browser shows this speed for each engine. The following graph shows that the best warp speed for this engine is warp 6.

The grid between warp 9 and 10 shows that the ship using that engine has a 10% chance of self-destructing while traveling at warp 10.

Travel Warp 1 without Using Fuel

Any ship can travel Warp 1 without using fuel. This means you travel 1 light year per year of play. You also generate tiny amounts of fuel at Warp 1, and may be able to put on small bursts of speed. This really is helpful only if you’re close to your destination, almost out of fuel, and don’t want to bother sending a rescue ship.

The simplest way to locate a planet or fleet is to use the Find command. Use either the Command (Find) menu item, or press CTRL-F.

To find a fleet of your own, do one of the following:

- Enter the fleet number using any format (fleet #58, fleet 58, #58, 58).
- Enter the full name of the fleet.
To find another player ’s fleet:

- Enter the fleet identification using this format:
race_name fleet #fleet_number

If Stars! says it cannot find a planet or fleet by that name, try again, making sure you type the correct name or number, or that you used the correct format for finding another player ’s fleet. If you still can’t find a fleet, it may no longer exist.

Ship Design filter

If you are looking for a fleet with a specific composition:

1. Select the Scanner pane’s Ship Design Filter.
2. Select the ship type from the pop-up list. Only fleets that contain that type
of ship will appear in the Scanner.

3. Double-click on the fleets now shown in the Scanner. If more than one
fleet is at a location, continue to click. As you click, the fleets will cycle through the Command pane. You can also use the Next or Prev buttons on the Fleet tile, or click in the Fleet report--Reports (Fleets) menu item.

Details for each fleet are listed in the Fleet Composition tile.

### SWITCHING BETWEEN FLEETS

Switch between fleets using one of the following methods:

- Use the Find command (CTRL-F), then click on the ship in the Scanner
pane.

- Press the Prev and Next buttons on the Fleet tile to scroll through all your
fleets in the Command pane. The fleets appear in the current sort order of the Fleet Summary Report.

- Click a location where more than one fleet is present. Right-click on the
spot and select another fleet from the pop-up list. Alternately, continue to click in the location until the fleet appears in the Fleet tile.

- In the Other Fleets Here tile, select a fleet from the dropdown list.
- Click on the row for that fleet in the Fleet Summary Report.

### NAMING FLEETS

1. Select the fleet you wish to rename, displaying it in the Fleet tile.
2. Click on Rename in the Fleet tile.
3. Replace the existing text with your own more descriptive label.
4. OK the Rename dialog. The new name appears in the Fleet tile and
anywhere else you’d expect the name to be displayed.

You can use either the new name or the fleet number when Finding a fleet. Other players cannot see the names you have given your fleets.

### USING FUEL

Fuel is a manufactured commodity made of anti-matter and is measured in milligrams (mg). This means it has little effect on the ship’s mass (and thus, fuel usage). Fuel can only be obtained from starbases with ship building capability or from other fleets. It is also created by ships traveling at their engine’s free speed, by fuel tankers and by ships with Anti-Matter Generators.

Fuel is shared by all ships in a fleet. The fuel capacity of a fleet is the sum of the fuel capacity for each ship in the fleet. The rate at which fuel is used is based partially on the mass of all ships and cargo in the fleet. Fuel usage is also based on the rate at which each ship in the fleet uses fuel at a given speed. All ship types can move at any speed, but they each burn different amounts of fuel to achieve that speed. The total fuel usage for the fleet is the sum of the fuel usage for all the individual ships.

Ship_fuel_usage = (ship_mass x efficiency x distance / 200 + 9) / 10

Fuel usage between waypoints is shown in the Fleet Waypoints tile. The amount shown for reaching the selected waypoint is always exact.

Estimated Fuel Usage for travel from the current waypoint to the fleet named Perfect Logic #163, with speed set to Warp 8.

Sometimes Slowing Down Uses More Fuel

Each year’s travel is a separate jump that uses a finite, countable number of milligrams of fuel. Let’s say that you have a fleet that can travel at warp 5 for 3mg per year of travel. A journey of 100ly would take 4 years and use 12mg of fuel. If you slowed down to warp 4 it would only cost 2mg per year of travel but the journey would take 7 years for a total of 14mg of fuel. This is a case where it is more economical to go at the faster speed.

Refueling

To refuel, simply visit one of your planets with a starbase with ship building capability in orbit. You’ll be refueled automatically. Fuel can also be transferred between fleets manually or with a Transport waypoint task.

Fuel and Combat

Ships don’t use fuel while in combat.

Fuel Transports

Fuel transports produce 200 mg of fuel each year, regardless of how far they travel.

Fuel and Ramscoop Engines

Ramscoop engines draw fuel from surrounding space, allowing them to travel up to a certain speed at no cost. If you load fuel on a fleet using ramscoop engines and set a speed greater than that allowed for free travel, the fleet will travel at the set speed until it runs out of fuel, then slow to the maximum free speed for that ramscoop. Ramscoops generate fuel when traveling at the free speed. Traveling at speeds below the maximum free speed can generate even more fuel.

Fuel, Stargates and Wormholes

Ships don’t use fuel while traveling through a stargate or a wormhole.

Only races with the Interstellar Traveler trait can take cargo through stargates. All other races are limited to fleets that do not carry cargo. Fuel does not count as cargo when passing through a stargate.

Running Out of Fuel (Well, Nearly)

Even the best of us occasionally runs out of gas. The same is true for you as an Emperor. For ships with Ramscoop engines this isn’t a problem as they will automatically slow down and continue their journey at their fastest free speed. For ships with normal engines you have several choices. If they are worth saving you can send a fleet to rescue them. If they aren’t worth saving then you can either just ignore them or scrap them. Or you can let them limp home at Warp 1.

Tip: Since fuel is shared by the entire fleet, you can help guarantee that a ship with a low fuel capacity reaches its destination by merging it into a fleet with a large fuel capacity.

Tip: Fuel transports also cause damaged ships in the same fleet to heal 5 or 10% faster, depending on the hull type of the fuel transport.

Speed for Free Each type of engine has a different maximum speed for travel without using Fuel. See the Engines section of the Technology Browser for more information.

Wormholes are unstable and can wander. Be sure that any fleet using a wormhole has enough fuel to return to a friendly planet should the opposite end of the wormhole travel and deposit the fleet far from the expected location.

Any ship can travel Warp 1 without using fuel. This means you travel 1 light year per year of play. You also generate tiny amounts of fuel at Warp 1, and may be able to put on small bursts of speed. This really is helpful only if you’re close to your destination, almost out of fuel, and don’t want to bother sending a rescue ship.

### ROUTING FLEETS

Routing automatically sends fleets from one planet to another. Stargates are used, if they are available. If the destination planet is yours, and it also has a route destination, the fleet will be passed automatically to the next point.

Routing is most useful in large universes where you are regularly distributing new ships from specialized production centers to other points in your empire. Routing can also be used to send existing fleets from one side of your empire to the other, specifying only one waypoint within fuel range.

Fuel Warning in the Fleet Waypoints Tile When you choose a waypoint you can’t reach given the current speed and fuel supply, the Fuel Usage amount displayed in the Fleet Waypoints tile

Routing is a function of a planet’s center of production.

To set a planet’s route destination:

1. Click on the Route button in the planet’s Production tile.
2. Move your cursor to the scanner and click on the route destination. A line
appears between the origin and destination. Any ship that has route orders will be sent to this destination, as well as any newly built fleet.

To change the route destination:

- Click on the Route button, then click on the new destination.
To remove a route:

- Click on Route, then click on the planet of origin.
Tip: You can also change a planet’s route destination by holding down the CTRL key and clicking on the new destination.

To pass fleets from route destination to route destination:

1. Set a route destination for each planet in your circuit or path.
2. Select the fleet to be routed.
3. Using the Waypoint Tasks tile, assign the fleet Route orders. When it
arrives at a planet with a route destination, it will automatically be passed along. If the planet has a starbase with ship building capability, the fleet is automatically refueled as well.

Route Behavior

If the route destination is an uncolonized planet and fleet includes remote miners, its orders are automatically changed at the destination to Remote Mining. If the route destination is a planet with your mining fleet already in orbit, the final waypoint task is automatically changed to Merge with Fleet.

Route will not auto-colonize at the destination. You must specify colonization orders upon the fleet’s arrival.

### RENDEZVOUSING FLEETS

It’s useful to specify one fleet as a destination for another if you are transferring cargo between fleets (for example, between a remote miner and a freighter), merging fleets, or chasing an opponent’s fleet.

To rendezvous one fleet with another, just select the current position of the destination fleet as the waypoint for the fleet that wishes to intercept it. As long as the destination fleet can be detected by the pursuing fleet’s scanner, this fleet will follow the destination fleet until it overtakes it or runs out of fuel. If the fleet in pursuit loses sight of the destination fleet, it travels to the destination fleet’s last known position.

How to Pick a Fleet Out From a Crowd

When two or more fleets are at the same location or close together, and you want to send another fleet to meet with one of them, do one of the following:

- If the fleets are close together, zoom in using the plus (+) key until you
can see everything clearly. Then set the waypoint on the fleet you wish to rendezvous with. Press the minus (-) key to zoom out.

- If two fleets are in the same location and you wish to target one
specifically, or target an opponent’s fleet in orbit, click on the blue diamond in the Fleet Waypoint tile, then select the destination fleet from the pop-up list.

- If the goal is to refuel the destination fleet or join with the destination fleet
then you can use the Merge with Fleet waypoint task. This task requires that you specify the destination fleet as the waypoint.

### SPLITTING FLEETS

To split a fleet, click on the Split or Split All button in the Fleet Composition tile. Choose Split to transfer any number of ships between the fleet under command and the fleet selected in the Other Fleets Here tile. Choose Split All to divide all ships in the fleet into separate fleets based on ship design.

You can use the Ship Count overlay to help you find locations where more than one fleet is present.

Transferring Fuel and Cargo to other

- Ships, p
The Split and Split All buttons are disabled when you reach 512 fleets.

The Split All button will fail if the action will result in you having more than 512 fleets.

### MERGING FLEETS

To merge entire fleets with others, click on Merge in the Fleet Composition tile. This allows you to merge any combination of fleets at the same location.

You can also merge fleets using the Merge with Fleet waypoint task, located in the Waypoints task tile.

If you would like to transfer some but not all ships between the fleet under command and a selected fleet at the same location, click on the Merge button on the Other Fleets Here tile.

### SCRAPPING FLEETS

Scrap or destroy a fleet by merging it with a colony fleet or by choosing the Scrap Fleet waypoint task. Scrapping allows you to regain a percentage of the minerals used in the ship’s construction and all the mineral cargo on board. This is a good way to get rid of ships built using a hull design that is no longer useful. You can scrap fleets at any planet or even in deep space.

The construction minerals you recover are added to the minerals at the planet where the fleet is scrapped. The percentage of minerals recovered depends on the following circumstances:

Colonization mission — leaves 75% of the minerals used in construction on the surface of the planet.

Ultimate Recycling

Races with the Ultimate Recycling trait recover 90% of the minerals and 70% of the resources when scrapping at a starbase. Scrapping at a planet gives 45% of the minerals and 35% of the resources.

Scrap Fleet at a starbase — leaves 80% of the minerals used in construction on the surface of the planet.

Scrap Fleet at any planet without a starbase — leaves 33% of the minerals used in construction on the surface of the planet.

Scrap Fleet in deep space — all construction minerals are lost.

Feeding Scraps to other Players

You can exchange technology with an opponent by scrapping a fleet at the opponent’s planet. The opponent has the same chance of learning the technology as they if they had met you in battle. They also get the recycled minerals and, if they have the Ultimate Recycling trait, they also get resources.

### REPORT FOR YOUR FLEETS

The Fleet Summary report shows where all your fleets are currently located, the orders that each is to follow at the next waypoint, the fuel supply, cargo, fleet composition, cloaking percentage, and current mass.

- Go to a fleet by clicking anywhere in the row for that fleet.
- Display the fleet’s composition and any damage by clicking on the
Composition column. If the composition is shown in red, one or more ships has taken damage. A plus sign (+) indicates that the fleet is composed of more than one ship type.

- Transfer Cargo by clicking on the Cargo column.
Learn more about

- Reports, p
