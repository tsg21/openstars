# 17. Scanning and Cloaking

Scanners tell you about:

- planetary environments
- enemy fleets
- minefields
- mineral packets in transit
- salvage
- wormholes

Both planets and ships can have scanners. You initially create a planet-based scanner by adding it to your production queue. Afterward, the scanner is automatically upgraded as your technology improves. Ship-based scanners must be included in the hull design.

All fleets detected by your scanners appear in the Scanner pane. Fleets can use cloaking devices to reduce a scanner's effective range and increase the chances of escaping detection.

## Scanner Technology

Like all other technology, the science behind scanners and cloaking devices must be researched.

- Planet-based scanners are described in the `Planetary` category of the Technology Browser.
- Ship-based scanners are described in the `Scanners` category.
- Cloaking devices are described in the `Electrical` and other miscellaneous categories.

Alternate Reality races do not build planetary scanners. Scanning is an inherent ability of the population. To learn more about these unique beings, read Chapter 22, "Alternate Reality Races."

### Planet-Penetrating Scanners

These scanners can detect fleets in orbit around a planet. They can also tell you planetary statistics from a distance, such as mineral concentrations under the planet surface.

### Normal, Non-Penetrating Scanners

These scanners cannot penetrate a planet. Any object orbiting the planet is hidden from your radar. Minefields are cloaked 75% from this type of scanner.

### Scanners Are Additive

The formula for calculating a ship's scanner range is the fourth root of the sum of each scanner raised to the fourth power. For example, a ship design with two 100 light-year scanners and one 60 light-year scanner has this total scanner strength:

```text
(100^4 + 100^4 + 60^4)^(1/4) = 120 light years
```

The same calculation applies to planet-penetrating scanners.

### Minefields as Scanners

Minefields act as non-penetrating scanners for players with the `Space Demolition` primary racial trait. These scanners do not detect fleets orbiting planets.

### Scanners and Primary Traits

Some races have extra scanner technology.

- If you have chosen `Packet Physics` as your primary trait, all your mineral packets act as planet-penetrating scanners.
- If you choose `Space Demolition`, all your minefields act as normal scanners.

## Selecting Fleets in the Scanner Pane

Fleets in orbit are indicated by a circle around the planet. To select a fleet in orbit:

1. Right-click on the planet in the Scanner pane.
2. Select the enemy fleet from the pop-up list.

Follow the same procedure to select a fleet from a group in deep space.

If you own the ship, it appears in the Command pane.

### Estimated Path of Another Player's Fleet

Click an opponent's fleet in the Scanner pane to display its estimated path. The arrow points in the approximate direction of travel. Tick marks appear on the line indicating how far the fleet will move in a year at its current speed.

Since a fleet travels in a straight line from waypoint to waypoint, you can use this path to estimate the fleet's origin and destination.

Using the opponent's fleet summary and estimated path, you can guess at the activities your foe or friend is pursuing. For example:

- Attack fleets may indicate where you should prepare for battle or lay minefields.
- Scout, miner, or colonist fleets may reveal that player's current strategy and likely needs.

## Scanning Planets

When you scan an uninhabited planet, you can detect the environment and the concentration of each mineral under the planet surface, but not the minerals stored on the surface.

If you attempt to scan a planet inhabited by an opponent, you can detect only:

- the environment
- underground mineral concentration
- an estimate of the population, accurate to within plus or minus 20%

If the planet's starbase has cloaks, the distance at which you can detect the enemy starbase is reduced.

## Cloaking

Cloaking devices reduce your opponent's effective scanner range when detecting your cloaked fleet or planet. Cloaking devices do not make a fleet or planet invisible: no matter how strong the cloak, the object will always be visible to another fleet at the same location.

Cloaking reduces your opponent's scanner range by a specific percentage. The higher the percentage, the more the range is reduced. The maximum amount of cloaking possible is 98%, reducing your opponent's scanner range by 98%.

Cloaking is shared by the entire fleet. The cloaking percentage of a fleet is displayed in the Fleet Composition tile, except when in small-screen mode.

Uncloaked ships are also hidden in a cloaked fleet, although they reduce the fleet's overall cloaking percentage.

### Advantage of a Second Cloak

Cloaks are additive. Additional cloaks reduce your fleet's visibility further.

### Types of Cloaks

There are several types of cloaking devices. If your race uses the `Super Stealth` primary trait, you also have access to:

- cloaked armor: `Depleted Neutronium`
- a cloaked shield: `Shadow Shield`
- a ship-based cloaked scanner: `Chameleon`

Multiple cloaks on the same ship can all be of the same or different strengths.

### Cloaked Starbases

Adding cloaks to a starbase hull cloaks only the starbase, not the planet.

## Detecting Opponents' Fleets

Having scanners on as many planets as possible reduces the chance that cloaked fleets will sneak past. For example, if your opponent has 75% cloaking and your scanners normally detect fleets at a range of 200 light years, your effective scanning range is reduced to 50 light years.

If your scanners are close together, whether planet-based, ship-based, or a combination of both, you can create a gauntlet that opponents' ships are less likely to pass through undetected.

For a description of how cloaking is calculated, read Chapter 24, "The Guts of Cloaking." To learn more about a specific cloak, open the Technology Browser with `F2` and view the `Electrical` category or the appropriate category for devices with secondary cloaking attributes.

Also consider placing sentry ships at uninhabited planets along your border. They help prevent unseen planet-hopping by your opponents. Even if a ship is cloaked, you will still detect it when it passes by.

The X series of planet-based scanners and certain ship-based scanners can detect both fleets in deep space and fleets in orbit. Both ranges are affected by cloaking. For example, if you are using a `Snooper 250X` planet-based scanner against a 75% cloak, the scanner has effective ranges of 62 light years and 31 light years. If the ship is in orbit of a planet 32 light years away, you will not see it.

With the Scanner's Radar Overlay turned on, check for gaps in your coverage if each scanner only sees part of its usual range. Adjust the percentage to estimate your coverage against opponents with different cloaking strengths. For example, select `75%` to show how close a fleet with 25% cloaking must be before you can detect it.

Keep in mind that a cloak only reduces a scanner's effectiveness in detecting the cloaked fleet. It fools the scanner rather than physically changing it.

### Tachyon Detector

You must have the `Inner Strength` trait to use this device.

Each `Tachyon Detector` reduces the effectiveness of another player's cloak by 5%. The reduction is only seen by the fleet carrying the detector. The effect of multiple detectors is additive. For example, if a fleet has two detectors, the first lowers the effectiveness of the opponent's cloak to 95%, and the second reduces that 95% by almost another 5%, down to 90.2%.

This makes it significantly harder for enemies to sneak past fleets carrying the device, making it useful for ships on regular patrol duty.

When you add a `Tachyon Detector` to a hull design, the Ship and Starbase Designer displays the other player's cloaking effectiveness on the design's scanner information line.

## Pirating Using Stealth-Based Scanners

You need the `Super Stealth` primary race trait and a fleet with the `Pick Pocket` or `Robber Baron` scanner to steal cargo from an opponent's hold.

1. Set the opponent's fleet as a waypoint.
2. Set the `Transport` order to `Load` the amount you want to steal.

The theft takes place as soon as your pirate fleet reaches its victim.

You can steal only cargo, not fuel or colonists.
