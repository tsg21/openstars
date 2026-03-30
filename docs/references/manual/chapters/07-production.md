# 7. Production

In Stars! you produce ships, mines, factories, and defenses, and assign tasks such as terraforming. The Production dialog lists all the things you can build or tasks you can perform on a specific planet, along with commands that allow you to add these items to the queue, information showing how much each item will cost, and when or whether it will be completed given your available resources.

## How Production Works

You have one production queue per planet. The queue is essentially a work list. Items are produced in the order shown in the queue, from top to bottom.

Resources are units of work created by people and factories. They represent the effort required to perform a task or produce an item.

The Production dialog shows:

- Items waiting in production.
- Minerals and resources required to build the selected item in the specified quantity.
- Completion status of the selected item.
- An inventory of everything the planet can currently build.

The production inventory lists all the things you know how to build or tasks you can currently perform on that planet. Like items are displayed in the same color.

You can add, delete, or move items at any time, anywhere in the queue. The percentage complete is shown for the selected item. If you add an item to the top of the queue in front of something that is partially complete, your people will not work to complete the original item until the new item is complete or deleted. Production of items that require minerals is halted if the planet runs out of minerals. Auto-build items that require only resources continue to be produced.

The amount of each mineral and the number of resources required to produce one selected inventory item are shown in the dialog.

### Unique Items

When a planet can use only one of an item, such as a planet-based scanner or starbase, the item appears only once in the inventory. When this kind of item is added to the queue, it disappears from the inventory.

### Upgrades of Existing Items

Upgrades of existing items, such as stargates and starbase hulls, replace any older versions in the inventory list. When you upgrade an item, it is labeled as an upgrade. Since upgrades enhance rather than replace an item, they require only enough minerals to create the enhancements.

## Adding an Item to the Production Queue

You can add an item at any time to any spot in the production queue.

### Add an Item to the Top of the Queue

1. Click on `-- Top of the Queue --`.
2. Click on an item in the inventory, then click on `Add`, or double-click on the item in the inventory list.

### Add an Item to the Middle of the Queue

1. Click on the item in the queue under which you want the new item to appear.
2. Click on an item in the inventory list, then click the `Add` button, or double-click on the item in the inventory list.

### Add an Item to the Bottom of the Queue

1. Click on the last item in the queue.
2. Click on an item in the inventory list.
3. Click the `Add` button, or double-click on the item in the inventory list.

### Move an Item in the Queue

1. Click on the item in the queue that you want to move.
2. Click on the `Item Up` or `Item Down` buttons.

## Removing an Item from the Production Queue

Do one of the following:

- Select an item in the queue, then click the `Remove` button, or double-click on the item in the queue.
- Keep clicking the `Remove` button, or double-clicking on the item name, to remove additional units.

## Production Templates

A production template is a sequence of auto-build items imported from a production queue and saved for later use. Use production templates to automate auto-build production strategies you plan to use more than once.

The default production template is automatically applied on any planet taken over or newly colonized by your people. The other three templates can be manually applied to any planet's production queue. Templates are saved for the duration of the game but may be edited at any time.

### Adding Large Orders

- `Shift` + `Add` adds up to `10`.
- `Ctrl` + `Add` adds up to `100`.
- `Ctrl` + `Shift` while clicking `Add` adds as many of that item as possible.

This also works if you press `Ctrl` + `Shift` and double-click on the item in the inventory list. These keys behave the same when used with the `Remove` button.

### Speedy Removal

- `Shift` + `Remove` removes up to `10`.
- `Ctrl` + `Remove` removes up to `100`.
- `Ctrl` + `Shift` while clicking `Remove` removes as many of that item as possible.

This also works if you press `Ctrl` + `Shift` and double-click on the item in the queue. These keys behave the same when used with the `Add` button.

You apply templates by selecting the template name instead of manually adding the items to the production queue. When you apply a template, all auto-build items currently in the queue are replaced with the list of items in the template.

### Production Template Strategy

To illustrate how production templates are useful, here is an example of a helpful default template for new colonies:

```text
Minimum Terraform Up to 10%
Factories (Auto Build) Up to 10
Mines (Auto Build) Up to 10
Defenses (Auto Build) Up to 2
Factories (Auto Build) Up to 25
Mines (Auto Build) Up to 25
Maximum Terraform Up to 10%
Defenses (Auto Build) Up to 5
```

Explanation:

- `Minimum Terraform Up to 10%`: The planet works on terraforming first if it is possible and people might die otherwise. This handles negative worlds, overcrowding, and disasters.
- `Factories (AB) Up to 10 / Mines (AB) Up to 10`: You want constant progress on improving the planet's productivity. This is what fledgling colonies spend most of their time doing.
- `Defenses (AB) Up to 2`: If the planet is doing well enough to complete those mines and factories, you can afford to work on defenses a bit to keep from falling behind.
- `Factories (AB) Up to 25 / Mines (AB) Up to 25`: At this point you want to ensure the planet has the maximum number of mines and factories. Only mature planets will reach this point.
- `Maximum Terraform Up to 10%`: Push a mature planet toward perfection. The mines and factories are probably maximized for the current population, so, if possible, increase the maximum population and growth rate.
- `Defenses (AB) Up to 5`: Add defenses if the colony has the maximum number of mines and factories possible for the current population.

While the colony is fledgling, it is a good idea to have `Contribute only leftover resources to research` checked. When the colony reaches the point where defenses are being auto-built, you can deselect that option.

### Creating a Template

1. Make sure the auto-build items in the queue are arranged in the same order in which they should appear in the template.
2. Make sure the `Contribute only Leftover Resources to Research` checkbox is set the way you want it to be reflected in the template.

Auto-build items do not need to be consecutively listed, nor do they need to appear at the top of the list to work.

When `Contribute Only Leftover...` is checked, the custom template includes the label `Don't Contribute to Research (until production is complete)`. Otherwise, the template reads `Contribute to Research (before production begins)`.

3. Right-click on the blue diamond and select `<Customize>`.
4. Select `Default` or one of the three other template choices.
5. Click on `Import`.
6. Type in a name for the template and confirm the name dialog.
7. Confirm the Template dialog.

If you created a default template, it will be applied automatically whenever you establish a new colony.

### Manually Applying a Template

Right-click on the blue diamond and select a template to apply to the current production queue. The auto-build items in the template are applied underneath the last item currently in the queue.

### Editing a Template

1. Repeat steps 1 and 2 above.
2. Right-click on the blue diamond and select `<Customize>`.
3. Select the template to be edited.
4. Click on `Import`.
5. Type in a new name for the template if you wish, then confirm the name dialog.
6. Click on `OK`.

The edited template is now ready to apply.

### Renaming or Deleting a Template

1. In the Production dialog, right-click on the blue diamond and select `<Customize>`.
2. Select one of the three non-default templates.
3. Click on `Delete` to erase the template contents and its name, or click on `Rename` and type in a new name.

The default template cannot be renamed. To clear the contents of the existing default template, you must import an empty production queue.

## Clearing the Production Queue

To remove all items from the production queue, click on the `Clear` button in the Production dialog or the Production tile.

If an item is removed from the queue before completion, resources and minerals already spent on the item are lost.

## Unblocking Production

If your planet's mineral concentration runs so low that the time to completion exceeds `100` years, the item name turns red. This means it will practically never be completed unless you do something about it. You have two choices: transport minerals from other planets, or use mineral alchemy, or use both.

### Transporting Minerals

To transport minerals, set up freighter waypoints to move minerals from your remote miners or mineral-rich planets to the planet with the blocked production queue. If both the needy planet and the mineral-rich planet have mass drivers, you can also fling mineral packets between them without using ships.

### Mineral Alchemy

Mineral Alchemy transmutes resources into minerals. If you can't complete an item in the queue because you've run low on one or more minerals, place Mineral Alchemy in the queue ahead of the item you're trying to build.

Each unit of Mineral Alchemy turns `100` resources, or `25` if you have the Mineral Alchemy trait, into `1 kT` of each of the three minerals. This is a good strategy for unblocking queues on a planet where you have a large population and can quickly replace the resources used by alchemy.

Add as many Mineral Alchemy units as you need to finish the item stuck in the queue. Like other items in a queue, the color of each Mineral Alchemy task tells you how long it will take for the process to complete. If you have a large number of resources dedicated to production, you can create a large amount of minerals fairly quickly.

Mineral Alchemy is one of the items available for auto-building. Consider adding it to your default or a custom production template. If auto-alchemy is placed in front of an item, it will be used only if you have a mineral shortage. If it is the only item in the queue, it will convert resources into minerals until you remove it or place another item immediately following it.

## Adding Auto-Build Items to the Queue

Auto-build items are always italicized, but appear differently in the production inventory and queue.

When they're in the inventory, they are labeled as `Auto-build`. When you add them to the queue, they are labeled `<Item> up to <number>`, for example `Factories Up to 50`. The latter number indicates that the queue will attempt to produce the stated number of that item every year.

Auto-build Mineral Alchemy is the exception, displaying as `Mineral Alchemy as needed`. If you insert it in front of an item in the queue, it means to perform as much Alchemy as possible to maximize the production rate for that item. If you already have enough minerals, Mineral Alchemy is not needed and does not happen. If Alchemy is the last item in the queue, it means to spend all remaining resources on Mineral Alchemy.

Auto-build items can be used to create a default queue for newly colonized worlds, or for items you wish to produce on any world whenever extra resources are available for production, or when the queue is empty of anything but auto-build items. For example, early in the game, it is useful to continuously build mines and factories. It is always useful to auto-terraform when conditions are less than perfect and you have the means.

Like any production item, auto-build items can be inserted anywhere in the queue. An auto-build item stays in the queue until you remove it. This means your production queue will annually attempt to build these items when possible. You can always place other items ahead of auto-build items, or rearrange the items in the queue. Auto-build items that cannot be built are skipped.

There are, however, differences between the behavior of auto-build items and other items in the queue:

- Auto-build items do not block the queue. If they cannot be performed, they are skipped.
- Auto-build items are never automatically removed from the queue. They remain there until manually removed and activate only when necessary and possible.
- You never make progress on auto-build items. When work is done, it appears as a partially completed normal build item in the queue.

Auto-build items include Mines, Factories, Defenses, Mineral Alchemy, Terraforming, and auto-building and flinging Mineral Packets, if you have a mass driver.

## Changing the Order of Planets in the Production Dialog

You can use the Planet Report to change the order in which planets appear in the Production dialog. This allows you to easily find planets that may need upgrades of a specific type and add those upgrades to the queue.

1. Press `F3` to open the Planet Report.
2. Click at the head of any column, choosing a sort that appeals to you. You may want to sort by starbase, production, mines, or factories.
3. Click in the `Production` column to open the queue for that planet.
4. Click on `Next`, paging through the queues for each planet. Notice that they appear in the order you specified in the report.

Changing the sort order of planets also changes the order in which they appear when you click on `Next` and `Prev` in the Planet tile.

## Conditions That Affect Production

Page 5 of the View Race dialog tells you whether your race excels at building and operating factories and mines, as well as how many resources `N` colonists will generate each year, not counting resources created by factories.

The more the following conditions are true, the more your race will excel at production:

- One resource is generated each year for every seven colonists.
- Factories produce `15` resources per year.
- Every factory requires five resources, and the usual amount of minerals, to build.
- Colonists may operate `25` factories.
- Factories cost one mineral less to build.

The mining rate also affects production. The closer your race is to meeting one or more of the following conditions, the better:

- Mines produce `25 kT` of minerals per year.
- Every mine requires two resources to build.
- Every `10,000` colonists can operate `25` mines.

### How Research Makes Production Cheaper

Production of a particular item becomes cheaper when all research requirements are surpassed by one level. For example, an engine requiring research level 3 Propulsion and level 1 Energy becomes `4%` cheaper when you attain level 4 Propulsion and level 2 Energy, `16%` cheaper with level 7 Propulsion and level 5 Energy, and so on.

You can eventually reduce the cost of producing some items by `75%`, or `80%` if you possess the Bleeding Edge trait, which decreases costs at a rate of `5%` per level instead of the normal `4%`.

### Disaster Strikes Planet X!

When comets or other naturally occurring blunt instruments crash into inhabited planets, the planet's production queue is reset. All work in progress is lost, including the resources spent on that work.

It is not all bad. Usually a cosmic barrage brings extra minerals that you can apply immediately to production.
