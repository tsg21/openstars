# 10. Managing Fleets

A fleet is a distinct group of one or more ships, and it can contain any mix of ship types. Fleets can be created, merged, and split at any point in the game. You design ship types, add them to production queues, create fleets, then assign waypoints and tasks. Fleets can be used for exploration, defense, offense, colonization, remote mining, and transporting minerals and people.

## Assembling Fleets

Each player can have up to `32,000` ships of each design in a fleet, with up to `16` different designs per fleet, and up to `512` fleets total.

For some tasks, a fleet with a single ship is sufficient. Exploration or colonization usually needs only one ship outfitted with the appropriate technology. However, moving large quantities of minerals, defending planets, and attacking other players often works better with large groups of ships combined into a single fleet.

You can merge and split fleets as needed by using the `Merge Fleets` waypoint task or the `Merge` and `Split` buttons in the Command pane. The ships involved must be in the same location.

## Warp Speed

A fleet's warp speed determines both the number of years it takes to reach a waypoint and how much fuel it uses. Actual distance traveled is the square of the warp speed. For example, a fleet traveling at `Warp 8` can move up to `64` light years in a turn.

The Fleet Waypoints tile normally suggests an optimum speed that uses the least fuel while still delivering the fleet in the shortest time. If a stargate is present and safe to use for travel between waypoints, Stars! selects it automatically. If the next waypoint is a friendly starbase, or if the fleet has `Scrap Fleet` or `Colonize` orders, or includes a hull with a colony pod, the fleet travels at the maximum speed allowed by its engine and fuel supply.

Read chapter 11, Navigation, for more on using stargates.

### Maximum Speed

All engines have an absolute maximum speed, a maximum safe speed, a maximum free speed, and an optimum speed.

The absolute maximum speed for all engines is `Warp 10`. The maximum safe speed for most ships is `Warp 9`. You can push a fleet to `Warp 10`, but each ship in the fleet then has a `10%` chance of being lost in transit. Only ships using warp-10-capable engines can travel safely at `Warp 10`. In the Technology Browser, a yellow warning pattern between warp `9` and `10` indicates an engine that cannot do so safely.

For most standard engines, the maximum free speed is `Warp 1`, meaning the ship can travel at that speed without consuming fuel.

For standard engines, the optimum speed is the highest speed that uses less than `120%` fuel. For Ramscoop engines, the optimum speed is the highest speed the engine can maintain without consuming fuel. To learn the best speed for a specific engine, use the Engines section of the Technology Browser and review its Fuel Usage vs. Warp Speed graph.

The grid between warp `9` and `10` on those graphs indicates that a ship using that engine has a `10%` chance of self-destructing if it travels at `Warp 10`.

### Traveling at Warp 1 Without Fuel

Any ship can travel at `Warp 1` without using fuel. This means moving `1` light year per year of play. Ships also generate tiny amounts of fuel at `Warp 1`, which can occasionally provide enough energy for small bursts of speed. This is mainly useful when you are very close to your destination, nearly out of fuel, and do not want to send a rescue ship.

## Finding and Switching Between Fleets

The simplest way to locate a planet or fleet is to use the `Find` command. Use the `Command (Find)` menu item or press `Ctrl-F`.

To find one of your own fleets, enter any of the following:

- The fleet number in any common format, such as `fleet #58`, `fleet 58`, `#58`, or `58`
- The fleet's full name

To find another player's fleet, enter its identification in this format:

```text
race_name fleet #fleet_number
```

If Stars! says it cannot find a planet or fleet by that name, try again and confirm that you entered the correct name or number and used the correct format for another player's fleet. If it still cannot be found, the fleet may no longer exist.

### Finding Fleets by Ship Design

If you are looking for a fleet with a specific composition:

1. Select the Scanner pane's `Ship Design Filter`.
2. Choose the ship type from the pop-up list. Only fleets containing that ship type will appear in the Scanner.
3. Double-click the fleets shown in the Scanner. If more than one fleet is present at a location, continue clicking to cycle through them in the Command pane.

You can also use the `Next` and `Prev` buttons on the Fleet tile, or click in the Fleet report from `Reports (Fleets)`.

Details for each fleet are listed in the Fleet Composition tile.

### Switching Between Fleets

You can switch between fleets in several ways:

- Use `Find` (`Ctrl-F`), then click the fleet in the Scanner pane.
- Use the `Prev` and `Next` buttons on the Fleet tile to scroll through your fleets in the current Fleet Summary Report sort order.
- Click a location where more than one fleet is present. Right-click and choose another fleet from the pop-up list, or continue clicking that location until the desired fleet appears in the Fleet tile.
- Select a fleet from the dropdown in the Other Fleets Here tile.
- Click the row for that fleet in the Fleet Summary Report.

## Naming Fleets

1. Select the fleet you want to rename so it appears in the Fleet tile.
2. Click `Rename` in the Fleet tile.
3. Replace the existing text with a more descriptive label.
4. Confirm the dialog.

The new name appears in the Fleet tile and everywhere else the fleet name is displayed.

You can use either the new name or the fleet number when using `Find`. Other players cannot see the names you assign to your fleets.

## Using Fuel

Fuel is a manufactured commodity made of anti-matter and measured in milligrams (`mg`). Because it has little mass, it has little effect on ship mass and therefore little direct effect on fuel usage. Fuel can be obtained from starbases with shipbuilding capability or transferred from other fleets. It is also created by ships traveling at their engine's free speed, by fuel transports, and by ships equipped with Anti-Matter Generators.

Fuel is shared by all ships in a fleet. A fleet's fuel capacity is the sum of the fuel capacities of its ships. Fuel usage depends partly on the total mass of the ships and cargo in the fleet, and partly on the fuel efficiency of each ship at the selected speed. All ship types can move at any speed, but some consume much more fuel than others.

The manual gives this formula:

```text
Ship fuel usage = (ship mass x efficiency x distance / 200 + 9) / 10
```

Fuel usage between waypoints is shown in the Fleet Waypoints tile. The amount shown for reaching the selected waypoint is exact.

### Sometimes Slowing Down Uses More Fuel

Each year's travel is a separate jump that uses a discrete amount of fuel. A slower speed can therefore consume more total fuel if it adds extra travel years.

The manual's example:

- At `Warp 5`, a fleet traveling `100ly` might use `3mg` per year, take `4` years, and spend `12mg` total.
- At `Warp 4`, the same trip might use `2mg` per year but take `7` years, for `14mg` total.

In that case, the faster trip is more economical overall.

### Refueling

To refuel, simply move a fleet into orbit around one of your planets that has a starbase with shipbuilding capability. Refueling happens automatically. Fuel can also be transferred between fleets manually or by using a `Transport` waypoint task.

### Fuel and Combat

Ships do not use fuel while in combat.

### Fuel Transports

Fuel transports produce `200mg` of fuel each year regardless of how far they travel.

### Fuel and Ramscoop Engines

Ramscoop engines draw fuel from surrounding space, allowing travel up to a certain speed at no cost. If you load fuel onto a fleet using ramscoops and set a speed above the free-travel limit, the fleet travels at the chosen speed until it runs out of fuel, then automatically slows to the ramscoop's maximum free speed. Ramscoops generate fuel when traveling at their free speed, and traveling below that speed can generate even more fuel.

### Fuel, Stargates, and Wormholes

Ships do not use fuel while traveling through a stargate or a wormhole.

Only races with the `Interstellar Traveler` trait can take cargo through stargates. All other races are limited to fleets that do not carry cargo. Fuel does not count as cargo when passing through a stargate.

Wormholes are unstable and can wander, so any fleet using one should keep enough fuel to return to a friendly planet if the far end shifts and leaves the fleet far from its expected destination.

### Running Out of Fuel

Even careful emperors occasionally run out of fuel. Fleets using Ramscoop engines are not in much danger, because they automatically slow down and continue at their fastest free speed. Fleets using normal engines have several choices:

- Send a rescue fleet
- Ignore the stranded ships
- Scrap them
- Let them limp home at `Warp 1`

Tip: Because fuel is shared across the fleet, a ship with low fuel capacity is more likely to reach its destination if merged into a fleet with a much larger fuel supply.

Tip: Fuel transports also help damaged ships in the same fleet heal `5%` or `10%` faster, depending on the hull type of the fuel transport.

Every engine type has a different maximum free speed. See the Engines section of the Technology Browser for details.

As noted earlier, any ship can travel at `Warp 1` without consuming fuel.

## Routing Fleets

Routing automatically sends fleets from one planet to another. If stargates are available, Stars! uses them. If the destination planet is yours and already has a route destination of its own, the fleet is automatically passed onward to the next point.

Routing is most useful in large universes where you regularly distribute new ships from specialized production centers to other parts of your empire. It can also move existing fleets from one side of your empire to the other while requiring you to set only one waypoint within fuel range.

Routing is a function of a planet's production center.

If you choose a waypoint that the fleet cannot reach with its current speed and fuel supply, the Fleet Waypoints tile displays a fuel warning.

### Setting a Route Destination

To set a planet's route destination:

1. Click `Route` in the planet's Production tile.
2. Move the cursor into the Scanner and click the route destination.

A line appears between the origin and destination. Any ship with route orders, as well as any newly built fleet, will be sent to that destination.

To change the route destination:

- Click `Route`, then click the new destination.

To remove a route:

- Click `Route`, then click the planet of origin.

Tip: You can also change a planet's route destination by holding `Ctrl` and clicking the new destination.

### Passing Fleets Along a Route

1. Set a route destination for each planet in the path.
2. Select the fleet to be routed.
3. In the Waypoint Tasks tile, assign the fleet `Route` orders.

When the fleet arrives at a planet with a route destination, it is automatically passed along. If the planet has a starbase with shipbuilding capability, the fleet is automatically refueled there as well.

### Route Behavior

If the route destination is an uncolonized planet and the fleet includes remote miners, its orders automatically change to `Remote Mining` on arrival. If the route destination is a planet where one of your mining fleets is already in orbit, the final waypoint task automatically changes to `Merge with Fleet`.

Route orders do not automatically colonize the destination. You must specify colonization orders yourself.

## Rendezvousing Fleets

It is often useful to specify one fleet as the destination of another, especially when transferring cargo between fleets, merging fleets, or chasing an opponent's fleet.

To rendezvous one fleet with another, select the destination fleet's current position as the waypoint for the pursuing fleet. As long as the target can still be detected by the pursuing fleet's scanner, the fleet will continue to follow it until it catches up or runs out of fuel. If the pursuing fleet loses sight of the target, it travels to the target's last known position.

### Picking a Fleet Out of a Crowd

When two or more fleets are at the same location or very close together and you want to rendezvous with a specific one:

- If the fleets are merely close together, zoom in with the plus (`+`) key until they are clearly separated, then set the waypoint on the desired fleet. Use minus (`-`) to zoom out again afterward.
- If two fleets occupy the same location, click the blue diamond in the Fleet Waypoint tile and choose the destination fleet from the pop-up list.
- If your goal is to refuel or join the destination fleet, use the `Merge with Fleet` waypoint task after specifying that fleet as the waypoint.

## Splitting Fleets

To split a fleet, click `Split` or `Split All` in the Fleet Composition tile.

- `Split` transfers any number of ships between the fleet under command and the fleet selected in the Other Fleets Here tile.
- `Split All` divides all ships in the fleet into separate fleets based on ship design.

You can use the Ship Count overlay to help locate positions where more than one fleet is present.

The `Split` and `Split All` buttons are disabled once you reach the `512`-fleet limit.

`Split All` also fails if using it would raise your total above `512` fleets.

See chapter 14, Transporting Freight, for more on transferring fuel and cargo between ships.

## Merging Fleets

To merge entire fleets with others, click `Merge` in the Fleet Composition tile. This lets you combine any set of fleets at the same location.

You can also merge fleets by using the `Merge with Fleet` waypoint task in the Waypoints Tasks tile.

If you want to transfer some ships but not all of them between the fleet under command and another fleet at the same location, click the `Merge` button in the Other Fleets Here tile.

## Scrapping Fleets

You can scrap or destroy a fleet by merging it with a colony fleet or by choosing the `Scrap Fleet` waypoint task. Scrapping lets you recover a percentage of the minerals used in the ship's construction, as well as all mineral cargo on board. It is a practical way to retire ships built from hull designs that are no longer useful. Fleets can be scrapped at a planet or even in deep space.

The recovered construction minerals are added to the minerals on the planet where the fleet is scrapped. The percentage recovered depends on where and how the fleet is scrapped:

- Colonization mission: leaves `75%` of the construction minerals on the planet's surface
- `Scrap Fleet` at a starbase: leaves `80%` of the construction minerals on the planet's surface
- `Scrap Fleet` at a planet without a starbase: leaves `33%` of the construction minerals on the planet's surface
- `Scrap Fleet` in deep space: all construction minerals are lost

### Ultimate Recycling

Races with the `Ultimate Recycling` trait recover `90%` of the minerals and `70%` of the resources when scrapping at a starbase. Scrapping at a planet gives `45%` of the minerals and `35%` of the resources.

### Feeding Scraps to Other Players

You can exchange technology with an opponent by scrapping a fleet at that opponent's planet. The opponent has the same chance to learn the technology as if they had met you in battle. They also receive the recycled minerals and, if they have the `Ultimate Recycling` trait, the resources as well.

## Report for Your Fleets

The Fleet Summary Report shows where all your fleets are located, the orders each will follow at the next waypoint, the fuel supply, cargo, fleet composition, cloaking percentage, and current mass.

- Click anywhere in a row to go to that fleet.
- Click the `Composition` column to display the fleet's composition and any damage. If the composition appears in red, one or more ships in the fleet has taken damage. A plus sign (`+`) indicates that the fleet includes more than one ship type.
- Click the `Cargo` column to transfer cargo.

Read chapter 18, Reports, for more on using the reporting screens.
