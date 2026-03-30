# 25. The Guts of Mass Drivers

### 20

For example, an empty ship with a Stealth Cloak has 70 cloak units/kT, or 35% cloaking. By itself, the ship is visible to enemy scanners at only 35% of their maximum range.

When a cloaked ship has cargo, we need to recalculate the number of cloak units/kT available. Let’s say this ship is a small freighter with a Quick Jump 5 engine, Tritanium Armor, and a Stealth Cloak. Empty, it weighs 91kT, with 70 cloak units/kT, and is cloaked at 35%. If you completely fill this particular

Cloaks marked here with an * are available only to Super Stealth races.

freighter with cargo, it weighs 161kT. To calculate the new cloaking percentage:

1. Calculate the total number of cloaking units for the ship:
Max_cloak_units/kT x Ship_mass_empty.

Example: 70 units/kT x 91kT = 6370 total cloak units

2.  Calculate the actual units/kT:
Total_units / Ship_mass_with_cargo

Example: 6370 / 161 kT = ~40 units/kT

Use the following chart to learn how much coverage a given number of cloaking units provides.

At 40 cloak units/kT, the loaded freighter in our example is now only 20% cloaked. The following table provides exact numbers at certain points on the graph, allowing for more precise calculations.

100 units/kT

50% cloaked

300 units/kT

75% cloaked

600 units/kT

87.5% cloaked

1000 units/kT

93.75% cloaked

In a fleet with more than one ship, uncloaked ships are counted as cargo when calculating units/kT. Let’s place our empty freighter in a fleet with an empty scout that has a Quick Jump 5 engine, Laser, and a Bat Scanner, which weighs 15kT when empty. The entire fleet weighs 106kT, so traveling together, this fleet would be 6370 / 106 = ~60 units/kT, approximately 30% cloaked.

Cargo does not affect cloaking for races with the Super Stealth trait.

### THE EFFECT OF MULTIPLE TACHYON DETECTORS

When a hull has more than one Tachyon Detector in its design, the effectiveness is calculated as follows:

95% ^ (SQRT(#_of_detectors) = Reduction in other player’s cloaking

### THE APPENDIX OF CLOAKING

Here’s pseudo code you can use to determine cloaking percentage from cloaking points per kT.

if points <= 100

percent = point / 2

else

points = points - 100 if points <= 200

percent = 50 + points / 8

else

points = points - 200 if points <= 312

percent = 75 + points / 24

else

points = points - 312 if points <= 512

percent = 88 + points / 64

else if points < 768 percent = 96 else if points < 1000 percent = 97

else

percent = 98

end if

end if

end if

end if

### 25

### THE GUTS OF MASS DRIVERS

### DAMAGE POTENTIAL OF MINERAL PACKETS

So you always wondered exactly what sort of damage a mineral packet was capable of doing? Here’s the scoop on mass packets.

Mineral packets can be flung at speeds from Warp 5 to 3 Warp levels above the driver’s rated speed. Exceeding the rated speed will form unstable packets that will disintegrate and lose minerals as they travel. Thus, with a top of the line Warp 13 mass accelerator, you can fling packets at speeds up to Warp

16. Why would you want to fling packets slower than the rated speed? Simple:
the planet you are sending packets to doesn’t have an driver capable of catching the faster packets and you don’t want to kill off your own colonists.

### PACKET DECAY RATE

Packets thrown over the rated speed of the mass driver decay as follows:

+1 Warp 10% / year (turn) +2 Warp 25% / year (turn) +3 Warp 50% / year (turn)

There is a minimum decay of 10kT of each mineral in the packet each year.

Packets decay in both the year they are launched and the year they reach their destination by a prorated amount based on the distance they traveled that year. The decay rate is not of the original amount in the packet, but the current amount.

### SPEED AND DISTANCE

Warp N means that something traveling at that speed will cover N x N light years per year. Thus, a Warp 16 packet will travel 256 light years each turn!

If you have the Interstellar Traveler trait, packets flung at or below the driver’s rated speed decay at 10% per year. Overflung packets decay as if flung at one Warp speed higher.

If you have the Packet Physics trait, the decay rate is half the state stated rate; as is the minimum decay.

### DAMAGE AND RECOVERY FORMULAS AND CALCULATION

When a packet hits a planet without a mass driver, or with a mass driver rated beneath the speed of the incoming packet, damage will be done. Damage is determined by the speed of the packet, not the rating of the driver sending the packet. For example, if a Warp 5 driver flings a packet at Warp 8 to another Warp 5 driver, damage will be done to the receiver.

Speed

spdPacket = Packet Warp ^ 2 spdReceiver = Rcvr Accel ^ 2

Percent Caught Safely

The percentage of the packet recovered intact. %CaughtSafely = spdReceiver / spdPacket

Minerals Recovered

The receiver recovers 1/3 of the portion not caught safely. (packetkT x %CaughtSafely + packetkT x %remaining x 1/3)

Raw Damage dmgRaw = (spdPacket - spdReceiver) x wtPacket / 160

Raw Damage modified by planetary defenses

dmgRaw2 = dmgRaw x (100% - pctDefCoverage)

Colonists Killed

The number colonists killed is the larger (maximum) of the following: dmgRaw2 x Population / 1000 dmgRaw2 x 100

Planetary Defenses Destroyed

#destroyed = #defenses x dmgRaw2 / 1000

If #destroyed is less than dmgRaw2 / 20, then it is that number.

Interstellar Traveller Trait Affects Catching Packets

Races with the Interstellar trait are only 1/2 as effective at catching packets. To calculate the damage taken, divide speed_received by two.

Example

You fling a 1000kT packet at Warp 10 at a planet with a Warp 5 driver, a population of 250,000 and 50 defenses preventing 60% of incoming damage.

spdPacket = 100 spdReceiver = 25 %CaughtSafely = 25% minerals recovered = 1000kT x 25% + 1000kT x 75% x 1/3 = 250 + 250 = 500kT dmgRaw = 75 x 1000 / 160 = 469 dmgRaw2 = 469 x 40% = 188

#colonists killed = Max. of (188 x 250,000 / 1000, 188 x 100)

= Max. of (47,000, 18800) = 47,000 colonists

#defenses destroyed = 50 * 188 / 1000 = 9 (rounded down)

If, however, the receiving planet had no mass driver or defenses, the damage is far greater:

minerals recovered = 1000kT x 0% + 1000kT x 100% x 1/3 = only 333kT dmgRaw = 100 x 1000 / 160 = 625 dmgRaw2 = 625 x 100% = 625

#colonists killed = Max. of (625 x 250,000 / 1000, 625 x 100)

= Max. of (156,250, 62500) = 156,250.

If the packet increased speed up to Warp 13, then:

dmgRaw2 = dmgRaw = 169 x 1000 / 160 = 1056

#colonists killed = Max. of (1056 x 250,000 / 1000, 1056 x 100)

= Max. of (264,000, 105600) destroying the colony

Learn more about

- Mass Drivers, p
