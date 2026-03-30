# 11. Navigation

You cause a fleet to move by assigning it one or more destinations, or waypoints. You can assign a task at each waypoint, such as transport, colonize, remote mine, or scrap fleet. When fleets reach their last waypoint, they stop.

## Adding Fleet Waypoints and Tasks

To add a fleet waypoint and a task to accomplish at that waypoint:

1. Select the fleet into the Command pane. Double-click on its location in the Scanner, or right-click on it and choose the fleet from the pop-up list.
2. If you want to follow a fleet currently at your location, right-click on the diamond in the Fleet Waypoints tile and select that fleet from the list. That fleet then appears as the waypoint.
3. `Shift`-click on the destination waypoint. This can be any planet, fleet, other object, or point in space. A green line appears between your current location and the new waypoint.
4. Assign an appropriate task from the Waypoint Task tile. If there is no work to be done at that waypoint, choose `No Task Here` from the dropdown list.
5. Repeat steps 3 and 4 to add more waypoints.
6. If you want the fleet to continually repeat the entire series of tasks until it is interrupted, and if the final waypoint is the same as the starting waypoint, check `Repeat Orders` in the Waypoint Task tile.

## Notes and Tips on Waypoints and the Scanner

### Distance and the Scanner Grid

When you set a waypoint, notice that the Scanner snaps to an invisible grid. The grid snap is one light year and cannot be redefined. Vertical or horizontal distance is measured in whole years. Diagonal distance between coordinates is a decimal amount slightly larger than one light year.

You can disable snapping to objects by holding down the `Shift` key while dragging the cursor.

### Selecting One Object from Many at the Same Location

If there are multiple objects at the location, click on the blue diamond in the Fleet Waypoints tile and select the object you wish to make the waypoint.

### White Fleet Paths

The fleet path appears in white if two or more legs of the route are identical, for example if you set a return path along the same route.

### Don't Choose the Same Waypoint Twice in a Row

You cannot add two consecutive waypoints at the same location.

## Moving Fleet Waypoints

If you want to move a waypoint from one place to another, move the cursor over the point you want to move and the cursor will change to a hand. Click the mouse and the hand will close. Drag the mouse to the new destination.

The destination snaps to objects when you get close to them so you do not accidentally miss a planet. If you want to set a waypoint close to an object, but not at the object, hold down `Shift` while dragging to disable the snap-to-object behavior.

## Deleting Fleet Waypoints

There are two ways to remove a waypoint:

- Click on the waypoint you want to remove, then press either the `Backspace` or `Delete` key.
- Click on the waypoint, then drag it to the next or previous waypoint and release.

## Stargate Navigation

You must have a stargate at the source planet and at the destination planet. You can navigate using your own stargates and a Friend's stargates. Stargates have limitations both on the mass they can transfer and the distance the mass is transferred.

A stargate appears as a dark green dot in orbit.

To send a fleet through a stargate:

1. If necessary, bring the fleet to the planet with the stargate. Make sure the fleet is carrying only fuel. For all races except those based on the `Interstellar Traveler` trait, cargo must be transferred to the planet or to another fleet before using the stargate.
2. `Shift`-click on the destination planet, which must also have a stargate, selecting it as the next waypoint.
3. Click in the Warp Speed gauge and drag to the end of the gauge. The speed changes to `Use Stargate`.

On the next turn, your fleet appears at the destination planet regardless of the distance traveled.

Use the Technology Browser to display statistics for each type of stargate. Press `F2` and select `Orbital Devices` from the dropdown list.

### Stargate Travel Time

The Fleet Waypoint tile can show these travel-time states:

- `1 Year`: Travel is safe.
- `Uncertain`: You do not know enough about the destination planet, or your data is old. Your stargate attempts the jump, but there is no guarantee there is a gate at the other end.
- `Danger`: Your fleet will take damage in transit. The fleet exceeds the mass or distance limitation of one or both stargates.
- `Never`: A stargate does not exist at one or both waypoints, or the jump exceeds more than five times the mass or distance limitation.

### Range

Range, meaning how far fleets can jump safely, is determined by the source stargate.

To learn the range of a stargate that belongs to you:

1. Left-click on the Starbase tile to display the starbase schematic with the included stargate.
2. Read the bottom number shown on the stargate picture. That is the range.

If the source stargate belongs to a Friend, you need to ask them about the range.

You may be able to exceed the normal range by up to five times the distance and still arrive at the other gate. The fleet will, however, always take damage. Keep this in mind: any time you exceed either the range or the mass limit, there is a chance that the fleet will explode.

### Hull Mass Limitation

Most stargates have a safe hull mass limitation. Only ships that do not exceed the safe mass limitation of both the source and destination stargates will arrive safely. If your fleet exceeds this limitation, Travel Time on the Fleet Waypoint tile reads `Danger`.

To learn the mass limitation of a stargate that belongs to you:

1. Select the planet into the Command pane.
2. Move the cursor over the Starbase tile.
3. Left-click on the tile to display the starbase schematic with the included stargate.
4. Read the top number shown on the stargate. That is the mass limit.

If the source stargate belongs to a Friend, you need to ask them about the mass limitation.

You can exceed the acceptable mass capacity by up to five times the amount and possibly still arrive at the other gate. Ships always take damage when you exceed capacity, and there is also a chance that the ship will explode.

## Wormhole Navigation

Wormholes are spacial anomalies that appear and disappear at whim. There are several types, some more stable than others. Wormholes offer free travel across huge distances of space and have no limitations on ship or cargo mass.

Wormholes appear only in deep space, being somewhat repelled by the gravity wells caused by planets.

Wormhole stability ranges from `Rock Solid` to `Very Unstable`. Rock Solid wormholes can stay in one general area for 30 years or more. Very Unstable wormholes tend to move to a different area within about five years.

Each end of the wormhole moves independently. Due to their complex nature, wormholes jiggle a bit every year. Their exact location is always shifting.

To navigate a wormhole:

1. Select the wormhole as a waypoint.
2. Your fleet enters the wormhole as soon as it reaches the opening and appears at the other end in the same year.

Click on a wormhole to display its destination, if known, and its stability range in the Selection Summary.

## Detecting Wormholes

Similar to a cloaked fleet, a wormhole is hard to see. To normal scanners, a wormhole is `75%` less visible. Once you discover a wormhole, it is no longer cloaked to you.
