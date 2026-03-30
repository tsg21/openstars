# Appendix D. Frequently Asked Questions

## Is Anyone Out There?

### Do the AIs (computer players) cheat?

Stars! is one of the few games where computer players do not cheat. The Stars! AIs are governed by the same code that governs human players and receive the same information. Expert-level AIs start with more race design advantage points than human players; that is the only difference.

If you feel like you have been taken advantage of by an AI, let the authors know. They state that they will investigate and correct any unfair advantage if one exists.

### Will anyone listen if I have feedback for the authors?

If you did not like something in particular, experienced problems with the game, or have ideas for the game, the authors ask that you let them know. They state that they answer all mail and value feedback, whether it concerns a bug, a usability problem, or a missing feature.

When submitting ideas, keep in mind that Stars! is turn-based, not real-time.

### How do I get player and technical support?

If you have not used the tutorial, the manual recommends starting there. Even experienced players can learn from it. The online player's guide (`Help`) also contains detailed documentation about virtually every aspect of the game.

If those resources do not answer your questions, the appendix lists the following support contacts:

- `support@webmap.com`
- UK: `http://www.empire.co.uk/support/support.htm`
- US: `http://www.empire-us.com/support/support.htm`

### How do I submit bug reports?

1. Write a description of the suspected bug in a text file.
2. Zip all relevant game files together with that text file:

```text
pkzip gamename.zip gamename.* backup\gamename.* bugnotefile
```

3. Send the zip file in one of these ways:

- Mail the zip file to `bugstars@webmap.com` along with a description of the problem.
- FTP the zip file to `beast.webmap.com/pub`, then send email to `bugstars@webmap.com` with a description of the problem and the name of the uploaded zip file.

The manual notes that receiving the actual game files makes bug investigation much easier and thanks players for the extra effort.

### When I zip my game files, they don't get any smaller. Why not?

Stars! game files are already compressed.

## Different Strokes

### Can several people play on the same computer using one copy?

Yes. Up to 16 people can play "hot-seat" on the same computer with one copy of Stars!, provided all players use that same copy and only one copy of the game is running.

To play one game with several players on one machine, the manual gives two methods:

#### Method 1

Each player submits their turn, saves, and then returns to the splash screen using `File (Close)`. You do not need to exit Stars! between players.

#### Method 2

If you have enough memory, about `2-4 MB` per player depending on universe size, you can run multiple instances of the game. An "instance" is one running session of the game.

For setup and play details, see chapter 3, `Multi-Player Setup`.

### Can two or more people using the same machine submit turns in the same email game?

Yes. When your `.x#` file is created, it is marked with both your serial number and a fingerprint of your machine. The host only penalizes two or more people playing with the same serial number and different machine fingerprints.

Any number of people can submit turns from the same machine with the same serial number. If, however, you submit one `.x#` file from each of two different machines, then each machine must use a unique serial number.

The manual notes that this allows situations such as taking a friend's turn while they are away or having multiple family members play from the same machine, while keeping copy protection relatively non-intrusive.

### Where can I find hosted games and other players?

The appendix lists these resources:

- Stars! website: `http://www.webmap.com/stars!`
- Usenet newsgroup: `rec.games.computer.stars`

The website is described as including a waypoints page that lists Stars! sites where you can join games and find player resources.

## A Host's Work Is Never Done

### Is it possible to host Stars! in DOS?

It depends. If the machine cannot run Windows, the answer is no. If the machine can run Windows but usually does not, the answer is yes.

The manual says it is possible to launch Windows and Stars! from a DOS batch file in a way that lets Stars! generate turns for one or more games and then exit all the way out of Windows so the batch file can continue. A stray OCR fragment in the source chapter has been omitted here.

### Why is there any way for a host to retrieve a lost password?

The manual's answer is that any utility that allowed hosts to remove or change passwords would remove all security from the game. A dishonest host could copy the game files elsewhere, remove passwords in that copy, and inspect every player's data without the real players ever knowing.

The same logic applies to any player in a network game. The appendix argues that multiplayer security is effectively all-or-nothing, and that without at least the existing level of security, Stars! multiplayer would be meaningless.

### I have multiple licenses. How do I restore a turn ruined by installing the wrong serial number on a machine?

Copy the game files from the backup directory to the game directory, open each affected player's turn, and choose `File (Save)`. This resaves their `.x#` files with the correct serial numbers and machine IDs.

## Race Design

### How do I create and save a custom race?

Read chapter 20, `Designing Custom Races`.

### Is there an ultimate race?

It depends on the type of universe and on the placement and experience of the other players. The manual says expert players can make almost any race into an "ultimate race," but that the same race might be completely ineffective in another game with a different mix of circumstances.

### Can I edit a race during play?

Once a game is started, you are stuck with the race you entered the game with.

All game files are compressed and encrypted to provide security for all players, so players cannot read or modify data files directly.

You can, however, open a saved race file, including one for a race currently in play, and edit it for future use. The manual suggests doing this when you discover weaknesses you want to correct before using that race again.

To edit a race, open the race file using `File (Open)`. See chapter 20, `Designing Custom Races`, for more information.

## While I'm Playing

### Can I design my own ship hulls?

You can design elaborate ship configurations, but you cannot design your own hulls. The manual describes this as a core game-balancing restriction.

### Can I use diplomacy in Stars!?

Stars! includes features for simple diplomacy in multiplayer games.

Use the `Message` pane to communicate with other players about alliances, rendezvous, trade agreements, and non-aggression pacts.

When setting up a game, you can also specify winning conditions that allow for multiple winners, which encourages diplomatic play. Stars! does not require a single winner.

You can declare players neutral or friendly in the `Player Relations` dialog. This helps prevent accidental attacks, allows you to come to a friend's aid automatically if they are under fire, and lets friends pass harmlessly through each other's minefields.

### How can I print out a star chart of the universe?

Use `File (Print Map)`.

## Glossary

### Added Cost of Research

The added cost of research represents the cost of factors such as diluting research effort across more than one field and the ramp-up time needed to enter a new field of study.

### AI

An AI is a computer player. AIs always exist in single-player games and can exist in multiplayer games if chosen.

### AIs and Advantage Points

Easy AIs receive substantially fewer advantage points than you do. Expert AIs receive more advantage points than you. Standard and Hard AIs fall somewhere in between.

### Annual Growth Rate

This rate is calculated by multiplying the habitability value by the `Maximum Colonist Growth Rate Per Year` shown on page 4 of the `View Race` dialog. For races with the `Hyper-Expansion` trait, the actual maximum colonist growth rate is twice the displayed value.

### Battle Speed

In computing movement in battle, the best speed for all engines is the figure for `120%` fuel usage.

### Best Warp Speed

This is the maximum warp speed that the engines on a ship design can achieve at `120%` normal fuel consumption or less. For Ramscoop engines, it is the maximum speed the engine can travel without using fuel. This number appears in the `Fleet Composition` tile for the selected fleet.

This speed applies only to travel between waypoints, not to battle.

### Capital Ship

A ship with a power rating of at least `2000`.

### Collateral Damage

Damage taken by the shields of targeted ships when torpedoes miss.

### Defenses and Invading Troops

Defense percentage values are based on an installation's effectiveness against bombs. Planetary defenses are `75%` effective against invading troops.

### Disengaging

The token attempts to get out of battle by jumping into hyperspace. It does not try to leave the square directly. Eventually it disappears from the board, which hopefully means it escaped instead of being "liberated to its component quarks."

### Energy Sources for Starships

Standard starship engines use anti-matter created at starbases, while Ramscoops gather fuel from the surrounding universe.

### Factory

Factories produce resources. Resources are units of work created by people and factories for use in production, research, and other tasks.

### Fibonacci Series

Fibonacci numbers are the endless sequence `1, 1, 2, 3, 5, 8, 13, 21, 34...`, where each term is defined as the sum of its two predecessors.

### Fleet Colors

A blue fleet belongs to you. A red fleet belongs to an opponent. A purple fleet indicates that both your fleet and an opponent's fleet are in the same, or nearly the same, location.

### Host File

`gamename.hst` is the file containing the information the host program needs for a specific game. This file should be available only to the host. If the file is password-protected, you will be asked for a password.

### Initiative

Initiative determines order of firing in battle. The ship with the highest initiative fires first.

### Load Optimal

This is a transport order that loads no more fuel than needed to reach the next waypoint. It can only calculate the amount of fuel needed for one waypoint and does not attempt to load enough fuel for later waypoints.

### Maximum Ship Designs and Ships

You may have `16` different ship designs at one time, and up to `32,000` ships of each design in a fleet.

### Mine

Mines bring minerals to the surface of your planets, where they are used in production.

### Mineral Alchemy

Mineral alchemy turns resources into minerals. One instance uses `100` resources to produce one `kT` of each mineral, or only `25` resources for players with the `Mineral Alchemy` trait. This item appears in the production inventory and can be automated through the production dialog's auto-build feature.

### Movement

Movement is battle speed, ranging from one-half square to two and one-half squares per round.

### Orbit Ring Colors

A white circle indicates that one or more of your fleets are in orbit. A red circle indicates one or more of an opponent's fleets. A purple circle indicates that both your fleets and an opponent's fleets are in orbit.

### Planet-Penetrating Scanners

These scanners can detect fleets in orbit around a planet and can also reveal planetary statistics from a distance.

### Player Log File

`gamename.mN` is the individual file for each player, where `N` is a number from `1` to `16` representing the player number. It contains the data about that player's race and the state of the empire at the beginning of a turn. Both the player and the host maintain copies of this file.

You can load the current turn by opening the `.m` file with your player number in the extension. If the file is password-protected, you will be asked for a password.

### Race File

`name.rN` is a race description file created and saved with the `Custom Race Wizard`. If you open it from `File (Open)`, the wizard opens so you can view or edit the race. If the file is password-protected, you will be asked for a password.

The `.r` extension is not required, so race files saved with other extensions can also be opened.

### Race Description File

This glossary also describes `NAME.RN` files as race description files created with the `Custom Race Wizard`. `N` can be any number, though the default is commonly `r1`. Opening the file through `File (Open)` launches the wizard so you can review or change the race's attributes.

The source appendix includes this duplicate entry in addition to `Race File`, so it has been preserved here as a separate glossary item.

### Rating

A ship's rating is a relative value of its offensive capability. Ratings are useful only for broad comparisons among similar ship designs when deciding which design might be more effective in battle.

### Resources

Resources are units of work created by people and factories. They represent the effort involved in performing a task or producing an item.

### Round of Battle

Battles last up to `16` rounds. One round of battle is every token getting a chance to move and fire. A round is broken into phases, where one phase is a single token moving and, if applicable, firing.

### Ship Classes

- Unarmed ships: any design with no weapons and no threat.
- Utility ships: unarmed ships that still pose a threat; a subset of unarmed ships.
- Scouts: ships based on the `Scout`, `Super Scout`, and `Destroyer` hulls.
- Warships: all other armed ships, including armed freighters.
- Bomber: any ship based on one of the `Bomber` hulls.

### Token

Each token is a stack of identical ships from a single fleet.
