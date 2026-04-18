# Stars! Documentation - Game Rules

Source URL: https://www.elite-games.ru/stars/doc/game_rules.shtml

Original title: Stars! Документация - Правила игр

Note: Automatically translated from Russian. Review against the source HTML before relying on subtle rules wording.

[Image:] Stars! Documentation - Game Rules

Rules of the game

In Stars! there is no concept of a standard game. In each game, you must independently set the game conditions, which include both the starting parameters of the game world (game difficulty, size of the galaxy, etc.) and victory conditions (conditions under which one of the players is considered the winner). Of course, at the stage of creating a party, it is necessary to specify a set of players with their races.

Standard and Extended Game

When creating a game, you can use both the standard menu (which appears when you select “New Game...”) and the expanded menu (“Advanced Game...”). In the latter case, you can more accurately and explicitly set the game parameters.

Standard game

The standard game is played for one player only. That is, if you select it, you will be able to play on the same machine with a computer and multiplayer will be impossible.

This type of game (as opposed to the extended one) is recommended for beginners and for a quick start to a race test - when you don’t need to think about many additional parameters.

Here you select the difficulty level, the size of the galaxy and the player’s race.

Difficulty levels (from easy to difficult):

* Easy - small number of AI competitors, weak AI races

*Standard

*Harder

* Expert - a large number of AI competitors, strong AI races, all races play in an alliance against the player

The AI algorithm of computer races does not differ at different difficulty levels. The game of races differs only in the AI ​​race itself. The lower the difficulty, the weaker the race (the higher the number of race points in the editor). If on Easy this number of points is standard (and maybe positive), then on Expert AI it already takes races whose number of points is hundreds and thousands of points less than zero.

The size of the galaxy (Universe Size) is described in detail in the corresponding section.

The number of competitors depends on the size of the galaxy. According to documentation from Stars! this number is:

* Tiny (2-3)

* Small (4-6)

* Medium (4-12, up to 16)

* Large (up to 16)

* Huge (up to 16)

The player has the opportunity to choose one of the standard races supplied with the game (Humanoid, Rabbitoid, Insectoid, Nucleotid, Silicanoid, Antetheral) or a random one (Random). In addition, it is possible to assemble a race yourself (“Customize Race...”).

Extended game

Setting the advanced game parameters occurs on three pages: setting the starting parameters (1), selecting player races (2) and setting victory conditions (3).

Universe Size

Selected exactly the same as in the standard game.

Density of planets (Density)

* Sparse - small number of planets not per unit area

*Normal

* Dense

* Packed - a large number of planets per unit area

See galaxy size description for details.

Player Starting World Positions

Sets how close the players will be after the map is generated.

* Close - close location

*Moderate

* Farther

* Distant - as remote location as possible

Game flags

Each of the flags can be either set or cleared. This choice is yours.

* Beginner: Maximum Minerals - when the flag is turned on, the concentration of minerals at the start of all planets is 100 for all minerals; otherwise the concentration will be set by a random number.

* Slower Tech Advances - slow progress of technologies: all technologies with the flag set become 2 times more expensive when studied.

* Accelerated BBS Play - accelerated start of the game. Worlds have a much larger starting colony population (~100 thousand when the flag is on and ~25 thousand when it is off).

* No Random Events - disable random events when the flag is set.

* Computer Players Form Alliances - AI races play in an alliance against all others when the flag is enabled. Otherwise, they play every man for himself.

* Public Player Scores - when the flag is turned on, from the 20th year onwards, all players will be shown the entire completed table in the information about races in the game (Menu “Report” -> “Score” (F10) during the game).

* Galaxy Clumping - when the flag is turned on, planets are not distributed evenly across the map, but rather in groups (when several planets are closer than others).

Choice of player races

In the second step, the races of all players participating in the game are selected.

The player can select a standard race, build a new one from scratch, or load a race from a file (if there is a favorite race or a multi-player game is being assembled, in which other players send their races).

For AI, you can only select a standard race (or a random one) and the difficulty level of such a race.

Victory Conditions

At the last step, the conditions for winning the game are selected.

These conditions are optional in the selection (the conditions can be set by the players during the creation of the game and victory can be determined during the game). In addition, these conditions can be used as some kind of indicator without emphasis on the fact that these are victory conditions, because After victory is declared, the game can continue.

Each condition can be turned on or off. If it is enabled, then it is active in the game and participates in the calculation (shown in the “Report” -> “Score” -> “Victory Conditions” table).

If a condition is active, it must be parameterized. That is, if, for example, the “Owns N Planets” condition is turned on, then you need to select the number N.

Existing conditions:

Owns N% of all planets

Executed if one of the players controls N% of the worlds. Control means that at the beginning of the turn N% of the planets are under control (in the form of a colony).

N can be set from 20 to 100 in steps of 5.

Attains Tech N in M fields

Executed if the player has reached technology level N in M branches.

N is set from 8 to 26 in steps of 1, M is set from 2 to 6 in steps of 1.

Exceeds a score of N

Executed if the player has scored N points.

N is selected from 1,000 to 20,000 in steps of 1,000.

Exceeds second place score by N%

Executed if the player in first place beats second place by N% in points.

The number N can be set from 20 to 300 in increments of 10.

Has a production capacity of N thousand

Executed if the race has reached production of N thousand resources.

Changes from 10 to 500 in steps of 10.

Owns N capital ships

Executed when the player has N ships of the Capital class at his disposal.

The number N varies from 10 to 300 in increments of 10.

Has the highest score after N years

Executed when the player has the most points for the specified year.

The number N can be set from 30 to 900 in increments of 10.

In addition to the flags, there are two more positions for setting rules, which in any case must be selected:

Winner must meet N of the above selected criteria

The parameter specifies that in order for the game to win, it is necessary for the player to complete N of the points marked with flags.

The number N is selected from 0 to 3 in increments of 1.

At least N years must pass before a winner is declared

To win, at least N years must pass before the winner is announced. That is, a victory for N years is not counted and is checked only after N years have passed.

N can be selected from 30 to 500 in steps of 10.

The flag is calculated every year after the limit is overcome (and in a game with a declared victory too).

Triggering Victory Conditions

In the flag status table for a player, you can see which of the fields he has completed at the moment (regardless of the time the victory conditions are triggered). These flags are visible only to yourself. Until victory is declared, these crosses are not visible to others. When triggered, completed flags become visible to everyone.

If the flag was not turned on during the creation of the game, then it is inactive (but it is shown whether it was completed or not, and is shown to all players).

If a flag has been executed and is subsequently found to no longer be executed, it is reset.

If the victory conditions are met, a corresponding message appears (You have been declared the winner of this game. You may continue to play though, if you wish to really rub everyone's nose in your grand victory). Next, the scores of all active players are automatically published (full table).

If there is only 1 player in the galaxy, then the victory does not work.

If the conditions work for several players, then the system counts the victory for everyone who fulfilled the victory conditions.

PPS does not mean that completed flags will automatically be shown to players after the 20th year.
