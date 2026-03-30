# 9. Ship and Starbase Design

Use the Ship and Starbase Designer to create, edit, and delete ship and starbase designs. Once you create a ship design, you can add it to the production queue of any planet that has a starbase with a space dock.

You do not need a starbase to build a starbase. If a colony has the necessary resources and minerals, just add the starbase to the production queue.

## How to Approach Hull Design

Develop a strategy for deciding when to create a new design. If you create a new design every time you research a new component, you will likely end up with too many similar ships in service at once. Try to leave room for at least one additional design slot so you can create something new without first deleting an existing design.

You may also want to replace a design when an older class of ship has outlived its usefulness. For example, if you have already colonized all planets within range of your current colonizers, deleting the old design and replacing it with a new one may make sense.

Spend time in the Technology Browser learning about the ship technology you expect to want. Plan research with future ship design in mind. If possible, create new ships only when you gain the technology needed for a meaningful improvement over older designs.

Hull schematics show the type and number of components a hull can carry. Each component slot accepts only the type and number of items shown on its label. Cargo spaces show carrying capacity only and do not accept components.

## Designing a New Ship from an Empty Hull

1. Select `Available Hull Types`.
2. Open the dropdown list and choose a hull design.
3. Click `Copy Selected Design`.

Tip: You can use `Copy Selected Design` to clone a known enemy ship design, although the result may not be perfect.

If `Copy Selected Design` is grayed out, you have reached the maximum of `16` concurrent ship designs. You must delete an existing design before creating a new one.

4. Attach components by dragging them from the ship component list to compatible slots on the hull schematic.

Tip: Hold `Ctrl` while dragging to add as many items as the slot can hold, or hold `Shift` to drag four parts at a time.

The lower-right corner of the Designer shows the design's cost, mass, fuel capacity, shield strength, armor strength, and other statistics. These values update as components are added or removed. Some values shown in the original figure are not visible at resolutions lower than `800x600`.

5. Choose a hull picture and enter a name for the design.
6. Click `OK` to save the design.

## Editing an Existing Hull Design

You can edit a design only if none of your current ships use it. If ships still exist with that design, you must create a copy instead.

To change an existing design or create a new one based on it:

1. Select `Existing Designs`.
2. Choose the design from the dropdown list.
3. Click `Copy Selected Design`.

If `Copy Selected Design` is grayed out, you have already reached the maximum of `16` concurrent ship designs.

If `Edit Selected Design` is grayed out, ships based on that design still exist. Only designs with no surviving ships can be edited directly.

Tip: `Copy Selected Design` can also be used to clone a known enemy ship design, though the result may not be exact.

4. Remove components by dragging them from the hull schematic back to the component list.

Drag items one at a time, hold `Ctrl` to remove all items from a slot, or hold `Shift` to remove four parts at a time.

If desired, replace the removed components with new ones by dragging them from the component list to the schematic.

5. If desired, change the design image and name.
6. Save the design:

- To keep the same name, click `OK`.
- To create a renamed copy, type the new name in the name field, then click `OK`.

## Deleting an Existing Hull Design

If you delete a design, all ships using that design are destroyed and their minerals are lost. If you want to recover some of those minerals, scrap the ships first and then delete the design.

A plaque appears below the schematic for an existing design. It tells you how many ships built from that design still exist. Deleting the design destroys all ships that still use it.

Examples from the manual:

- If all ships built from a design have already been destroyed, deleting the design has no further effect.
- If some ships still survive, deleting the design destroys every remaining ship of that class.

Ships destroyed by deleting a design are not recycled for scrap.

### Deleting Designs in the Designer

1. In the Ship and Starbase Designer, select `Existing Designs`.
2. Choose the design to delete from the dropdown list.
3. Click `Delete Existing Design`.

### Other Ways to Retire Old Designs

Choose a design that is no longer useful, such as one that is too slow or under-armed. Before deleting it, think about the best way to dispose of the ships that still use it.

Example strategies:

- Send each ship to a planet that needs minerals and set its waypoint task to `Scrap Fleet`. Part of the mineral value will be returned to the planet's surface stores, but you must wait for the ships to arrive.
- Delete all ships of that design at once through the Designer. This is immediate, but you receive no minerals.
- Use obsolete armed ships as disposable forces in combat before removing the design.

## Counting Hull Designs

To find the total number of designs you have created:

1. In the Ship and Starbase Designer, select `Existing Designs`.
2. Open the dropdown menu and count the listed designs.

To find how many ships of one design are still in play:

1. Select `Existing Designs`.
2. Choose the design from the dropdown list.
3. Read the plaque beneath the dropdown.

The first number shows how many ships of that design still exist. The second shows how many have been built since the design was created.

## Design, Ship, and Fleet Limits

Stars! limits the number of designs, ships, and fleets each player can maintain. Plan your empire with those limits in mind.

- Different ship designs per player: `16`
- Total ships of each design in a fleet: `32,000`
- Fleets per player: `512`
- Different starbase designs per player: `10`

Tip: You can locate all ships of a given type by using the Ship Design Filter in the Scanner pane.

Stars! grays out `Copy Selected Design` once you reach the `16`-design limit. Although the game warns you when you try to create a seventeenth design, it is still worth tracking your design count yourself.

If you reach the limit and want to create something new, you must delete an existing design first. The Ship and Starbase Designer is where you do that, so it pays to think ahead about when to replace older ships.

## Adding Ship-Based Scanners

To gather planetary details from orbit or inspect enemy fleets at range, most fleets need a ship-based scanner. Scanning an unowned planet reveals only environmental data and underground mineral concentrations. Without scanners, a ship must send down a robot miner to gather the same information and can detect an enemy ship only if both occupy the same `X,Y` coordinates.

### Scanner Types

There are three basic kinds of ship-based scanners:

- Scanners that inspect planets from orbit only.
- Scanners that inspect planets from orbit and fleets at a distance.
- Scanners that inspect both planets and fleets at a distance.

The `Chameleon` scanner also functions as a cloaking device.

### Your First Scanner

You generally begin the game with the `Bat` scanner, a low-tech device that reveals planet details only from orbit and has no long-range fleet detection capability. Browse the more advanced models in the Technology Browser to see what becomes available later.

### Scanners Are Cumulative

Multiple scanners on one ship combine their effect. A fleet is still limited by the best scanner range available within that fleet, but an individual ship's scanner range is the modified sum of its installed scanners.

The manual gives this formula:

```text
scanner range = fourth root of the sum of each scanner's fourth power
```

Example:

```text
(100^4 + 100^4 + 60^4)^(1/4) = 120 light years
```

The same calculation applies to planet-penetrating scanners.

Tip: To determine your current number of fleets, open the `Report (Fleets)` screen. The total appears in the report window's title bar.

You learn how many minerals are on a planet's surface only after colonizing it, remote mining it, or using a `Robber Baron` scanner.

### Scanners for Pirates

The `Pick Pocket` and `Robber Baron` scanners can reveal the contents of an enemy fleet's cargo holds. The `Robber Baron` can also see surface minerals on enemy planets. These scanners are useful for deciding which targets are worth robbing.

## Adding Cloaking Devices

A cloaking device reduces the distance at which enemy scanners can detect your fleets. Different cloaks reduce scanner effectiveness by different percentages. Higher percentages mean better concealment.

Cloaks on a ship may all be of the same strength or of mixed strengths. Cloaking applies to the entire fleet: ships without cloaks are protected as long as they stay in the same fleet as cloaked ships.

When designing a ship, you can place a cloaking device in any slot labeled `Electrical` or `General Purpose`.

## Engines

There are two broad classes of engines:

- Standard engines, which require anti-matter fuel available at full-service starbases.
- Ramscoop engines, which gather fuel from space.

Both types have an absolute maximum speed of `Warp 10`. Each has different strengths, weaknesses, and race-trait requirements.

### Standard Fuel-Hungry Engines

Conventional fueled engines work well in the early game. If your race has the `No Ramscoop Engines` trait, you will use standard engines for the entire game. In that case, the `Interspace-10` is available to you.

### Ramscoop Engines

Ramscoops collect fuel from space and are therefore the cheapest engines to operate. The `Radiating Hydro-Ram Scoop` emits heavy radiation and should not be used for colonist transport unless your race is immune to radiation or has an optimal radiation level of at least `85 mR`.

The manual's examples make the rule clearer:

- A range of `80` to `90 mR` works.
- A range of `70` to `100 mR` also works.
- A range of `35` to `95 mR` does not work, because the midpoint is only `65 mR`.

Ships with ramscoops take more damage from mine hits than ships using other engines.

Races with the `Inner Strength` trait can research `Tachyon Detectors`, which reduce the effectiveness of other players' cloaking devices.

You cannot build ramscoop engines if your race has the lesser trait `No Ramscoop Engines`.

Important: the optimal radiation level is the midpoint of your race's radiation habitability range. Use the `View (Race)` menu item to check it.

### Overthrusters

Overthrusters help in combat and offset movement penalties from hull and cargo mass. One Overthruster gives a ship an extra half-square of movement per battle round. Each additional Overthruster adds another half-square.

### Maneuvering Jets

Maneuvering Jets also improve combat movement. One Maneuvering Jet adds one-quarter of a square of movement per battle round. Each additional jet adds another quarter-square.

Overthrusters and Maneuvering Jets are described in more detail in the `Mechanical` section of the Technology Browser.

## Learning About Other Players' Hull Designs

When you first encounter an enemy ship, you automatically learn its basic hull type. If you later fight that ship in battle, you also learn which components the design uses.

To review enemy hull designs:

1. Select `Enemy Hulls`.
2. Open the dropdown list and choose a design.

The ship schematic appears. If you have only seen the ship in passing, the schematic is empty. If you have fought it in battle, the components are shown. Right-click a component to display additional details.

## Trading Ship Designs

You can trade ship designs with other players by using the `Transfer Fleets` waypoint task. To receive a transferred fleet, you must have fewer than `16` different designs, which is the maximum allowed.

Tip: You can use `Copy Selected Design` to clone a known enemy ship design, though the result may not be exact.

### War Mongers

Races with the `War Mongers` trait learn full ship designs the moment they see them. They do not need to fight a battle first to reveal hull details.
