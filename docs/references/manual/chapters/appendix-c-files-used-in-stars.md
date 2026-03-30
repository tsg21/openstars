# Appendix C. Files Used in Stars!

This appendix summarizes the main file types used by Stars! during game setup, turn submission, and local play.

## Host File: `GAMENAME.HST`

The host file contains the information the host program needs for a specific game. It should be available only to the person acting as host.

## Universe File: `GAMENAME.XY`

The universe file contains the positions of all planets. It does not change over the course of the game. Both the host and the individual players need this file.

## Turn File: `GAMENAME.MN`

Turn files are numbered from `1` to `16`, where `N` is the player number. Each file contains that player's race data and the state of that player's empire at the beginning of a turn.

## Race Description File: `NAME.RN`

This file contains a race description created and saved with the Custom Race Wizard. `N` can be any number, and Stars! defaults to an extension such as `r1`; the default extension is not required.

You can specify a race file for each non-computer player in step 2 of the `New Advanced Game` dialog. Once the universe has been created, the race file is no longer needed.

If you open a race description file using `File (Open)`, the Custom Race Wizard opens.

## Log File: `GAMENAME.XN`

Log files are numbered from `1` to `16`, where `N` is the player number. A log file records the orders a player has given for the current turn.

This file is submitted to the host program, either automatically or manually. The host applies those orders to the player's `mN` file and returns an updated turn file when the next turn is generated. The host needs the log files to update each player's information from the `.hst` file before turn generation.

Each time a player opens or continues a game, the `.mN` file is loaded. If a corresponding log file exists, it is also loaded so the current state reflects any unsent orders already recorded.

## History File: `GAMENAME.HN`

History files are numbered from `1` to `16`, where `N` is the player number. This file is created from the universe data as the player sees it and stores a history of what that player has seen or learned on previous turns.

Normally only the player keeps a copy of this file. If a player will be absent for a few turns and wants the Housekeeper AI to take over temporarily, a copy of this file should be given to the host so the absent player's view of the universe can continue to update.

If this file is lost, corrupted, or moved to another directory, the player will no longer see what happened in past turns.

## INI File: `STARS.INI`

The `stars.ini` file is stored in the Windows directory. Stars! keeps player options and current game information there. Most entries concern interface state, such as window arrangement, the current scanner view, and overlays.

The following items in `stars.ini` are described as user-changeable:

### Default Password

Set the password in the `[Misc]` section:

```ini
DefaultPassword=Foo
```

Replace `Foo` with the password you generally use. If your opponents do not have access to your `stars.ini` file, you can store your usual password there so Stars! will not prompt you when opening a game file protected by that password.

### Number of Backup Directories

Set the backup count in the `[Misc]` section:

```ini
Backups=N
```

`N` can be any number from `1` to `999`. Backup directories are named `Backup1` through `BackupN`, and old game files are stored according to the turn number. For example, if `Backups=4`, the first turn is saved in `Backup1`, the second in `Backup2`, the third in `Backup3`, the fourth in `Backup4`, and the fifth cycles back to `Backup1`.

By default, Stars! saves one previous turn in a directory named `Backup`.

### When the INI File Is Written

The `stars.ini` file is written the first time you play Stars! and save a game. If you start Stars! and exit from the splash screen without saving, the file is not written.

You can delete the file if necessary, but Stars! will then ask for your serial number again. A missing `stars.ini` file is one of the conditions that causes Stars! to prompt for the serial number.

The extracted Markdown ends here; the remaining raw text was a broken spillover into the copy-protection FAQ that continues in Appendix D.
