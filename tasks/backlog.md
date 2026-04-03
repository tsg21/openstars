# Backlog

## Tech Debt & Infrastructure

- [x] Upgrade Node to 24 — Dockerfile, CI workflow, `.nvmrc`/`engines`
- [x] Add `npm run typecheck` script using `tsc -b --noEmit` (matches CI)
- [x] Backend CI workflow — ruff check, ruff format --check, pytest, int tests
- [x] GCS storage adapter — `storage/gcs.py` implementing `GameStorage` for production
- [x] Remove or repurpose mock data files (`mocks/galaxy.ts`, `mocks/playerState.ts`)
- [x] Add loading/error states and retry to GameLobby
- [ ] Store game state blobs as `.json.gz` in storage adapters to reduce GCS/storage cost while keeping `GameStorage` load/save APIs JSON-shaped
- [ ] Add support for reverting a game to an older turn, including storage/meta rollback rules and a safe server-side workflow

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
- [ ] Expanded production catalog — ships, starbases, defences, terraforming

### Population & Colonisation
- [x] Population growth — based on planet value, crowding, growth rate
- [x] Habitability — gravity, temperature, radiation values per planet
- [x] Overcrowding and population death
- [ ] Colonisation — colonise waypoint task, colony ships
- [x] Population transport — load/unload colonists as cargo

### Race Design
- [ ] Primary racial traits (10 traits: HE, SS, WM, CA, IS, SD, PP, IT, AR, JOAT)
- [ ] Lesser racial traits (e.g. improved fuel efficiency, cheap factories, bleeding edge tech)
- [ ] Habitability ranges — gravity, temperature, radiation tolerance
- [ ] Growth rate setting
- [ ] Economy settings — resource production, factory/mine cost and efficiency
- [ ] Race points balancing system

### Ship Design
- [ ] Hull types — scout, frigate, destroyer, cruiser, battleship, dreadnought, etc.
- [ ] Component slots — weapons, shields, armour, engines, scanners, specials
- [ ] Ship designer UI — drag components into slots, see stats
- [ ] Design cost calculation — mineral and resource costs
- [ ] Fuel capacity and consumption per engine type

### Fleet Operations
- [ ] Cargo holds — carry minerals and colonists
- [ ] Fuel model — fuel consumption based on speed, mass, and engine type
- [ ] Refuelling — at starbases and fuel depots
- [ ] Fleet merge and split
- [ ] Fleet scrapping — recover minerals at planets/starbases
- [ ] Waypoint tasks — load, unload, colonise, remote mine, patrol, transfer, lay mines, scrap
- [ ] Wait-for conditions at waypoints (wait for fuel, cargo, fleet, etc.)
- [x] Repeat waypoint routes
- [ ] Speed selection per waypoint leg

### Scanners & Intel
- [ ] Normal scanning — detect planets and fleets within range
- [ ] Penetrating scanning — see planet details (minerals, population) at reduced range
- [ ] Scanner tech progression — better scanners at higher tech levels
- [ ] Planet reports — last-known data for previously scanned planets

### Starbases
- [ ] Starbase construction — build at planets via production queue
- [ ] Starbase hulls and components (orbital fort, space dock, starbase, ultra station)
- [ ] Starbase upgrades — modify design in place
- [ ] Ship building — only possible at starbases
- [ ] Starbase defence bonus (+1 weapon range in combat)
- [ ] Refuelling at starbases

### Research & Technology
- [ ] Six tech fields — Energy, Weapons, Propulsion, Construction, Electronics, Biotechnology
- [ ] Tech level progression — costs increase per level
- [ ] Research spending allocation (% per field or fixed amounts)
- [ ] Component unlocks at tech levels
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

### Minefields
- [ ] Mine laying — fleets with mine layers create/expand minefields
- [ ] Minefield types — normal, heavy, speed bump (SD racial)
- [ ] Minefield hit detection during fleet movement
- [ ] Mine sweeping — beams destroy mines within range
- [ ] Minefield decay over time

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

### Remote Mining
- [ ] Remote mining fleets — mine uninhabited planets from orbit
- [ ] Remote mining module (component)
- [ ] AR racial — can only remote mine (no planet colonisation)

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
- [ ] Turn deadline/timer — auto-resolve after timeout
- [ ] Turn notifications — email/push when new turn is ready
- [ ] Spectator mode
- [ ] Game history/replay — review past turns
