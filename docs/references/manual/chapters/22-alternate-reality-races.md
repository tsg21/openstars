# 22. Alternate Reality Races

Although `Alternate Reality` is technically a primary trait, it creates races unusual enough to deserve their own chapter.

## Population and Growth

Alternate Reality races are highly developed energy-based life forms. Their bodies are fragile and flatten under anything but the lightest gravitational conditions, so they live on starbases and control their planets from orbit.

Their growth rates are still determined by the planet's habitability value, since those values reflect tolerance to factors such as solar radiation and planetary gravity wells. Their maximum population on a world is determined by the size of the starbase in orbit, ranging from `250,000` for starter colonies to `3,000,000` for a `Death Star`.

Living on the starbase has a major downside: if the starbase is destroyed, the population is destroyed with it.

## Scanners

Alternate Reality colonists perform scanning duty from the starbase. Their scanner range is determined by this formula:

```text
Scanning Distance = sqrt(Population / 10)
```

The `Ultra Station` and `Death Star` include equipment that also allows penetrating scans at half that distance, as long as you did not choose the `No Advanced Scanners` trait when defining the race.

## Factories

Because Alternate Reality races are not suited to planetary operations, they cannot build factories. Instead, their energy-based nature gives them a different resource formula:

```text
Resources = Habitability Value *
  sqrt(Population * Energy Tech Level / Efficiency Coefficient)
```

The `Efficiency Coefficient` is set in the `Custom Race wizard`. As your `Energy` tech level increases, planetary efficiency improves.

## Mining

Alternate Reality races cannot build mines. Using energy powers alone, they perform a limited amount of innate mining equal to:

```text
Mining = sqrt(Population / 10)
```

Since they do not actually inhabit the planet surface, they can also remote-mine worlds they own as well as uncolonized worlds.

## Defenses

Alternate Reality races cannot build planetary defenses. Since they live and die with their starbase, planetary defenses have no meaning to them.

Enemy players cannot bomb Alternate Reality planets, and mineral packets flung from other planets do not kill Alternate Reality colonists.

Their best defenses are well-armed, well-armored starbases and protective minefields.

## Starbases

Starbases cost Alternate Reality races `20%` less than they do for other races, though this does not stack with the `Improved Starbases` trait.

They can also build the `Death Star`, the biggest and most powerful starbase hull in the game.

## Colonization

Alternate Reality races cannot build normal colonization modules. Instead, they must build the more expensive `Orbital Colonization Module`, which can be mounted only on the `Colonizer` hull. At the target world, it deploys as an `Orbital Fort`.

The module also includes viral weapons that can kill `2000` enemy colonists each year while bombing, making it useful for removing lightly defended startup colonies.

Travel itself has a cost: interstellar movement kills `3%` of any colonists in the fleet each year.

Alternate Reality races also cannot drop colonists onto worlds to take them over, so they do not participate in ground combat.
