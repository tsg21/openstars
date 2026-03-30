# 16. Patrolling

While on patrol, your fleet will automatically intercept and attack any incoming enemy fleets within a specified range. Fleets on patrol will not target neutrals or friends.

## Assigning Patrol Orders

To place a fleet on patrol duty:

1. Give the fleet one waypoint in the Scanner.
2. In the Waypoints Task tile, select the `Patrol` task.
3. Select an intercept range. Your fleet will only attempt to intercept enemy fleets it detects within the specified range.
4. Set the intercept speed using the warp factor gauge, or accept the default of `Automatic`. The default chooses the optimum speed, attempting to use the least fuel while intercepting in the shortest possible time. You will be notified when a patrolling fleet is given a new target and can adjust the warp speed or retarget it before the intercept happens.
5. Set any additional waypoints. The `Patrol` order will be carried out automatically for each waypoint until you assign a different task.

To station a patrol at a particular location, send the fleet to that location, then give it the `Patrol` task and select the `Repeat Orders` checkbox in the Fleet Waypoints tile.

The fleet will only target enemies within its intercept range from that point and will automatically return there after the intercept.

## Patrol Targets Enemies Only

Fleets on patrol will only intercept and attack enemy fleets. In a single-player game against AIs, all other players are your enemies. In a multi-player game, you can choose who is your enemy, friend, or neutral.

To make a player your enemy in a multi-player game:

1. Choose `Commands (Player Relations)`, opening the Player Relations dialog.
2. Select the player in the dropdown list, then click `Enemy`.
3. Click `OK`.

Patrol does not immediately target an enemy fleet. Targeting occurs after all players move, as one of the last tasks in generating a new turn. This lets you receive a message and inspect the patrol order that was given, altering it if necessary before the ship commits to the attack.

If you want a ship to patrol and attack a particular enemy fleet you can already see, add a waypoint at that enemy fleet with orders to patrol at that ship.

## Patrol and Battle Plans

Patrol takes battle plans into account when deciding who to intercept. Your primary target will be matched according to its hull type. For example, if you target unarmed ships, your patrol fleet will only target fleets guaranteed to be unarmed. It would not target a battleship, even if you have fought it before and know that it does not carry weapons.

The original manual ends this section with a cross-reference to the battle plans material, but the extracted page reference is incomplete in this chapter source.
