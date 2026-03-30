# 6. Planets

Planets are the gold nuggets of the Stars! universe: everybody wants them, and hardly anyone wants to share. Green worlds give your people a place to grow, learn, and produce. The minerals in each planet provide the building blocks for all the technology you create, including planetary installations such as defenses and scanners, as well as starbases with stargates and mass drivers.

When you click on a planet in the Scanner, you're actually selecting a star system. The planet that appears on your screen is the most desirable planet in that system. There may be lesser rocks in the system too, but you usually won't want them. If you colonize a planet, it becomes your capital world in that system, the local center of government and industry. If the planet is dangerous to your people, you can mine it from orbit and ship its valuable minerals to other parts of your empire. If the planet is inhabited by another player, you can try to take it away. If the owner is another human, you can also try to establish trade relations.

No matter how you play, you need to give your people room to grow. That growth rate will vary on any given planet, depending on the levels of gravity, temperature, and radiation. You can create a race that is immune to one or more of these environmental factors, though that is a very expensive advantage. You can also make a planet's environment more hospitable by terraforming.

## Your Home World and Other Inhabited Planets

You start the game on your home world, a place with optimal environmental conditions where you have a small but thriving population, basic industry in the form of factories and mines, fundamental technology, and a short-range planet-based scanner. In orbit, you have a starbase capable of building ships and providing a small amount of planetary defense.

Each player's home world, whether it belongs to a computer AI or a human, starts out with these same items. When you colonize another planet, you can build these and other items as your resources and technology allow.

All planets contain minerals. All home worlds start with the same surface mineral content, adjusted to even out any advantages or disadvantages provided by racial attributes. If your home planet has a serious lack of a specific mineral on its surface, then your opponents are initially faced with the same problem.

Resources are units of work created by people and factories. They represent the effort involved in performing a task or producing an item.

All the information about a planet you own and the controls you use to give orders to that planet are available in the Command pane. The Selection Summary shows the gravity, temperature, and radiation levels of a planet, as well as the rate at which your population will grow. Environmental conditions on your home world are optimal for your species.

To learn about the Command pane and other parts of the Stars! screen, read chapter 5, The Stars! Screen.

### Abandoning a Planet

When you abandon a planet, the starbase and all installations on that planet are destroyed automatically.

## Population

People, along with factories, create the resources you need to build your empire. The more people you have, the more resources you have, and the faster you'll get things done.

Your maximum population on a planet is based on the planet's habitability value. When you select a planet in the Scanner, its value appears in the Selection Summary. The first number is the current value. The number in parentheses is the value after terraforming.

To see how many colonists it takes to produce one resource per year, use `View (Race)` and turn to page 5 of the View Race dialog.

The higher the percentage, the more people the planet will support. A negative value tells you the percentage of population the planet will kill if you colonize under the current environmental conditions. For example, a planet with an optimal value of `100%` may fully support `1,000,000` people. A planet with a value of `50%` can support only `500,000` people. A planet with a value of `-9%` will kill `0.9%` of the colonists on that planet each year.

All planets with a positive value of less than `5%` are treated as `5%` planets when determining the maximum supportable population.

### Annual Growth Rate

This rate is calculated by multiplying the habitability value by the Maximum Colonist Growth Rate Per Year found on page 4 of the View Race dialog. For races with the Hyper-Expansion trait, the actual maximum colonist growth rate is twice that displayed.

### Alternate Reality Races and Population

Since Alternate Reality races live on starbases, they use a different population model. Read more about them in chapter 22.

### Growth Rate

The habitability value also determines your population's annual growth rate. Left-click on the value to display the current growth rate, as well as the total number of people the planet will support based on current environmental conditions. The growth rate is shown as "up to n%" because the rate slows as the population approaches the maximum. Population growth begins to plateau after the planet reaches `25%` capacity.

### Maximum Population

The maximum population on an optimal planet, for all races but two, is `1,000,000`.

Hyper-Expansion races grow fast but are limited to one-half the typical maximum population: `500,000` on an optimal world. Jack-of-All-Trades races receive a maximum population that is `20%` greater than normal. Under optimal conditions, a Jack-of-All-Trades world supports up to `1,200,000` people.

Races with the Only Basic Remote Mining trait receive an additional `10%` increase beyond their normal limit. For example, the maximum population for a Jack-of-All-Trades race with Only Basic Remote Mining is `1,320,000` under optimal conditions.

### Overcrowding

The number of people between `100%` and `300%` population capacity work at `50%` efficiency. Any population in excess of `300%` capacity can perform no useful work whatsoever.

Deaths from overcrowding reach an annual maximum of `12%` at `400%` capacity.

### Killer Planets

Planets with negative habitability values kill colonists. The annual death rate is calculated as:

```text
Habitability Value / 10 of the colonists on the planet each year
```

For example, a planet with a habitability value of `-10%` inhabited by `2000` colonists will kill `1%`, or `20` colonists, per year.

If you terraform the planet after colonizing, your people will continue to die until environmental conditions become favorable, meaning the value becomes `0%` or positive.

### Claim Adjuster Races and Negative Planets

If your race has the Claim Adjuster trait, your colonists automatically terraform your new planet to the best of their abilities the first year it is colonized.

## Minerals

All planets contain three important raw minerals: Ironium, Boranium, and Germanium. These provide the building blocks for almost everything your race produces. Minerals exist both on and under the planet's surface. Minerals found on the surface can be used immediately in production. Those under the surface must be mined to become available for use.

Minerals can be transported to other planets where they're needed using freighters and mass drivers. Minerals can also be created through a production-based recycling effort called Mineral Alchemy. You also receive minerals when you initially colonize a world, automatically scrap a colonizing vessel, or scrap a ship at a planet you own.

The Selection Summary pane shows the surface mineral supply, the concentration of minerals under the surface, and the mining rate for the selected planet. Each mineral is represented by a colored bar:

- The bright bar shows how much of the mineral is on the surface and ready to use.
- The dark bar shows the amount that will be mined next year.
- The diamond shows the current mineral concentration, measured from `0` to `200` units.

The width of the graph is `100`, with a plus sign appearing if the concentration exceeds the current scale. If you are scanning the planet but don't own it, you see only the mineral concentration. You see all mineral information as soon as you colonize the planet.

If your race possesses the Mineral Alchemy trait, you can transform existing resources into minerals four times faster than races without this advantage.

You can also obtain mineral information from the Minerals on Hand tile when you are commanding the planet.

Left-click on a bar to display the exact quantity, concentration, and mining rate for that mineral.

The mineral concentration on your home world never drops below `30`. This world always retains this advantage, regardless of who occupies it during the course of play.

## Mines

Mines extract minerals from the planet. As you mine, you decrease the concentration of minerals under the surface, adding them to the supply on the surface and making them available for immediate use. You never run out of minerals on a planet; you only decrease the concentration until it reaches `1`, when it becomes difficult to extract more than tiny amounts from each mine each year.

You can build mines on any planet you inhabit or use robot miners on uninhabited planets.

## Factories

Factories, along with people, create resources used to build items such as ships, mines, defenses, and more factories. Resources are also required to research new technologies. In general, any task that requires mental or physical effort requires resources.

You do not need factories in order to build things. Factories only increase the total number of resources you receive each year. For a typical race, you can double the number of resources generated per year by building factories. Think of factories as virtual colonists. Once built, they produce work and consume nothing. Factory resources not used for production are directed into research.

Factories cost `4 kT` of Germanium to build or, if you selected `Factories Cost 1 kT Less` when defining your race, `3 kT` of Germanium. No minerals other than Germanium are used.

The Minerals on Hand tile shows you the current number of mines and factories operating on a planet, and the maximum number of mines and factories the current population can operate.

### Alternate Reality Races and Factories

Alternate Reality races cannot build factories or any other planetary installation.

To learn how many resources a factory will produce for your race, and the cost of building a factory, select `View (Race)` and turn to page 5 of the View Race dialog.

## Building Planetary Defenses

Defenses partially protect a planet from bombs, incoming mineral packets, and invasion. Unless you are playing an Alternate Reality race, you should always build defenses, especially in a single-player game. AIs love to bomb planets. While you can't build a perfect planetary defense system, you can significantly reduce the number of bombs, mass packets, and invading colonists that make it to the surface.

Whether you build defenses in a multi-player game depends on how much you can trust other players to leave your worlds in peace.

While you can build as many defenses as you wish, you can operate only as many as your population has resources to handle. When commanding a planet, look at the Status tile to see the current and maximum number of defenses, the type of defenses deployed, and the percentage of bombs and invading colonists that can be stopped.

As a game progresses, you can increase the number of defenses and upgrade the technology and efficiency of existing defenses.

Adding defenses increases the number of existing defenses of the type you're currently employing. For example, if you're using Missile Batteries, then adding `Defenses` to the production queue causes more Missile Batteries to be built. This increases the percentage of coverage.

Upgrading defenses happens automatically. Whenever you learn new technology that applies to defense, all defenses on all your planets upgrade automatically and at no cost.

### Alternate Reality Races and Planetary Defenses

Alternate Reality races cannot build planetary defenses or any other planetary installation.

To learn about defense technology, open the Technology Browser by pressing `F2`, choose `Planetary` from the dropdown menu, then click `Next` until the browser displays defense technology.

For more information on how planetary defenses help protect you from mineral packet attacks, read chapter 25, The Guts of Mass Drivers.

## Planet-Based Scanners

A scanner is the inhabited planet's radar, giving you information about all objects within scanner range. There are several types of planet-based scanners, with different ranges for detecting fleets, mass packets, minefields, and wormholes, and different ranges for detecting the environment and mineral content of other planets. You start the game with a basic scanner on your home planet.

The cost of building a scanner is fixed. Once you build a scanner, it will automatically be upgraded when your research allows you to build a better scanner.

A planet's scanner type and range appear in the Status tile.

Planet-based scanners are useful for detecting opponents' fleets that pass near or enter your empire. Only fleets that are cloaked have a chance of escaping detection. You can reduce the chances of fleets sneaking past if you place scanners on all your planets. When you select an enemy fleet, the scanner will also show the estimated path of the fleet.

To view the area covered by your scanners, select the Scanner pane's Radar overlay. Your basic radar coverage appears in red. Planet-penetrating radar coverage appears in yellow. You can also adjust the displayed effective coverage to different percentages, showing your vulnerability to cloaked fleets. Changing the displayed coverage does not actually decrease the effectiveness of your scanners. It merely shows you how effective they would be against other players' cloaks. For example, if you believe your enemy is using `80%` cloaked ships, it would be informative to set your displayed scanner coverage to `20%`.

### Alternate Reality Races and Planetary Scanners

Alternate Reality races cannot build planetary installations. Read chapter 22 to learn how they perform scanning.

## Starbases

A starbase can be an orbiting shipyard, fuel depot, defensive station, and a platform for a stargate and mass drivers. Before a planet can build ships, it must have a starbase with a space dock. Starbases stand in the way of attacks against the planet: your fleet must destroy the starbase before bombing can commence. Starbases with weapons always strike back and can initiate attacks against enemies in orbit.

A starbase can also carry cloaks and thus can partially cloak itself from remote scans. Cloaking a starbase does not cloak the planet.

You can find details on a specific starbase hull design in the Technology Browser. Press `F2`, click on the dropdown list, and choose the `Starbase Hulls` category.

### Alternate Reality Races and Starbases

Alternate Reality races live in orbit on starbases. This means that the starbase also determines a planet's maximum population, and gives Alternate Reality races greater incentive to protect their orbiting homes.

Your starbase is your primary defense against bombing and invasion by enemy fleets. Your planet cannot be bombed or invaded as long as your starbase still exists.

In the Scanner pane, a starbase appears as a yellow dot in orbit if a space dock is present, or a blue dot if no space dock is present. The Starbase tile describes a starbase belonging to the planet you're commanding.

### Building a Starbase

Build a starbase by adding it to the production queue. Like a ship, cost depends on the type and number of items attached to the hull. Starbase hulls are very expensive, but hull parts attached to a starbase are `50%` cheaper than the same parts attached to ship hulls.

A planet can have only one starbase at a time. An existing starbase can be upgraded or replaced, with credit given for recycled materials.

You'll have access to additional starbase hulls if you have the Improved Starbases trait.

### Starbase Design

There are five starbase hulls, with slots for weapons, armor, and other items:

- `Orbital Fort`: No ship building or refueling capacity. These don't count as starbases in the score.
- `Space Dock`: Ship building capacity for `200 kT` or smaller ships. This hull requires the Improved Starbases trait.
- `Space Station`: Unlimited ship building capacity.
- `Ultra Station`: Unlimited ship building capacity, with more slots for weapons, shields, and other components. This hull requires the Improved Starbases trait.
- `Death Star`: Top-of-the-line orbital habitat for Alternate Reality races.

### Upgrading a Starbase

You can upgrade a starbase by changing the hull or by adding or changing items in the hull slots. You receive full credit for the existing installation, paying only the difference between the old and new hulls. The upgrade appears in the production inventory, ready for you to add to the production queue.

Here is how the cost is determined:

- If the hull changes, you receive a `50%` credit for minerals and resources used in the original starbase.
- If the hull does not change, slots where the components don't change are free.
- Slots where only the count of the component increases cost only the component price multiplied by the number of additional items.
- Slots where the component type changes to a similar component are discounted in cost based on the closeness of the part types.
- Slots where the component type changes dramatically cost the full price of the new component. You receive some minerals back if the old components are recycled.

### Sorting Starbases for Easy Upgrades

1. Press `F3` to open the Planet Summary Report, then maximize the report window.
2. Click on the top of the `Starbase` column and select the starbase sort order.
3. Find the first planet with a starbase design you want to upgrade.
4. Click on the `Production` column for that planet. The Production dialog opens, showing the queue for that planet.
5. In the Production dialog, double-click on the new design listed in the production inventory.
6. Click on `Next`. Notice that the `Next` and `Prev` buttons follow the sort order of the report.
7. Keep adding upgrades for each planet until you've upgraded all your starbases.
8. Close the Production dialog and the report.

## Stargates

Stargates are starbase installations that provide cargo-less ships with fuel-free, single-year transport between your planets. This is the optimum way to move scouts and warships when you're in a hurry, or any other ship that isn't carrying anything but fuel.

In the Scanner pane, the stargate appears as a green dot orbiting the planet.

### Building a Stargate

A stargate occupies an Orbital slot in a starbase hull. You can add a stargate by upgrading an existing starbase hull or building a new hull.

To upgrade a hull and add the gate:

1. Choose `Commands (Ship Design)` to open the Ship and Starbase Designer.
2. Under `Design`, click on `Starbase`.
3. Select the design you wish to upgrade from the dropdown.
4. Click on `Copy Selected Design`.
5. Select a hull picture using the arrows under the picture and type in a new name, or use the defaults shown in the dialog.
6. Drag the stargate from the component list to an Orbital slot in the design. Subtract and add any other components as you wish.
7. Click on `OK`, then click on `Done` to close the dialog.
8. Click on `Change` in the Production tile, and add the new starbase to the planet's production queue.

### Interstellar Travelers and Stargates

For Interstellar Traveler races, starbases with stargates scan any planet in range that also has a stargate. Interstellar Traveler stargates are also able to move ships full of cargo.

### Hyper-Expansion

Races with the Hyper Expansion trait cannot build stargates.

All stargates require research into Construction and Propulsion. The Orbital section of the Technology Browser describes the capabilities of each stargate.

## Mass Driver Basics

Mass drivers provide a fuel-free method of transporting mineral packets between planets and can also act as long-range weapons. Mineral packets are bundles of Ironium, Germanium, and Boranium. Mass drivers fling mineral packets at high acceleration. This prevents you from flinging fuel, which would explode, or colonists, who would also explode.

In the Scanner pane, a mass driver appears as a purple dot orbiting the planet.

### Building a Mass Driver

A mass driver occupies the Orbital slot in a starbase hull. You'll need to research Energy. The requirement for each type of driver is listed in the Orbital section of the Technology Browser.

Once you complete your research, upgrade your starbase hull design to hold the driver, or design a new starbase hull that includes it.

To upgrade a hull and add the driver:

1. Choose `Commands (Ship Design...)` to open the Ship and Starbase Designer.
2. Under `Design`, click on `Starbase`.
3. Select the design you wish to upgrade from the dropdown.
4. Click on `Copy Selected Design`.
5. Select a hull picture and type in a new name, or use the defaults shown in the dialog.
6. Drag the driver from the component list to an Orbital slot in the design. Subtract and add any other components as you wish.
7. Click on `OK`, then click on `Done` to close the dialog.
8. Click on `Change` in the Production tile, and add the new starbase to the planet's production queue.

### Building and Flinging Packets

Mineral packets are built and flung as a function of the Production queue. The Production inventory will list a packet for each mineral and a mixed packet that contains all three minerals. When you click on a packet type in the inventory, the numbers below it show how many kT of each mineral the packet contains.

Once a packet is built, the driver automatically flings it at the destination you've set. If you don't set a destination, the packet disintegrates.

- Target a mass driver by clicking on `Set Dest` in the Starbase tile, then clicking on the destination in the Scanner.

For the packet to arrive safely, the target must also have a driver of equal or greater capacity. If the planet has a lesser mass driver, or no mass driver at all, the packet destroys colonists and installations on the surface.

The gauge in the Starbase tile allows you to control the speed at which packets are flung. You can purposefully fling packets at a slower speed if your receiving planet is not equipped with an accelerator advanced enough to catch the packet at full speed.

The Scanner pane shows mass packets within your scanner range, regardless of who the packets belong to, unless you are a Packet Physics race.

### Interstellar Traveler Races

Interstellar Traveler mass drivers are only half as effective at catching minerals as their rating, are less efficient at flinging minerals, and all mineral packets they fling decay regardless of speed.

You can also target a mass driver by Shift-clicking on the destination.

### Planet-Penetrating Scanners

These scanners can detect fleets in orbit around a planet. They also can tell you planetary stats from a distance.

### Packet Physics

For Packet Physics races, mineral packet decay rates are half the normal level.

You may fling packets at speeds up to three warp levels above the rated speed. Packets flung above the rated speed become unstable, decaying at `10%` per year for one warp level above the rated speed, `20%` for two warp levels, and `50%` for three warp levels. Packets decay in the year they are launched and in the year they arrive at a planet proportional to the distance they travel in those years.

During a packet's first year out, it travels only half the normal distance, then the normal distance in following years. Since production happens all year long, the packets could be launched at any point. Stars! averages this out to a half-year's travel.

#### Packets as Scanners

For Packet Physics races, mineral packets also behave like a planet-penetrating scanner. The radius of the scan is equal to the square of the packet's warp speed.

#### Packets Perform Terraforming

Packet Physics mineral packets do only one-third the normal damage when hitting a planet, but have a `50%` chance per `100 kT` of minerals to terraform the planet's environment toward the player's ideal value.

#### You Can't Attack Packets

You can't attack mineral packets. You can only intercept them and transfer their contents to your fleet.

#### Stealing Mineral Packets

If you can intercept a mineral packet in flight, you can steal from it. When a packet is at the same location as your selected fleet, it appears in the Other Fleets Here tile. Use the `Cargo` button and the Cargo Transfer dialog to transfer minerals from the packet to your fleet.

#### Building Two Mass Drivers on a Starbase

You can build up to two identical mass drivers on the same starbase, assuming you have not used an Orbital slot with a stargate already. This has two advantages:

1. You can catch incoming packets at one warp speed greater than the driver's nominal rating.
2. Packets flung at a speed higher than the recommended maximum from dual-drive starbases decay as if they were flung at one warp speed lower.

#### Packets as Weapons

Packets flung at planets with a lesser mass driver or no mass driver damage the planet and kill inhabitants. A warp-13 mineral packet is about as close as Stars! comes to a doomsday weapon.

## Terraforming

Terraforming is the ability to change a planet's environment to make it more habitable for your race. If you are immune to environmental conditions, you do not need to terraform.

You won't know whether you need to terraform or can terraform a planet unless you can scan it and gather information about the planet's environment. To see all terraformable planets you've found, use the Scanner pane's Planet Value view. Yellow planets are planets you can terraform into habitability. Most green planets can also be terraformed to improve them. The larger the yellow dot, the better the planet will be once terraformed.

Click on a planet in the Scanner pane, then look in the Selection Summary pane. The habitability value shows the current value of the planet followed in parentheses by the value the planet would be after terraforming, given the limits of your current technology.

To see your race's habitability range, choose `View (Race)` and turn to page 4 of the View Race dialog.

The environment graph shows how much you can modify the planet's environment, given your level of terraforming technology. It shows:

- The habitable range.
- The original value.
- The current value.
- The best value possible using your current terraforming technology.

You do not have to worry about the order in which the different factors are terraformed. The terraforming task that appears in the production dialog always works on the factor furthest out of range.

Find out which factor should be terraformed to maximize the planet's habitability value by clicking in the environment graph of the Summary pane. A pop-up will tell you the potential increase in habitability value if you modify that factor to the limits of your current technology.

There are two basic ways to terraform a planet:

- Add auto-build terraforming tasks to the production queue.
- Manually add the `Terraform Environment` task to the production queue.

Terraforming tasks can use only the terraforming technology you possess. If you have only Radiation and Temperature Terraforming, you can modify only radiation and temperature, not gravity. Terraforming automatically acts first on the environmental attribute that will most improve the planet's habitability.

### Colonists Die if Minimum Terraforming Lasts More than One Year

If it takes longer than one year after colonizing to bring the planet to a habitability value of `0%` or better, your colonists will start to die. If you can bring it within range the first year, they will be fine. This is the best reason for creating a production template that contains auto-build terraforming tasks. An auto-build task already in place happens the same year as colonization. Terraforming added manually must wait until the following year.

### Claim Adjusters

Claim Adjusters automatically terraform a planet as soon as they land.

### Terraforming with Auto-Build Tasks

1. Bring the planet you wish to terraform under command.
2. Click on `Change` in the Production tile.
3. In the production inventory, click on either the `Min Terraform` or `Max Terraform` auto-build task, then click on `Add` to raise the limit to which the task will terraform.

Minimal terraforming changes only those environmental factors that have a negative value and that you have the technology to change, up to the percentage you specify in the task. Terraforming continues only until the habitability value reaches zero.

Max Terraforming changes any environmental attributes that you have the technology to change, up to the percentage you specify in the task.

As each terraforming task completes, an environmental factor is improved by `1%`.

### Terraforming as a Default Action

You implement default terraforming by defining a default production template that includes auto-build terraforming tasks:

1. Arrange the auto-build terraforming items in the production queue in the sequence you want them to appear in the template.
2. Set the `Contribute Only Leftover Resources to Research` checkbox the way you want it reflected in the template.
3. Right-click on the blue diamond next to `Apply or Define...` and select `<Customize>`.
4. Select `<Default>` in the Customize Production Template dialog.
5. Click on `Import` to copy in the auto-build items from the production queue, then confirm both dialogs.

The default production orders will take effect on every planet taken over or newly colonized. They do not affect any planets where colonists have already landed.

### Adding Terraforming to the Queue Manually

1. Double-click on the planet you wish to terraform, placing it in the Command pane.
2. Click on `Change` in the Production tile.
3. In the production inventory, click on the `Terraform Environment` task, then click on `Add` to add the desired number of tasks.

Each `Terraform Environment` task improves an environmental factor by `1%`. The number of tasks you may add is limited by your current level of terraforming technology. When you have completed all tasks currently possible, the `Terraform Environment` task disappears from the production inventory and reappears once your technology improves.

### Types of Terraforming Technology

Each of a planet's three environmental factors has a matching type of terraforming technology:

- Temperature terraforming requires Biotechnology and Energy.
- Gravity terraforming requires Biotechnology and Propulsion.
- Radiation terraforming requires Biotechnology and Weapons.

The Total Terraforming trait requires that you research only Biotechnology to learn terraforming technology.

Each technology allows you to improve a specific factor by a minimum of `3%` from its initial value and a maximum, without Total Terraforming, of `15%`.

As you upgrade your terraforming technology, you'll see the amount you can improve the planet increase. You may also find that some planets previously not terraformable become terraformable.

To learn more about the individual types of terraforming technology and their research requirements, open the Technology Browser with `F2` and select `Terraforming` from the dropdown list.

### Total Terraforming

Total Terraforming is a race trait, not a type of technology. Races with Total Terraforming begin the game with the ability to improve temperature, gravity, and radiation levels up to `3%`. Terraforming requires `30%` fewer resources, and these races can research terraforming technologies that improve factors up to `30%` instead of the normal `15%`. Terraforming requires research only in Biotechnology, instead of Biotechnology plus three different additional fields.

To determine whether your race has Total Terraforming, choose `View (Race)` and turn to page 3 of the View Race dialog.

### Claim Adjusters and Automatic Terraforming of Colonies

Races based on the Claim Adjuster trait automatically terraform new colonies upon landing. This terraforming action is both instantaneous and temporary. As soon as the planet is deserted or taken over, the environmental conditions revert to their original values.

As the race learns more about terraforming, all its planets are automatically and instantaneously terraformed to the limits of the technology.

### Claim Adjusters and Terraforming Other Players' Planets from Orbit

Races based on the Claim Adjuster trait can terraform other players' planets from orbit. This creates opportunities for diplomacy or war. If the owner is your Friend, you automatically perform positive terraforming toward the inhabitants' ideal conditions. If the owner is your Enemy, you perform negative terraforming.

Terraforming from orbit requires a fleet outfitted with Orbital Adjusters. These are described in the Mining Robots section of the Technology Browser. Every race with the Claim Adjuster trait starts out with one ship outfitted with Orbital Adjusters.

Terraforming is not additive. You cannot combine your orbital terraforming abilities with those of the inhabitants to super-terraform the planet. The planet will be terraformed only to the limit of whoever has the superior technology.

Terraforming from orbit can also be used as a weapon. Orbit the planet and begin terraforming it under your opponent's feet. This allows you to prepare more favorable conditions for a planetary invasion. You must destroy any existing starbase before you can launch this type of attack.

Specify Friends, Enemies, and Neutrals using the Player Relations dialog by pressing `F7`.

Terraforming from orbit happens automatically as soon as your fleet arrives. Just set the destination planet as the fleet waypoint. No waypoint task is necessary.

### Retro Bomb

Claim Adjusters can also gain the Retro Bomb, a type of terraforming weapon used to return the planet to its original conditions.

## Planet Reports

The Planet Report displays the same information shown in the Command pane, but for all your planets. You can use the report to change the order in which planets appear in the Planet tile and the Production dialog according to any category in the report.

A Planet Report contains the following information:

- `Planet Name`: The color of the dot, if present, indicates the type of starbase and whether a mass driver and stargate are present. The planet currently in the Command pane is highlighted.
- `Yellow dot`: Starbase has a space dock and can build ships.
- `Blue dot`: Starbase without a space dock.
- `Purple dot`: Mass driver.
- `Green dot`: Stargate.
- `Starbase`: Click to display the starbase design.
- `Population`: Current population. Click to display details.
- `Cap`: Percentage of planetary population capacity.
- `Value`: Maximum population percentage relative to maximum growth under optimal conditions, with a second number for the value after terraforming using your current technology.
- `Production`: The item at the top of that planet's production queue.
- `Mine`: Number of mines in existence.
- `Fact`: Number of factories in existence.
- `Defense`: Type of planetary defenses.
- `Minerals`: Number in kT of each mineral on the planet surface.
- `Mining Rate`: Mining rate of each mineral in kT per year.
- `Min Conc`: Mineral concentration for each mineral.
- `Resources`: Resources available for use by the planet, followed by total resources generated by the planet.
- `Driver Dest`: Destination of mineral packets flung from that mass driver.
- `Routing Dest`: Destination planet for ships routed from production.
