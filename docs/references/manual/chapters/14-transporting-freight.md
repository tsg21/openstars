# 14. Transporting Freight

You can transport minerals, fuel, and colonists from waypoint to waypoint. These waypoints can be either planets or fleets. Freight is either carried in ships that have cargo holds or cargo pods, or flung across space using mass drivers.

## Shipping Freight

To get the transport process started:

1. Select the fleet that will carry the cargo.
2. Add a waypoint or series of waypoints in the Scanner pane.
3. In the Fleet Waypoints tile, select the waypoint where you want to load or unload cargo.
4. In the Waypoint Task tile, specify the transport orders:

```text
Select Transport as the task
Select a cargo
Select a load/unload action
```

Repeat this process for each waypoint where you'll load or unload freight.

For a description of different cargo modules and mass drivers, refer to the Technology Browser.

Tip: Races with the Ultimate Recycling trait may find that it is economical to build ships from the desired minerals and simply scrap them at their destination.

### Zip Orders

You can also use Zip Orders to speed things up a bit. Right-click on the blue diamond in the Waypoint Task tile and select one of the sets of orders listed. Left-click on the diamond for a description of the predefined orders. You can also create your own custom Zip Orders.

### Repeat Orders

If you want to set up the fleet to endlessly follow a route until you specify otherwise, check the Repeat Orders box in the Fleet Waypoints tile. If you want the fleet to return to its planet of origin as part of the route, be sure to specify that planet again as a waypoint.

For a description of each transport order, read about the Transport task on page 5-7.

### Routing Fleets

Remember that you can specify another fleet as a waypoint. For example, if you want to set up a route between a remote mining fleet and one of your mineral-needy production planets, specify the mining fleet as the first waypoint and the production planet as the second waypoint.

At the first waypoint, the mining fleet, set transport orders for each mineral you plan to load, specifying `QuikLoad` using the Zip Orders diamond. At the second waypoint, specify the `QuikDrop` transport Zip Order for each type of mineral you load from the miner.

If you want to set up regular transport routes and you're playing in a large universe, consider using fleet routing to send your ships from planet to planet.

## Transferring Fuel and Cargo to Other Fleets

Fuel and minerals can be transferred between fleets. These fleets can belong to you or an opponent. Once given, the fuel or cargo cannot be taken back. This opens up possibilities for trade as part of a diplomatic strategy.

Fuel and minerals can also be transferred from any player's fleet to any player's planet. However, if one player attempts to transfer colonists to another player's planet, regardless of their relationship, that's called an invasion and is dealt with in the expected manner.

Transfer cargo using one of the cargo transfer dialogs. These are accessible from several tiles in the Command pane.

## Jettisoning Cargo

As indicated by the Location tile above, you must be in deep space to jettison cargo. Jettison if you don't have enough fuel, must reach your destination or make a fast getaway, and can't wait for another ship to reach you with fuel.

Transferring cargo to an opponent's ship or a planet you don't own effectively does the same thing: you lose the cargo. Jettisoned cargo is lost to the cosmos.

You cannot jettison cargo if there is salvage at the same location.

## Creating Custom Zip Orders

A Zip Order is a common transport order you wish to specify many times in a game by selecting the Zip Order name. Stars! provides four predefined Zip Orders, including Clear. You can't change the predefined orders, but you can add up to four custom Zip Orders.

Once you create a custom Zip Order, it becomes available in all your games until you delete it. Here's how to create one:

1. Specify the transport order in the Waypoint Task tile.
2. Set up the order you wish to add to the Zip Order list by selecting the appropriate cargo items and operations.
3. Right-click on the blue diamond in the Waypoint Task tile.
4. Select `<Customize>` from the pop-up menu. The Custom Zip Orders dialog appears.
5. Select a Custom Order slot in the dialog.
6. Click on `Import`. This copies in the current transport orders from the Waypoint Task tile. The Rename Zip Order dialog appears.
7. Type the name, then confirm the dialog. The new order appears in the Custom Order dialog.
8. Confirm the Custom Order dialog.
9. Right-click on the blue diamond again. Your custom Zip Order appears in the pop-up.

### Editing a Custom Zip Order

1. Repeat steps 1 through 5 above, and in step 5 select the order you wish to modify.
2. Click on `Import` and confirm the Rename Zip Order dialog.

## Flinging Mineral Packets

Flinging a mineral packet is a two-step process.

### Step 1: Target the Mass Driver

This must be done before you build the packets, or the packets will disintegrate. Of course, you must also have a mass driver on the planet's starbase.

Mass driver information and controls:

1. Click on the `Set Dest` button on the Starbase tile.
2. Select a target by left-clicking on the destination planet in the Scanner. The Scanner displays the path as a purple line.
3. Accept the default packet speed or click in the mass driver's warp gauge to set a new speed.

Tip: You can also target a mass driver by Shift-clicking on the destination planet while the source planet is in the Command pane.

Slower speeds allow you to fling packets to planets with lesser mass drivers, meaning you want the planet to catch the packet. Packets flung above the rated speed are unstable but get there quicker and do more damage.

For the packet to arrive safely, the target must also have a driver of equal or greater capacity. If the planet has a lesser mass driver, or no driver at all, the packet will destroy some or all of the colonists and installations on the planet's surface. On both inhabited and uninhabited planets, two-thirds of the minerals in the packet will be lost in the collision.

### Step 2: Build and Fling the Packets

You build packets using the Production dialog. The packets are automatically flung as soon as they're built.

1. Click on `Change` in the Production tile, opening the Production dialog.
2. Look at the production inventory. It contains a packet type for each mineral and a mixed packet that contains all three minerals. When you click on a packet type in the inventory, the numbers below the inventory show how many kT of each mineral is required to build the packet. The inventory also includes an auto-build item for sending mineral packets.
3. Select the packets you want to build, then add them to the queue. Your planet will build and fling packets until you remove the item from the queue.

The Messages pane informs you each time a packet is sent. Mineral packets in scanner range appear in the Scanner as a green square if they belong to you or a red square if they belong to an opponent.

Races based on the Interstellar Traveler trait are less adept at building and using mass drivers than other races. Their mass drivers are only half as effective at catching minerals as rated. They are less efficient at flinging minerals, and all mineral packets they fling decay regardless of speed.

You can't attack mineral packets. You can intercept them and use the Other Fleets Here tile to transfer their contents to your fleet.

### Displaying a Packet's Destination

When you click on any mineral packet in the Scanner, its destination and contents are displayed in the Summary pane.

### Packet Physics

Races with the Packet Physics trait always detect any mineral packet in flight, regardless of the packet's location in the universe.
