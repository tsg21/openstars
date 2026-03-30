# 20. Designing Custom Races

The Custom Race wizard allows you to create, save, and edit player races. Here you define a race's strengths and weaknesses. The trick lies in balancing advantages with disadvantages to produce a race that makes the best use of advantage points, the game's units of primordial ooze.

## Opening the Wizard

Open the `Custom Race wizard` from the `File` menu, or from the basic or advanced new-game dialogs. You can also open an existing race for editing by choosing `File` -> `Open` and selecting the race file.

## Advantage Points

In each step, the box in the upper-right corner of the dialog shows the current number of unused advantage points.

Each advantage reduces the number. Slight advantages cost a few points; powerful ones cost many. Before you finish, the total must be zero or higher. If it becomes negative and turns red, you need to add disadvantages to bring the race back into legal range.

Choose race attributes carefully. Once the game begins, you can view your race characteristics, but you cannot change them.

## Step 1: Basic Race Definition

### Race Name and Password

Name your race and, if you wish, choose a password. The password selected when a race is created is attached to the race file. Although you may change the password during a game, that change applies only to the current game. Opening the race file for another game still requires the original password.

You also need the password to view or edit the race file. You can specify the race name only here in step 1.

### Predefined Races

Selecting a predefined race automatically presets all of the options in steps 2 through 6. Choosing one does not lock those options; predefined races are provided as time-savers and examples of different play styles.

To use a predefined race as a starting point:

1. Select each predefined race in turn.
2. Use the `Back` and `Next` buttons to step through the wizard and note the settings.
3. Return to step 1 and select the race that looks best for your purposes.
4. Fine-tune that race using as much of the wizard as necessary.

Read more about the predefined races in chapter 21.

### Other Basic Definition Options

#### Leftover Advantage Points: Surface Minerals

You get `10kT` of surface minerals for each leftover advantage point. For example, `20` unused points yields `200kT` of minerals. Stars! weights the distribution in favor of the rarest minerals. These minerals are available immediately.

#### Leftover Advantage Points: Mines

You get one additional mine for every two leftover advantage points. These mines are available immediately.

#### Leftover Advantage Points: Factories

You get one additional factory for every five leftover advantage points. These factories are available immediately.

#### Leftover Advantage Points: Defenses

You get one additional defense installation for every ten leftover advantage points. These defenses are available immediately.

Choosing the mines, factories, or defenses options has no effect on Alternate Reality players and wastes advantage points.

#### Leftover Advantage Points: Mineral Concentration

The concentration of the mineral on your home world that would otherwise be poorest is improved by `1%` for every three leftover advantage points. Increasing the concentration improves the mining rate, although mining still reduces that concentration over time.

### Race Emblem

Select a race emblem from the collection. This emblem identifies your fleets when they are displayed in the Selection Summary pane. In a multi-player game you may not get the emblem you select if another player chooses the same one first.

## Step 2: Primary Trait

Choose the major characteristics for your race. Each primary trait gives you a distinct and powerful set of strengths, technologies, and limitations.

### Hyper-Expansion Trait

#### Starting Advantages

- growth rate is twice the value shown on step 4 of the Custom Race wizard
- one armed scout
- three mini-colony ships

#### Exclusive Hulls

- Mini-Colonizer hull
- Meta Morph hull, which is completely flexible

#### Exclusive Engines

- Settler's Delight engine: warp 6 for free, but only for the Mini-Colonizer hull

#### Exclusive Components

- Flux Capacitor, which increases the damage done by all beam weapons on Hyper-Expansion ships by `20%`

#### Limitations

- cannot build stargates
- maximum population is limited to what the planet would normally support for a race with your environment requirements

### Super-Stealth Trait

#### Starting Advantages

- tech level 5 in Electronics
- one scout
- one colony ship

#### Exclusive Hulls

- Rogue hull
- Stealth Bomber hull

#### Exclusive Components

- Pick Pocket scanner, which sees enemy fleet cargo in the same location and lets you steal it using the cargo gauge and transfer dialog
- Chameleon scanner with a scanning range of `160|45` plus a `20%` cloak
- Robber Baron scanner, which sees enemy fleet cargo and enemy planet surface minerals
- Shadow Shield with strength `75` plus a `35%` cloak
- Depleted Neutronium with armor strength `200` plus a `25%` cloak
- `75%` Transport Cloak
- `85%` Ultra-Stealth Cloak

#### Exclusive Abilities

- all ships and starbases built by Super-Stealth races have an inherent `75%` cloak
- gain research by spying and combining it with your own research, receiving resources in each field equal to the average spent in that field by all races, including yourself, while at least one other race exists

### War Monger Trait

#### Starting Advantages

- tech level 5 in Weapons
- tech level 1 in Propulsion and Energy
- one armed scout
- one colony ship

#### Exclusive Hulls

- Battle Cruiser hull
- Dreadnought hull

#### Exclusive Weapons

- Gattling Neutrino Cannon
- Blunderbuss

#### Exclusive Abilities

- square movement bonus in battle
- colonists attack better
- all weapons cost `25%` less to build
- learns the exact design of enemy ships as soon as they are scanned

#### Limitations

- cannot build mine layers or lay minefields
- can build `SDI` or `Missile Battery` defenses only

### Claim Adjuster Trait

#### Starting Advantages

- tech level 1 in Energy, Weapons, and Propulsion
- tech level 6 in Biotech
- a ship capable of terraforming other players' planets from orbit

#### Exclusive Components

- Retro Bomb, which de-terraform planets
- Orbital Adjuster, which modifies another player's planetary environment from orbit

#### Exclusive Weapons

- bombs that de-terraform worlds

#### Exclusive Abilities

- terraforming is free, but temporary
- each year, all planets you own are terraformed to the limit of your terraforming technology
- a planet reverts to its original condition if it is abandoned or captured by another player

### Inner-Strength Trait

#### Starting Advantages

- one scout
- one colony ship

#### Exclusive Hulls

- Super Freighter hull
- Fuel Transport hull

#### Exclusive Components

- Croby Sharmor: shield strength `60` plus `65dp` as armor
- Fielded Kelarium: armor strength `175` plus `50dp` as shield
- Speed Trap 20 mines, which stop fleets cold
- Jammer 10 and Jammer 50, which deflect torpedoes
- Tachyon Detector, which reduces the effectiveness of other players' cloaks by `5%`

#### Exclusive Weapons

- Mini Gun: power `13`, range `2`, sweeps mines at `208/year`

#### Exclusive Abilities

- colonists defend better
- ships heal faster
- planetary defenses cost `40%` less
- colonists on freighters reproduce at their maximum rate and beam down excess population when orbiting a planet you own

#### Limitations

- weapons cost `25%` more than they do for other races
- no Smart, Neutron, Enriched Neutron, Peerless, or Annihilator bombs

### Space Demolition Trait

#### Starting Advantages

- tech level 2 in Propulsion and Biotech
- one scout
- one colony ship
- two mine layers, one standard and one speed trap

#### Exclusive Weapons

- Mine Dispenser 40, 80, and 130 for standard mines
- Heavy Dispenser 50, 110, and 200 for more serious firepower
- Speed Trap 20, 30, and 50 mines, which stop fleets cold

#### Exclusive Hulls

- Mini Mine Layer hull
- Super Mine Layer hull

#### Exclusive Abilities

- minefields act as non-penetrating scanners, and cloaks work as an absolute percentage against mine scans
- can travel through opponents' minefields at two warp speeds faster than the limit stated in the Technology Browser
- can remotely detonate standard minefields
- minefields decay at a rate of `1%` a year per planet enclosed in the field; all other players' fields decay at `4%` a year per planet enclosed
- learns the exact design of any enemy ship that detonates one of your mines

### Packet Physics Trait

#### Starting Advantages

- tech level 4 in Energy
- two shielded scouts
- one colony ship
- two starting planets in non-tiny universes

#### Exclusive Components

- Mass Driver 5, 6, 8, 9, 11, 12, and 13
- mineral packets with built-in penetrating scanners, with a range equal to the square of their warp speed
- Energy Dampener, which slows all ships in combat by 4 initiative points

#### Exclusive Abilities

- mineral packets are smaller and cheaper to build
- senses all players' mineral packets in flight, regardless of location
- learns the exact design of any enemy starbase that uses a mass accelerator to receive one of your packets
- planets receiving mass packets have a `50%` chance of a `1%` improvement in an environmental attribute
- for every `100kT` of a mineral not caught, there is also a `0.1%` chance that the overall planet value improves by `1%`

#### Limitations

- mineral packets do only one-third normal damage

### Interstellar Traveler Trait

#### Starting Advantages

- two planets with `100/250` stargates in non-tiny universes only
- tech level 5 in Propulsion and Construction
- one scout
- one colony ship
- one destroyer
- one privateer

#### Exclusive Hulls

- stargates with unlimited range and capacity

#### Exclusive Components

- Anti-matter Generator, which acts as a `200mg` anti-matter fuel tank and generates `50mg` of fuel each year

#### Exclusive Abilities

- can transport minerals and colonists in fleets through stargates, with cargo weight ignored when checking gate limits
- exceeding stargate safety limits is less likely to kill your ships
- stargates cost `25%` less
- stargates reveal planetary statistics on all other planets with stargates in range

#### Limitations

- mass drivers are only half as effective at catching minerals as their rating
- mass drivers are less efficient at flinging minerals
- all mineral packets you fling decay regardless of speed

### Alternate Reality Trait

#### Exclusive Hulls

- Death Star, the largest starbase hull ever known

#### Exclusive Components

- Orbital Construction Module, which contains viral weapons capable of killing 2000 enemy colonists per year and colonizes worlds by transforming into an Orbital Fort

#### Exclusive Abilities

- lives on starbases only, not planets
- starbases are `20%` cheaper to build, non-cumulative with `Improved Starbases`
- population acts as natural miners and scanners
- can remote-mine own planets because the race lives in orbit
- maximum population is determined by starbase size, not planet size
- planetary resources grow as Energy tech level increases

#### Limitations

- cannot build planetary installations
- interstellar travel kills `3%` of any colonists in the fleet each year

### Jack of All Trades Trait

#### Starting Advantages

- tech level 3 in all fields
- two scouts
- one colony ship
- one medium freighter
- one mini miner
- one destroyer

#### Exclusive Components

- Scout, Frigate, and Destroyer hulls get a built-in scanner with a range equal to `2x / x` light-years, where `x = 10 * Electronics Tech level`

#### Exclusive Abilities

- improves all `Costs 75% Extra` fields to tech level 4 if the box in step 6 is checked

## Step 3: Lesser Traits

Specify or view the lesser traits for your race. Several traits may not change your overall strategy very much. Every time you choose a trait that prevents development of something, you gain advantage points to use elsewhere or to bring the race back to zero or better.

Select lesser traits that complement the profile chosen in step 2.

### Improved Fuel Efficiency Trait

Your ships burn `15%` less fuel than their drive specifications indicate. The `Fuel Mizer` and `Galaxy Scoop` engines also become available. This trait also increases your starting Propulsion tech by one level.

### Total Terraforming Trait

You begin the game able to adjust each environmental attribute of a planet by up to `3%` in either direction. Throughout the game, additional terraforming technologies unavailable to other players become available, up to `30%` terraforming. Total Terraforming requires `30%` fewer resources.

### Advanced Remote Mining Trait

You get three additional mining hulls and two new robots. You start the game with two Midget Miners.

### Improved Starbases Trait

You get two new starbase designs. The `Space Dock` hull allows starbases to build small and medium ships. The `Ultra-Station` is much larger than a standard starbase. Your starbases are automatically cloaked by `20%`, and they cost `20%` less to build.

### Generalized Research Trait

Your race takes a holistic approach to research. Only half of the resources dedicated to research are applied to the current field. `15%` of the total is applied to each of the other fields. Yes, that adds up to `115%`.

### Ultimate Recycling Trait

When you scrap a fleet at a starbase, you recover `90%` of the minerals and `70%` of the resources used to produce the fleet. Those resources are available for use the next year. Scrapping at a planet gives you `45%` of the minerals and `35%` of the resources.

These resources are not strictly additive. The number a planet receives is determined by this formula:

```text
Resources = (Current_production x Extra_resources) /
            (Current_production + Extra_resources)
```

This formula is true whether or not a planet has a starbase.

### Mineral Alchemy Trait

You can turn resources into minerals more efficiently. One use of Mineral Alchemy consumes `25` resources to produce one `kT` of each mineral. Without this trait, it takes `100` resources to produce one `kT` of each mineral.

### No Ramscoop Engines Trait

You cannot build the `Radiating Hydro-Ram Scoop`, `Sub-Galactic Fuel Scoop`, `Trans-Galactic Fuel Scoop`, `Trans-Galactic Super Scoop`, `Trans-Galactic Mizer Scoop`, or `Galaxy Scoop`. You can build the `Interspace-10` engine, which can travel at warp 10 without taking damage.

### Cheap Engines Trait

Pro: engines cost `50%` less to build.

Con: your ship engines are less reliable. When attempting to travel above warp 6, there is a `10%` chance the engines refuse to engage.

### Only Basic Remote Mining Trait

You do not get the `Robo-Miner`, `Robo-Maxi-Miner`, or `Robo-Super-Miner` robots.

### No Advanced Scanners Trait

You do not have the standard scanners that can scan planets from a distance and see fleets hiding behind planets. All ranges for conventional scanners are doubled.

### Low Starting Population Trait

Instead of `25000` people, you start with `17500`, or `30%` fewer. It takes a long time to overcome a lower starting population. A high growth rate helps, but even then it can be painful.

### Bleeding Edge Technology Trait

New technologies initially cost twice as much to build. As soon as you exceed all of the tech requirements by one level, the cost drops back to normal. Miniaturization happens at `5%` per level up to `80%`. Without this trait, miniaturization happens at `4%` per level up to `75%`.

### Regenerating Shields Trait

All shields are `40%` stronger than their listed rating. Shields regenerate at `10%` of maximum strength after every round of battle. All armors operate at `50%` of rated strength.

## Step 4: Population Growth Factors

Use this step to specify your race's habitable range and optimum growth rate.

### Growth Conditions

Use this step to define how well your race tolerates gravity, temperature, and radiation. Tolerances are set separately for each environmental factor.

The width of the colored bar represents the extent of the habitable range. Its width and position determine the extremes of the habitable range. The numbers to the right of the bar show the extremes in gravities (`g`), degrees Celsius (`C`), or millirads (`mR`).

Your race grows only on planets whose conditions fall within those habitable ranges. On planets outside the habitable range, colonists die each year because of the unbearable conditions.

Gravity and temperature are chosen randomly, but slightly weighted toward values near the middle of the spectrum. If you move the colored bar away from the center, advantage points increase to compensate for the smaller number of habitable planets you will encounter. Radiation is chosen completely at random.

### Adjusting the Habitable Range

Click and hold the colored bar to drag the entire range left or right. Clicking while holding `Shift` moves the range in steps.

The range can also be narrowed or widened. Holding `Shift` while doing so changes the range in `20%` increments.

### Choosing an Extreme Range

Cons:

- the more extreme your habitability range, the more planets fall outside your habitable and terraformable range

Pros:

- you gain advantage points back
- planets with environments near the ends of the spectrum have a good chance of being super-rich in one or more minerals

For example, a planet with a flesh-searing radiation extreme of `97mR` could easily have four times the concentration of each mineral compared with a mild-mannered vacation world.

### Immunity

Selecting the `Immune to Radiation` checkbox lets you ignore an environmental factor. This is expensive and usually requires many disadvantages to bring the advantage-point total back above zero. Once immunity is selected, the habitable range for that factor becomes irrelevant and disappears.

If you select any kind of immunity, you may not want to spend points on the `Total Terraforming` advantage. Once the game begins, you can research terraforming technologies only for environmental factors that can affect you. If you are totally immune, you never need to terraform.

Immunity is different from simply expanding the habitable range to fill the entire spectrum. Immunity treats every point in the spectrum as `100%` ideal. A range widened to fill the spectrum still treats only the midpoint as `100%` ideal, and the edges of the range as `0%` ideal.

### Maximum Population Growth

Set the maximum colonist growth rate between `1%` and `20%` per year. Colonists grow at that full rate only if the habitability value is `100%`. If habitability is lower, the growth rate falls proportionally.

The source scan includes a broken in-game example for the planet `Demski` and an accompanying pop-up image. Those fragments have been omitted here because the OCR text is incomplete and does not survive cleanly.

## Step 5: Population Efficiency

Use this step to specify the efficiency of your colonists, mines, and factories on the planets you inhabit.

If you are unsure whether increasing or decreasing a value is an advantage, watch the advantage-points box in the upper-right corner of the dialog. If the number decreases when you change a setting, you have given the race an advantage.

If you choose the `Alternate Reality` primary trait, most of these controls are disabled because Alternate Reality races cannot build planetary installations.

### Sample Strategies

If your race has a high population growth rate, you may not care about factory efficiency. In that case, you can configure your colonists to produce fewer and more expensive factories, freeing advantage points to spend elsewhere.

If you do not plan to build many mines, or if you have extra advantage points, consider increasing the mining production rate. This does not change how quickly mineral concentration is reduced on a planet. It only improves how efficiently you extract minerals from the rock. This can give you an advantage over a player who runs more mines but extracts less efficiently, because they reduce concentration faster.

The rate at which mineral concentration decreases, always stopping at `1`, is determined by the number of mines on a planet and the number of years they have been in existence.

Keep in mind that when mineral concentrations on both your planets and your opponent's planets reach `1`, the player with more mines can perform as well as, and possibly better than, the player who is highly efficient at extraction. If you are strong at production and generate many resources, you may also find that `Mineral Alchemy` compensates for low mineral concentrations.

These are only simple examples of possible strategies. Make the choices that suit your game best, while keeping the mineral depletion rules in mind.

Next you specify the research cost profile for your race.

## Step 6: Research Costs

Use this step to specify how efficiently your scientists use planetary resources for research. Changes are reflected immediately in the advantage-points box.

Selecting `Costs 75% Extra` increases the available advantage points.

Selecting `Costs 50% Less` decreases the available advantage points.

If you check `All 'Costs 75% Extra' Research Fields Start at Tech 3`, then it becomes advantageous to mark as many fields as sensible as `Costs 75% Extra`, because this option costs a flat fee.

If you have chosen the `Jack of All Trades` primary trait, this benefit becomes `...start at Tech 4`.

## Finish

When you finish, Stars! asks you to save the race to a file and suggests the `.r1` extension. This is only a default. You can name a race file anything you wish. If you are editing an existing race, Stars! asks whether to save it using the current file name or a new one.
