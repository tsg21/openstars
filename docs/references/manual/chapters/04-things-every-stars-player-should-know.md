# 4. Things Every Stars! Player Should Know

## Tuning Stars! to Your Display Resolution

The higher your screen resolution, the better Stars! will look. However, it will run on any color VGA display.

### 1024 by 768, or Better

For maximum playing pleasure:

- Use `View (Window Layout > Large)`.
- If you use large fonts, you may need to specify `View (Window Layout > Medium)`.

### 800 by 600

This is the minimum recommended resolution.

1. Choose `View (Window Layout > Medium)`. If you're using large fonts, you may find that the small window layout works better for you.
2. Resize each of the windows to optimize the information you need to see at a glance.
3. If the screen still seems too cramped, try hiding the toolbar using `View (Toolbar)`. Most toolbar functions are available through shortcut keys.

### 640 by 480, VGA

This is the minimum required resolution.

1. Use `View (Window Layout > Small)`.
2. Resize each of the windows to optimize the information you need to see at a glance.
3. Collapse tiles in the Command pane, expanding them when needed.
4. If the screen still seems too cramped, try hiding the toolbar using `View (Toolbar)`. Most toolbar functions are available through shortcut keys.

## Replaying a Previous Turn

Stars! allows you to save previous turns in case you need to resubmit a turn to the host or replay the current turn. You can specify saving up to 999 turns using the `Backups` option in the `stars.ini` file. If you don't specify the number of turns to back up, Stars! backs up only the previous turn. Once you save and submit, Stars! saves the current turn as the most recent backup copy.

To start a turn using data from a previous turn, for example the last turn played:

1. Copy all files for the current game from the backup directory into the playing directory. For example, if you originally saved the game under the name `Nonstop`, copy all files with `Nonstop` as the prefix. To ensure that you are choosing the correct files, check the date and time stamp on the backup directory.
2. Choose `Open Game` or `File (Open)`. Select the player turn file, for example `nonstop.m1`, and confirm. You should be back where you started, although the universe will reflect the current positions of other players.

## Saving Your Game: What It Means

### Default Save Behavior

By default, saving a game saves only the current state of the current turn. The previous turn's data is saved in a directory called `Backup` under the directory in which you're saving the game. Stars! creates the `Backup` directory automatically. Each time you generate a turn, the old data in the `Backup` directory is overwritten with the previous turn's data.

### Saving the Current State of Your Game

Use `File (Save)` to save the current state of your game. This is useful if you need to exit the game before you finish your turn. When you restart Stars!, click on `Continue Game` to resume where you left off.

If you close the game before saving, you'll be asked whether you wish to save before exiting.

### Saving More than One Previous Turn

If you'd like to save more than one previous turn for review or any other purpose:

1. Open the `stars.ini` file for editing. It's a plain text file located in your Windows directory.
2. Under the `[MISC]` section, set the `Backups` option to a number of turns between 1 and 999. If the `Backups` option isn't present, type it in. For example:

```ini
Backups=50
```

Backup directories will be named `Backup1` to `BackupN`. Old game files will be stored in the backup directories according to the turn number. For example, when `Backups=4`, the first turn is backed up to `Backup1`, the second to `Backup2`, the third to `Backup3`, the fourth to `Backup4`, the fifth to `Backup1`, and so on.

The `stars.ini` file is written into your Windows directory the first time you save a Stars! game. It doesn't exist before that time.

### Save and Submit

Multi-player games only.

Use `File (Save and Submit)` to save the current state of your game and submit your turn. In multi-player games, this marks your turn as finished so the host can auto-generate. `Save` does not.

If you close the game before saving, you'll be asked whether you wish to save and submit your turn before exiting.

## Exiting the Game

Select `File (Exit)` or `File (Close)`. If you've made changes since the beginning of the turn, Stars! will prompt you to save or, if you're in a multi-player game, to save and submit your turn.

### Exiting Stars! the First Time

Important: The first time you play Stars!, exit using the `File (Exit)` menu item. This writes the `stars.ini` file to the Windows directory, saving game options and helping to prevent that pesky serial number dialog from appearing again.

### Exiting Stars! to Erase Changes

If you want to erase the changes you've made that turn before you submit:

1. Choose `File (Close)` without saving.
2. Select `Open Game` from the opening screen, then choose your player file from the Open File dialog. You'll be back at the start of the turn you just left.

### Save vs. Save and Submit

Multi-player games only.

Use `File (Save and Submit)` to save the current state of your game and submit your turn. In multi-player games, this marks your turn as finished so the host can auto-generate. `Save` does not.

If you close the game before saving, you'll be asked whether you wish to save and submit your turn before exiting.

## Options for Launching Stars!

Stars! can be launched from a DOS or Windows command line, using the `Stars!` command by itself or with a variety of options. When using an option, you must also supply either a player or host filename as an argument. You can also supply only the player or host filename without any other options.

With or without options, supplying the filename causes Stars! to start without displaying the splash screen.

- `-s`: Start with battle sound effects turned off.
- `-m`: Start with game music turned off.
- `-t`: Try, then exit. If you specify a player file, this opens the newly generated turn. If the turn hasn't been generated yet, Stars! exits. If you specify a host file, this checks to see whether all players have submitted their changes for the turn. If they have, Stars! generates the new turn and exits. Otherwise, it just exits.
- `-w`: Wait. If you specify a host file, this auto-generates the new turn as soon as all players have submitted their changes. If you specify a player file, this waits for the new turn to be generated. This option does not cause Stars! to exit.
- `-g`: Generate and exit. Specify a host file only. This forces the turn to generate regardless of whether all players have submitted changes, then exits. You can't load a player file with this option.
- `-p password`: Supplies the password on the command line. You can use this with a host file or a password-protected player file.
- `-x`: Exit Windows when Stars! exits. This is a good match with the `-b` option if you wish to create a script that automatically starts Windows, generates the new turn, then exits Windows.
- `-b gamelist_file`: Generate turns for each game listed in the supplied file.
- `-a game.def`: Create a new game or universe based on the contents of `game.def`.
- `-h`: Causes Stars! to always ask you for a password when you open a turn file. This is especially useful for hot-seat play.

The `-x` flag is for 16-bit Windows only, versions 3.1 or 3.11. Behavior of the `-x` option on OS/2, Windows NT, or Windows 95 is undefined and probably not what you want.

### Examples

```text
stars! Filename
```

Load a player or host file, starting the game without the splash screen.

```text
stars! -w gamename.hst
```

Load the host file and enter auto-generate mode.

```text
stars! -w gamename.mN
```

Load the specified player file and wait for the host to generate a new turn.

```text
stars! -t gamename.mN
```

Load the specified player file; quit if the host has not yet generated a new turn.

```text
stars! -g gamename.hst
```

Load the host file, force a new turn, and quit.

```text
stars! -w -g gamename.hst
```

Load the host file, wait for all players to submit turns, generate, and quit.

```text
stars! -t -g gamename.hst
```

Load the host file, generate a new turn only if all players have submitted turns, then quit. If it generates the turn, the return value is `1`; if the turn is not generated, the value is `0`.

```text
stars! -t -b gamelist_file
```

Conditionally generate turns for a list of games.

```text
stars! -x -b gamelist_file
```

Generate turns for each game listed in the supplied file, then exit Windows. Useful for BBS play.

If your BBS is OS/2-, NT-, or Windows-based, you can launch Stars! with the `-b gamelist_file` parameter to batch-generate turns for multiple games. Stars! will automatically exit when the last turn has been generated. The file listing the games must contain one game name per line, including the full path:

```text
c:\games\stars!\play\frenzy.hst
c:\games\stars!\play\game.hst
c:\user\jeff\stars!\killer.hst
```

You can name this games list file anything you want. If you are running a DOS-based BBS but have Windows installed on the machine, you can launch Windows and Stars! from a nightly maintenance script similar to this:

```text
win c:\games\stars!\stars!.exe -x -b c:\games\stars!\gamelist.txt
```

This launches Windows and Stars!, generates a turn for each game listed in `gamelist.txt`, then exits Stars! and Windows. This method is optimal for Windows 3.1.

If you have Windows for Workgroups installed, Windows 3.11, you may want to use the `win /n` option:

```text
win /n c:\games\stars!\stars!.exe -x -b c:\games\stars!\gamelist.txt
```

This prevents Windows from loading any of its network drivers and suppresses its login prompt. If you only need to generate a turn for a single game, you can still use the `-g gamename.hst` parameter with or without `-x`. Use `-x` only with Windows 3.1 or 3.11.

## Copy Protection

### Save Your Serial Number

The first time you run Stars!, you will be asked to enter your unique serial number. The number is printed on two labels enclosed in the pack. It is very important that you keep the serial number where you can find it later.

Stars! may ask for the number again if:

- You reinstall Stars!.
- You change your computer's configuration.
- You install a Stars! upgrade.

### One Computer, One Serial Number

Each computer running Stars! must use a unique serial number. Given this, the copy protection activates only in the following situations:

- When you cancel the serial number dialog.
- When players using the same serial number submit turns created on two different computers. This includes submitting turns from networked computers sharing a serial number. If you want to submit turns from different machines on a network, each of those machines must have a copy of Stars! installed with a unique serial number.
- When one person submits turns for two or more player positions from different computers that share the same Stars! serial number.

In every case, Stars! will give you a chance to enter a unique serial number and continue play normally.

### How the Copy Protection Works

Stars! is played by submitting player log files to the host, either a human or the game itself. Each log file is tagged with the serial number for the copy of Stars! used to generate the file, and a fingerprint of the computer on which the game was installed. If the Stars! host receives two or more log files with different computer fingerprints and the same serial number, it assumes that all the players associated with those log files are guilty of software piracy, and activates the copy protection for those players. Honest players are unaffected.

The copy protection makes the game unplayable for the guilty parties until each player enters a unique serial number. As soon as each player submits turns with a unique serial number, the copy protection deactivates.

### The Host Doesn't Need a Serial Number

A host can use the same serial number as one other player without affecting the host or the player. This allows you to host and play from the same copy of Stars!

### Computers Running More than One Version of Windows

If you are running some combination of Windows 95, NT, or 3.x on a single computer, you will be asked for a serial number the first time you run Stars! under each version of Windows. After that, you should only be prompted for the number if you change your system configuration or delete the `stars.ini` file from the Windows directory. Each version of Windows will have its own directory containing Windows system software. By default, this directory is named `Windows`. You may have named it something different on your system.

## The Stars! Screen

You can't manage an empire with a stick and whistle.
