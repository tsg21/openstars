# 25. The Guts of Mass Drivers

## Damage Potential of Mineral Packets

Mineral packets can be flung at speeds from Warp 5 to 3 Warp levels above the driver's rated speed. Exceeding the rated speed forms unstable packets that disintegrate and lose minerals as they travel. With a top-of-the-line Warp 13 mass accelerator, you can fling packets at up to Warp 16.

Why would you fling packets slower than the rated speed? Sometimes the receiving planet does not have a driver capable of catching the faster packets, and you do not want to kill off your own colonists.

## Packet Decay Rate

Packets thrown over the rated speed of the mass driver decay as follows:

| Overfling amount | Decay per year |
| --- | ---: |
| `+1 Warp` | 10% |
| `+2 Warp` | 25% |
| `+3 Warp` | 50% |

There is a minimum decay of 10 kT of each mineral in the packet each year.

Packets decay both in the year they are launched and in the year they reach their destination, by a prorated amount based on the distance traveled during that year. The decay rate is applied to the current amount in the packet, not the original amount.

## Speed and Distance

Warp `N` means that something traveling at that speed covers `N x N` light years per year. A Warp 16 packet therefore travels 256 light years each turn.

If you have the `Interstellar Traveler` trait, packets flung at or below the driver's rated speed decay at 10% per year. Overflung packets decay as if flung at one Warp speed higher.

If you have the `Packet Physics` trait, the decay rate is half the stated rate, and the minimum decay is also halved.

## Damage and Recovery Formulas

When a packet hits a planet without a mass driver, or with a mass driver rated below the speed of the incoming packet, damage is done. Damage depends on the speed of the packet, not the rating of the driver that launched it. For example, if a Warp 5 driver flings a packet at Warp 8 to another Warp 5 driver, the receiver takes damage.

### Speed

```text
spdPacket = packet_warp ^ 2
spdReceiver = receiver_accelerator ^ 2
```

### Percent Caught Safely

The percentage of the packet recovered intact:

```text
percentCaughtSafely = spdReceiver / spdPacket
```

### Minerals Recovered

The receiver recovers one third of the portion not caught safely:

```text
mineralsRecovered =
    packetKT * percentCaughtSafely +
    packetKT * percentRemaining * 1/3
```

### Raw Damage

```text
dmgRaw = (spdPacket - spdReceiver) * packetWeight / 160
```

### Raw Damage Modified by Planetary Defenses

```text
dmgRaw2 = dmgRaw * (100% - defenseCoveragePercent)
```

### Colonists Killed

The number of colonists killed is the larger of:

```text
dmgRaw2 * population / 1000
dmgRaw2 * 100
```

### Planetary Defenses Destroyed

```text
destroyed = defenses * dmgRaw2 / 1000
```

If `destroyed` is less than `dmgRaw2 / 20`, use `dmgRaw2 / 20` instead.

## Interstellar Traveler Trait Affects Catching Packets

Races with the `Interstellar Traveler` trait are only half as effective at catching packets. To calculate the damage taken, divide `spdReceiver` by two.

## Example

You fling a 1000 kT packet at Warp 10 at a planet with a Warp 5 driver, a population of 250,000, and 50 defenses preventing 60% of incoming damage.

```text
spdPacket = 100
spdReceiver = 25
percentCaughtSafely = 25%

mineralsRecovered =
    1000 kT * 25% +
    1000 kT * 75% * 1/3
  = 250 + 250
  = 500 kT

dmgRaw = 75 * 1000 / 160 = 469
dmgRaw2 = 469 * 40% = 188
```

Colonists killed:

```text
max(188 * 250000 / 1000, 188 * 100)
= max(47000, 18800)
= 47000 colonists
```

Defenses destroyed:

```text
50 * 188 / 1000 = 9
```

Rounded down, 9 defenses are destroyed.

If the receiving planet had no mass driver or defenses, the damage would be much greater:

```text
mineralsRecovered =
    1000 kT * 0% +
    1000 kT * 100% * 1/3
  = 333 kT

dmgRaw = 100 * 1000 / 160 = 625
dmgRaw2 = 625 * 100% = 625
```

Colonists killed:

```text
max(625 * 250000 / 1000, 625 * 100)
= max(156250, 62500)
= 156250 colonists
```

If the packet speed increased to Warp 13, then:

```text
dmgRaw2 = dmgRaw = 169 * 1000 / 160 = 1056

max(1056 * 250000 / 1000, 1056 * 100)
= max(264000, 105600)
```

That is enough to destroy the colony.
