# 24. The Guts of Cloaking

In order for matter to be cloaked, it requires a certain number of cloaking units per kT. When a ship is empty, its cloak provides the maximum amount of cloaking possible with that device. When the ship has cargo, the weight of the cargo reduces the number of cloak units per kT, and thus, the cloaking percentage.

## Cloaking When the Ship Is Empty

To determine the total number of cloaking units for an unladen ship, use the following table:

| Cloaking device | Cloak units/kT | Max cloaking % |
| --- | ---: | ---: |
| Transport Cloak* | 300 | 75 |
| Stealth Cloak | 70 | 35 |
| Super-Stealth Cloak | 140 | 55 |
| Ultra-Stealth Cloak* | 540 | 85 |
| Shadow Shield* | 70 | 35 |
| Depleted Neutronium Armor* | 50 | 25 |
| Chameleon Scanner* | 40 | 20 |

\* Available only to Super Stealth races.

For example, an empty ship with a Stealth Cloak has 70 cloak units/kT, or 35% cloaking. By itself, the ship is visible to enemy scanners at only 35% of their maximum range.

When a cloaked ship has cargo, you must recalculate the number of cloak units per kT available. Say the ship is a small freighter with a Quick Jump 5 engine, Tritanium Armor, and a Stealth Cloak. Empty, it weighs 91 kT, has 70 cloak units/kT, and is cloaked at 35%. If you completely fill this freighter with cargo, it weighs 161 kT. To calculate the new cloaking percentage:

1. Calculate the total number of cloaking units for the ship:
   `max_cloak_units_per_kT * ship_mass_empty`

   Example: `70 units/kT * 91 kT = 6370 total cloak units`

2. Calculate the actual units/kT:
   `total_units / ship_mass_with_cargo`

   Example: `6370 / 161 kT = ~40 units/kT`

Use the following reference points to learn how much coverage a given number of cloaking units provides:

| Units/kT | Cloaking % |
| ---: | ---: |
| 100 | 50 |
| 300 | 75 |
| 600 | 87.5 |
| 1000 | 93.75 |

At 40 cloak units/kT, the loaded freighter in this example is now only 20% cloaked.

## Cloaking for a Fleet with More than One Ship

In a fleet with more than one ship, uncloaked ships are counted as cargo when calculating units/kT. Place the empty freighter from the previous example in a fleet with an empty scout that has a Quick Jump 5 engine, Laser, and a Bat Scanner, and which weighs 15 kT when empty. The entire fleet weighs 106 kT, so traveling together this fleet would be:

`6370 / 106 = ~60 units/kT`

That is approximately 30% cloaked.

## The Effect of Multiple Tachyon Detectors

When a hull has more than one Tachyon Detector in its design, the effectiveness is calculated as follows:

`95% ^ sqrt(number_of_detectors) = reduction in other players' cloaking`

## The Appendix of Cloaking

Here is pseudocode you can use to determine cloaking percentage from cloaking points per kT:

```text
if points <= 100
    percent = points / 2
else
    points = points - 100
    if points <= 200
        percent = 50 + points / 8
    else
        points = points - 200
        if points <= 312
            percent = 75 + points / 24
        else
            points = points - 312
            if points <= 512
                percent = 88 + points / 64
            else if points < 768
                percent = 96
            else if points < 1000
                percent = 97
            else
                percent = 98
            end if
        end if
    end if
end if
```

Cargo does not affect cloaking for races with the Super Stealth trait.
