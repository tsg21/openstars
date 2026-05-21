# Backlog

## Tech Debt & Infrastructure

- [x] Upgrade Node to 24 — Dockerfile, CI workflow, `.nvmrc`/`engines`
- [x] Add `npm run typecheck` script using `tsc -b --noEmit` (matches CI)
- [x] Backend CI workflow — ruff check, ruff format --check, pytest, int tests
- [x] GCS storage adapter — `storage/gcs.py` implementing `GameStorage` for production
- [x] Remove or repurpose mock data files (`mocks/galaxy.ts`, `mocks/playerState.ts`)
- [x] Add loading/error states and retry to GameLobby
- [x] Dependency health check (phase 1) — security-only updates for Vite and Pygments vulnerabilities
- [x] Dependency health check (phase 2) — low-risk patch updates across frontend and backend lockfiles
- [x] Store game state blobs as `.json.gz` in storage adapters to reduce GCS/storage cost while keeping `GameStorage` load/save APIs JSON-shaped
- [ ] Add support for reverting a game to an older turn, including storage/meta rollback rules and a safe server-side workflow

## Deferred refactoring
- [x] Stop game creation from creating designs directly. Pass through the normal design save code. Remove HULL_MASS_BY_ID, fuel_capacity_by_hull

---

## Game Features

Features needed to reach parity with the original Stars! game.
Roughly grouped by system — prioritisation TBD.

### Economy & Resources
- [x] Mineral model — three mineral types (ironium, boranium, germanium) on planets
- [x] Mineral concentrations — each planet has concentration values per mineral type
- [x] Surface mineral deposits — minerals sitting on planets ready to use
- [x] Mines — extracting minerals from planets, diminishing concentrations over time
- [x] Factories — generating resources from population
- [x] Resources — population × efficiency, modified by factories

### Production
- [x] Simple production queues — per-planet ordered queues for mines and factories
- [ ] Production templates
- [ ] Auto-build production items
- [x] Expanded production catalog — ships
- [ ] Turns-to-complete estimate in the Production view — show estimated turns to finish each palette row and each queue row, derived client-side from the planet's resources/turn and current mineral stockpile walked across queued items. Deferred from [PRD 68](../docs/prd/68-ui-production.md).

### Population & Colonisation
- [x] Population growth — based on planet value, crowding, growth rate
- [x] Habitability — gravity, temperature, radiation values per planet
- [x] Overcrowding and population death
- [x] Colonisation — colonise waypoint task, colony ships
- [x] Population transport — load/unload colonists as cargo

### Race Design
- [x] MVP race implementation, including key traits: resources/colonist, resources/factory, resources to build factory, etc. https://www.elite-games.ru/stars/doc/race/economic.shtml
- [x] Habitability ranges — gravity, temperature, radiation tolerance
- [x] Growth rate setting
- [x] Economy settings — resource production, factory/mine cost and efficiency
- [x] Race points balancing system
- [ ] Leftover advantage bonuses — surface_minerals / mines / factories / defenses / concentrations applied at homeworld materialisation
- [ ] Population cap factors — HE 0.5×, JOAT 1.2×, AR 0× (currently always 1.0×)
- [ ] Custom race wizard UI — six-step polished flow (replaces flat MVP form)
- [ ] Account-level race library — save and reuse race designs across games
- [ ] Remaining predefined races — Insectoid, Rabbitoid, Nucleotid, Silicanoid, Antethereal (Humanoid lands in Phase A)

#### Primary Racial Traits (PRTs)
- [x] JOAT — Jack of All Trades: +20% pop cap, built-in scanners on Scout/Frigate/Destroyer, tech-4 accelerator (instead of tech-3)
- [x] HE — Hyper-Expansion: 2× growth multiplier, 0.5× pop cap, cannot build stargates, Mini-Colonizer / Settler's Delight / Flux Capacitor
- [ ] SS — Super Stealth: free 75% cloak on all owned ships and starbases, espionage research, +1 safe minefield speed, Rogue / Stealth Bomber, Pick Pocket / Robber Baron / Chameleon / Shadow tech
- [ ] WM — War Monger: weapons −25% cost, +0.5 battle movement (cap 2.5), ground-attack bonus, cannot lay mines, defences limited to SDI/Missile, Battle Cruiser / Dreadnought
- [ ] CA — Claim Adjuster: auto-terraform owned planets to biotech limit each turn (reverts on capture/abandon), Retro Bomb / Orbital Adjuster
- [ ] IS — Inner-Strength: colonist reproduction on freighters, 2× landing defence, 1.5× repair, defences −40%, weapons +25%, no smart bombs, Super Freighter / Fuel Transport / Croby Sharmor / Fielded Kelarium / Jammer 10–50 / Tachyon Detector / Mini Gun
- [ ] SD — Space Demolition: detonate own minefields, 2× safe minefield speed, minefields scan, 1%/yr decay, Mini / Super Mine Layer + full Dispenser/Heavy/Speed Trap series, Energy Dampener
- [ ] PP — Packet Physics: two starting planets (non-tiny galaxy), cheaper smaller packets, packets scan with penetrating, packets have terraform chance, Mass Driver 5/6/8/9/11/12/13, Energy Dampener
- [ ] IT — Interstellar Traveler: two starting planets with 100/250 stargates (non-tiny galaxy), 25% stargate discount, can gate cargo, reduced gate-loss probability, Anti-Matter Generator
- [ ] AR — Alternate Reality: live in starbases, no planetary installations, pop grows via starbase capacity, resources scale with energy tech, 3% in-flight colonist death, 20% starbase discount, Death Star / Orbital Construction Module

#### Lesser Racial Traits (LRTs)
- [x] IFE — Improved Fuel Efficiency: fuel ×0.85, unlocks Fuel Mizer + Galaxy Scoop (unless NRSE), +1 starting Propulsion
- [ ] TT — Total Terraforming: ±3 / ±5 / ±10 / ±15 / ±20 / ±25 / ±30 progression at biotech 0/6/9/13/17/22/25; terraforming costs −30%
- [ ] ARM — Advanced Remote Mining: unlocks Midget Miner / Miner / Ultra-Miner hulls + Robo-Midget / Robo-Ultra-Miner; starting fleet gains two Midget Miners
- [ ] ISB — Improved Starbases: unlocks Space Dock + Ultra Station; starbases auto-cloak 20%; starbase build cost −20% (does not stack with AR)
- [ ] GR — Generalized Research: 50% to current field + 15% to each of the other five (net 125% spend, not redistribution)
- [ ] UR — Ultimate Recycling: scrap recovery 90% min / 70% res at starbases, 45% / 35% at planets via `(P×E)/(P+E)` formula
- [ ] MA — Mineral Alchemy: resource→mineral conversion at 25 res = 1 kT (4× more efficient than baseline 100 res)
- [ ] NRSE — No Ramscoop Engines: forbids all ramscoops except Fuel Mizer (with IFE) and Enigma Pulsar (Mystery Trader); unlocks Interspace-10
- [ ] CE — Cheap Engines: engines ×0.5 cost, 10% warp >6 failure-to-engage chance, +1 starting Propulsion
- [ ] OBRM — Only Basic Remote Mining: mining-ship hulls limited to Mini-Miner; mining robots limited to Robo-Mini-Miner; +10% planet pop cap (additive with HE/JOAT)
- [ ] NAS — No Advanced Scanners: penetrating scanners forbidden (except Chameleon / Robber Baron / JOAT-built-in / MT); normal scanner ranges ×2
- [ ] LSP — Low Starting Population: starting homeworld pop 70% of normal (17,500 vs 25,000)
- [ ] BET — Bleeding Edge Technology: new tech ×2 cost until all prerequisites exceeded by ≥1 level; miniaturisation 5%/level capped at 80% (vs 4%/75%)
- [ ] RS — Regenerating Shields: shields ×1.4 strength + 10% regen per round; armour rated strength ×0.5

### Ship Design
- [ ] Hull types — scout, frigate, destroyer, cruiser, battleship, dreadnought, etc.
- [x] Component slots — weapons, shields, armour, engines, scanners, specials
- [x] MVP Ship designer UI — simple selection 
- [ ] Full Ship designer UI — drag components into slots, see stats
- [x] Design cost calculation — mineral and resource costs
- [x] Fuel capacity and consumption per engine type

### Fleet Operations
- [x] Cargo holds — carry minerals and colonists
- [x] Fuel model — fuel consumption based on speed, mass, and engine type
- [x] Refuelling — at starbases and fuel depots
- [x] Fleet merge and split
- [x] Waypoint tasks — load, unload, colonise, transfer
- [ ] Wait-for conditions at waypoints (wait for fuel, cargo, fleet, etc.)
- [x] Repeat waypoint routes
- [x] Speed selection per waypoint leg
- [ ] Waypoint task: scrap - recover minerals at planets/starbases
- [ ] In-turn load/unload of resources/colonists while a fleet is in orbit of a planet. Include "unload everything" button.
- [x] Refuelling at starbases
- [ ] Ability to target other fleets as destinations for waypoints (for merging and later attacking)

### Scanners & Intel
- [x] Normal scanning — detect fleets within range
- [ ] Penetrating scanning — see planet details (minerals, population) at reduced range
- [x] Planetary scanners
- [ ] Scanner tech progression — better scanners at higher tech levels
- [ ] Planet reports — last-known data for previously scanned planets

### Starbases
- [x] Expanded production catalog — starbases
- [ ] Starbase hulls and components (orbital fort, space dock, starbase, ultra station)
- [ ] Starbase upgrades — modify design in place
- [x] Ship building — only possible at starbases
- [ ] Starbase defence bonus (+1 weapon range in combat)

### Research & Technology
- [x] Six tech fields — Energy, Weapons, Propulsion, Construction, Electronics, Biotechnology
- [x] Tech level progression — costs increase per level, progress is per-field, level-ups emit events
- [x] Research spending allocation — per-player resource allocation percentage plus per-planet leftover-only mode
- [x] Research UI — top-bar Research workspace tab with current/next field selection, allocation control, per-field progress rows, and auto-saved turn commands
- [x] Component unlocks at tech levels — design creation rejects hulls/components whose tech prerequisites are unmet
- [x] Build-time miniaturisation — ship production costs improve as owner tech exceeds prerequisites
- [x] Research event log messages — generic event formatter handles `research.level_up`
- [x] Next-field switching after level-up — completed levels switch to queued next field and apply leftover points there
- [ ] Technology Browser UI — list components/hulls by unlock field and level
- [ ] Tech trading/stealing from combat

### Combat
- [ ] Battle engine — 10×10 grid, tokens/stacks, up to 16 rounds
- [ ] Movement AI — six battle orders (disengage, maximise damage, etc.)
- [ ] Weapon types — beams (range dissipation), torpedoes (accuracy rolls), capital missiles
- [ ] Shields and armour — damage application order, regeneration
- [ ] Targeting — attractiveness formula (cost/defence), primary/secondary targets
- [ ] Battle plans — configurable per fleet (target type, tactic, enemy selection)
- [ ] Salvage — 1/3 mineral cost of destroyed ships left at battle location
- [ ] Battle replay/viewer in UI

### Bombing & Invasion
- [ ] Conventional bombing — kill population, damage infrastructure
- [ ] Smart bombs — kill population based on defence coverage
- [ ] Ground combat — troop drops for planet capture
- [ ] Planetary defences — reduce bombing effectiveness
- [ ] Expanded production catalog — defences

### Minefields
- [ ] Mine laying — fleets with mine layers create/expand minefields
- [ ] Minefield types — normal, heavy, speed bump (SD racial)
- [ ] Minefield hit detection during fleet movement
- [ ] Mine sweeping — beams destroy mines within range
- [ ] Minefield decay over time
- [ ] Waypoint task: lay mines

### Stargates
- [ ] Stargate construction — component on starbases
- [ ] Fleet transfer — instant movement between two stargates
- [ ] Mass/range limits — exceeding limits risks ship loss
- [ ] Gate ranges by tech level (any/300, any/800, 100/any, etc.)

### Mass Drivers
- [ ] Mass driver construction — component on starbases
- [ ] Mineral packet launching — send minerals between planets
- [ ] Packet speed by driver level
- [ ] Packet impact damage — unmatched-speed packets damage target planet
- [ ] Innate trader packet catching (IT racial)

### Terraforming
- [ ] Terraforming orders — improve planet habitability toward ideal
- [ ] Terraforming limits by tech level
- [ ] Total terraforming (racial ability)
- [ ] Terraform in production queue or as fleet waypoint task
- [ ] Expanded production catalog — terraforming

### Remote Mining
- [ ] Remote mining fleets — mine uninhabited planets from orbit
- [ ] Remote mining module (component)
- [ ] AR racial — can only remote mine (no planet colonisation)
- [ ] Waypoint task: remote mine

### Wormholes
- [ ] Wormhole generation on galaxy map
- [ ] Fleet travel through wormholes
- [ ] Wormhole stability and wandering endpoints
- [ ] Wormhole detection by scanners

### Diplomacy & Communication
- [ ] Player-to-player messaging
- [ ] Ally/enemy/neutral status per player pair
- [ ] Shared scanner data with allies
- [ ] Friend-or-foe settings for combat

### Random Events
- [ ] Comet strikes — random planet damage
- [ ] Mystery Trader — NPC fleet offering tech trades
- [ ] Artifact planets — bonus tech on colonisation

### Multiplayer & Platform
- [ ] Player accounts — Google Auth login
- [ ] Server-side storage of incomplete turn data, so it can be resumed
- [ ] Turn deadline/timer — auto-resolve after timeout
- [ ] Turn notifications — email/push when new turn is ready
- [ ] Spectator mode
- [ ] Game history/replay — review past turns
