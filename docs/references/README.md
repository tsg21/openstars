# Original Game References

OpenStars! is inspired by **Stars!** (1995), a turn-based 4X space strategy game by Jeff Johnson and Jeff McBride.

## Key Resources

- [Stars! AutoHost wiki](https://wiki.starsautohost.org/wiki/Main_Page)
- [Stars! Strategy Guide](https://wiki.starsautohost.org/wiki/Stars!_Strategy_Guide) — comprehensive guide covering all game mechanics, hosted on the AutoHost Wiki
- [Stars! AutoHost Wiki](http://wiki.starsautohost.org/) — community knowledge base, the most complete reference for game mechanics
- [Get Stars!](https://wiki.starsautohost.org/wiki/Get_Stars!#StarsWine_(Windows))
- [Stars! FAQ](http://www.starsfaq.com/) — technical details on battle engine, minefields, turn order
- [Official Strategy Guide](http://starsautohost.org/strategy/guidef/SSG.htm) — original published guide
- [Wikipedia](https://en.wikipedia.org/wiki/Stars!) — general overview and history
- [MobyGames](https://www.mobygames.com/game/2021/stars/) — screenshots, metadata, reviews
- [TotalHost](https://totalhost.starsautohost.org/scripts/index.pl?lp=home&cp=aboutus)
- [TotalHost GitHub](https://github.com/ricks03/TotalHost)

## Reference Documents

- `stars-resolution-order.md` — the original Stars! 16-step turn resolution order (from [Stars! FAQ](http://www.starsfaq.com/advfaq/order-of-events.htm))
- [Design.pdf](https://wiki.starsautohost.org/files/Design.pdf) — all base ship hull and starbase design layouts (slot types, counts, and positions for every hull in the game)

## Screenshots

- `stars-1995-screenshot-51464.jpg` — main UI showing planet management, fleet/starbase details, production queue, galaxy scanner map (from MobyGames)

## Original Game Art & Technology Item Images

The original Stars! used small 2D bitmap images for every technology component, ship hull, and game element. These are useful as reference for OpenStars! UI work.

### Sources

- **`starbmp.zip`** (617 KB) — all bitmap resources extracted from the Stars! executable. The definitive archive of every image in the original game.
  - Download: [Stars! wiki — Downloads](https://wiki.starsautohost.org/wiki/Downloads) (under "References")
  - Also linked from: [Stars! wiki — Technical Information](https://wiki.starsautohost.org/wiki/Technical_Information)

- **MobyGames screenshots** — 29 screenshots including individual technology items shown in the ship designer:
  - [Full gallery](https://www.mobygames.com/game/2021/stars/screenshots/)
  - Examples: [Jihad Missile](https://www.mobygames.com/game/2021/stars/screenshots/win3x/51467/), [Dolphin Scanner](https://www.mobygames.com/game/2021/stars/screenshots/win3x/51468/), [Bear Neutrino Barrier](https://www.mobygames.com/game/2021/stars/screenshots/win3x/51469/), [Trans-Galactic Fuel Scoop](https://www.mobygames.com/game/2021/stars/screenshots/win3x/51470/), [Gatling Gun](https://www.mobygames.com/game/2021/stars/screenshots/win3x/51472/), [Neutronium armour](https://www.mobygames.com/game/2021/stars/screenshots/win3x/51473/)

- **Stars! Nova** (`Graphics/` directory) — an open-source GPL-licensed C# clone with ~429 recreated PNG/JPG images covering every component category:
  - GitHub: [ekolis/stars-nova](https://github.com/ekolis/stars-nova)
  - SourceForge: [stars-nova](https://sourceforge.net/projects/stars-nova)
  - Categories: `Armor/`, `Beam/`, `Bomb/`, `Defense/`, `Electrical/`, `Engine/`, `Gate/`, `Mass_Driver/`, `Mechanical/`, `Mine_Layer/`, `Mining_Robot/`, `Planetary/`, `Planetary_Scanner/`, `Scanner/`, `Shield/`, `Ship/`, `Terraforming/`, `Torpedo/`, `High_Resolution/`
  - These are recreated images (not the original bitmaps) but they are categorised by component type and cover every tech item in the game.

## Terminology Mapping

The original game uses specific terminology that we follow in OpenStars!:

| Stars! term | OpenStars! equivalent | Notes |
|-------------|----------------------|-------|
| Planet      | Planet               | The primary map object — a colonisable location in space. Despite the game being called "Stars!", the dots on the map are planets, not stars. |
| Fleet       | Fleet                | A group of one or more ships travelling together. |
| Ship design | Design               | A blueprint for a class of ship (hull + components). |
| Turn file   | Player commands      | The `.x` file players submitted via email in the original. |
| Host        | Server               | The program that resolves turns. Originally a Windows app run by a human host. |


