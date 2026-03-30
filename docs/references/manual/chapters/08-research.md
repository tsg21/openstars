# 8. Research

You cannot go from rubber band drives to ramscoops, or from binoculars to `520X` planetary scanners, without applying mental elbow grease. This means research. Fortunately, to conduct research in Stars!, you need to know nothing of physics or animal husbandry, biomechanics or elastic waistbands. You only need to know which general areas of technology you wish to research and how many resources you wish to allocate to that research. That, pushing a couple of buttons, and being patient, will gain you access to all the technology you need to rule the known Stars! universe.

Before you start researching, spend a little time in the Technology Browser by pressing `F2`. Learn about the types of technology available to your race, the items you want to build, and which areas and levels of research are needed to do that.

Resources are units of work created by people and factories. They represent the effort involved in performing a task or producing an item.

## Fields of Study

There are six fields of study:

- Energy
- Weapons
- Propulsion
- Construction
- Electronics
- Biotechnology

You can research only one field at a time. Levels of proficiency range from `0` to `26`. At level `26`, you are a techno-geek summa cum astrolabe, a level that 20th-century hi-tech moguls can only daydream about reaching. When you complete a research level, new technology becomes available to you.

Going beyond the level needed to produce an item has cost benefits. For every technology level you achieve above the required level, the production cost of that item is reduced by `5%`. You can eventually reduce production costs for many items by `75%`. This is also referred to as miniaturization.

The type of research needed to gain a technology depends on the function of that technology. For example, most ship hulls require Construction research only. Some technology requires research in more than one area. Gravity Terraforming requires research in both Biotechnology and Propulsion.

Use the Research dialog to specify a field of study and the percentage of resources you wish to apply annually to that research. The dialog also displays the specific technology you will gain by achieving the next few levels in that field.

Resources applied to research are normally taken off the top of your resource heap. This allocation changes only if you check `Contribute Only Leftover Resources to Research` in the Production dialog, which reverses the order and allocates resources first to production, then to research.

You can change research fields before achieving a new level. Stars! keeps track of how much progress you have made in a field, allowing you to return to a partially researched field later without losing progress.

### Choosing the Next Field of Study

Queue your next field of interest by using the `Next Field to Research` dropdown in the Research dialog. This switches your research as soon as you reach the next level in your current field. All resources not needed to reach the next level in the current field are applied to the next field.

If you achieve the maximum level for a field and forget to specify a new one, Stars! automatically selects the least researched field.

## Browsing Stars! Technology

The Technology Browser provides details about every technology you can learn through research, including ship components, planetary installations, and terraforming. To open the Technology Browser, press `F2` or choose the `Help` menu item for it.

Use the browser to:

- Select a technology category from the dropdown list to find an item quickly.
- Review resource cost and weight.
- Check technical requirements.
- Read warnings and notes about availability and race-trait requirements.
- Filter the list to show only technologies you can currently build.

If you have not completely researched the technology required to build an item, its cost still appears. The color of each required research field shows whether you have met the requirement:

- Red means you still need more research.
- Black means you have reached the necessary level.

The number next to each field is the level you must attain. `Cost` is the number of resources needed to build that item.

The Technology Browser always displays cost and other information relative to your race type and current level of knowledge. The printed documentation and online help show base costs without regard to race traits or current knowledge.

See also `Technology Data Tables` in Appendix B.

## Allocating Resources for Research

### How Production Affects Research

For research, you receive all resources from planets with nothing in the production queue and with auto-build turned off. You also receive all unspent resources from planets whose queues are blocked by lack of minerals.

If the `Contribute Only Leftover Resources to Research` box is selected in the Production dialog, you will receive only the resources left over if the planet's queue is emptied that turn.

If that box is not selected, you receive the percentage of resources indicated in the Research dialog, plus any resources left if the production queue is emptied that turn. If the production queue is blocked, you receive all of that planet's resources for that turn.

### Predicting How Much Time Research Will Take

Predicting the amount of time it will take to complete a research level is slightly tricky. Stars! displays the estimated time to completion in the Research dialog.

The estimate is based on an unchanging supply of resources, including:

- All resources from planets with empty production queues and inactive auto-build.
- Allocated resources from planets that are producing items while dedicating resources to production first because `Contribute Only Leftover Resources to Research` is not selected.

To get your best estimate of how long research will take, look at both the current time estimate and the number of resources allocated the previous year, which is also shown in the Research dialog. Each turn, check how much the estimate changes as a result of changing conditions in your empire.

To get a more accurate estimate, assign or change your research allocation as the last task of your turn. By then, Stars! knows how many resources are required for production and removes those from the research-time calculation.

### Sample Strategies for Resource Allocation

Some people play Stars! with global research allocation set to a low number, assuming that on some turns production queues will run out of things to do and large amounts of resources will be allocated automatically to research. Other people like to keep their production queues busy all the time and prefer to allocate a larger research percentage up front. Both styles can be equally successful.

## The Cost of Research

Research becomes more expensive for each level of technology you achieve. You spend resources to do research, and research in any field becomes progressively more expensive, increasing in a Fibonacci-type series. The total cost equals the cost for that field plus the added cost of `10` resources per field of study for each level you have already achieved. This cost is calculated for you in the Research dialog.

In general, you should decide which technology you want to learn, then research only the field or fields needed to gain that technology. That minimizes the resources needed to reach a specific goal. Ultimately, though, it costs the same to research all technology. The added costs encourage you to develop a few initial technologies quickly and take them out into the universe.

The Fibonacci numbers are the unending sequence:

```text
1, 1, 2, 3, 5, 8, 13, 21, 34...
```

Each number is the sum of its two predecessors.

Research can be cheaper for some races than for others. To learn how efficient your race is at performing research, choose the `View (Race)` menu item, then turn to page `6` of the View Race dialog. Both the Technology Browser and pages `2` and `3` of the View Race dialog show which technologies you will not be able to research because of a primary racial trait. The Research dialog shows only the technology available to your race.

### Generalized Research Trait

If you choose the `Generalized Research` trait when building a race, your race takes a holistic approach to research. Only half of the resources dedicated to research are applied to the current field of research. `15%` of the total is applied to each of the other fields.
