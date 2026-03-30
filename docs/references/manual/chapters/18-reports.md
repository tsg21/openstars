# 18. Reports

Reports list statistics for:

- all your planets
- all your fleets
- other players' fleets you know about
- battles from the previous year

You can use reports to:

- hide columns by clicking a column label and selecting `Hide <column name>`
- show a hidden column by clicking any column and selecting `Show <column name>`
- choose a new sort order by clicking a label and choosing forward or reverse order
- jump to an item by clicking its row in the report
- display related pop-up information or game dialogs by clicking the statistics

In planet reports, the colored dot next to a planet name indicates special facilities:

- yellow: a starbase capable of building ships
- blue: a starbase unable to build ships
- green: a planet with a stargate
- purple: a planet with a mass accelerator

## Keyboard Shortcuts

Press `F3` to cycle through the report windows:

1. `Planet Summary Report`
2. `Fleet Summary Report` for your fleets
3. `Others' Fleet Summary Report`
4. `Battle Summary Report`
5. close the report window

Press `Esc` to close the report window directly.

## Sorting Report Fields

You can sort any report by a specific field type.

1. Right-click on a column header.
2. Select one of the pop-up sorting options.

Reports support up to two levels of sorting. For example, you can sort your planets by mineral content and then sort by starbase type. The result places planets in starbase order, with planets that share the same starbase type sorted by mineral content.

## How Sort Order Affects Planet and Fleet Display

You can change the order in which planets and fleets appear in the Command pane by changing the report sort order.

1. Click on a column header.
2. Change the sort order using one of the available options.

For planets, this matches the order used in the Planet tile and the Production dialog to the order shown in the Planet report. For fleets, it changes the order used in the Fleet tile.

## Printing the Map

Use the `File` -> `Print Map` menu item to print a pictorial map of the universe.

The map is printed in black and white, with the normal black background reversed to white. You can adjust the zoom level of the printout by specifying the number of pages to print: the larger the number of pages, the greater the zoom. The printed map supports the `Planet Names Overlay` and `No Player Info` view only.

## Dumping Reports to Text

To export basic information about the universe, planets, and fleets to plain text files, choose the `Dump to Text` command from the `Reports` menu.

Each option produces a file with the same base name as the current game:

- `Universe` uses the `.map` extension
- `Planet` uses the `.pla` extension
- `Fleet` uses the `.fle` extension

The source scan ends with incomplete fragments for planet, fleet, and battle report print references, so those lines have been omitted here rather than preserved as broken OCR debris.
