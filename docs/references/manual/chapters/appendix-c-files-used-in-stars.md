# Appendix C. Files Used in Stars!

### HOST FILE — GAMENAME.HST

This is the file containing the information the host program needs for a specific game. This file should be available only to the person playing the host.

### UNIVERSE FILE — GAMENAME.XY

This is the universe file, containing information about the positions of all the planets. It does not change over the course of the game. Individual players as well as the host program need to have this file available to them.

### TURN FILE — GAMENAME.MN

These are the turn files. N is a number from 1 to 16, representing the player number. This is the individual file for each player, containing all the data about that player’s race and state of the player’s empire at the beginning of a turn.

### RACE DESCRIPTION FILE — NAME.RN FILES

This file contains a race description created and saved using the Custom Race Wizard. N can be any number (you can actually use any extension, the default is r1.) You can specify a race file for each non-computer player in the game from step 2 of the New Advanced Game dialog. Once the universe has been created the race file is no longer needed. If you open this file using File (Open), the Custom Race Wizard opens.

The extension of.r1 is the default, and is not required.

### LOG FILE —- GAMENAME.XN

These are the log files. N is a number from 1 to 16, representing the player number. This is the log of orders given by a player for the current turn. This file is submitted, either automatically or manually, to the host program. The host adds the changes to the player’s.mN file, and returns that file to the player when the new turn is generated. The host needs these files to update the information about each player from the.hst file before turn generation.

Each time the player opens (or continues) a game, the.mN file is loaded. If a corresponding log file exists, it will also be loaded to update the game’s current state.

### HISTORY FILE —- GAMENAME.HN

These are history files. N is a number from 1 to 16, representing the player number. This file is created by the player as he sees universe data. It is a history of the things the player has seen or learned on previous turns. Typically, only the player maintains a copy of this file. If a player will be absent for a few turns, and wishes to be temporarily replaced by the Housekeeper AI, a copy of this file should be given to the host so the absent player’s view of the universe can be updated.

If this file is lost, corrupted or moved to another directory, the player will not see what’s been done in past turns.

### INI FILE — STARS.INI

The stars.ini file is located in the windows directory. Stars! stores player options and current game information in this file. Most of the items in the file have to do with relatively unimportant stuff like the arrangement and windows, the current scanner view and overlays.

The following items in the stars.ini are user changeable:

Default Password

Set the password in the [Misc] section of stars.ini:

DefaultPassword=Foo

Where Foo is whatever password you generally use. If you are sure that your opponents will not have access to your stars.ini file you can set this to your

password. Whenever you open a game file that is protected by this password you will not be prompted to enter it.

Number of Backup Directories

Set this option in the [Misc] section of stars.ini:

Backups=N

Where N is a number between 1 and 999. Backup directories will be named Backup1 to BackupN and old game files will be stored there according to the turn number. For example with backups=4 then the first turn would be backed up to the directory backup1, the second to backup2, the third to backup3, the fourth to backup4, the fifth to backup1 and so on.

By default Stars! saves one previous turn’s data in a directory it creates named Backup.

When the ini file is Written

The stars.ini file is written the first time you play Stars and save a game. If you start Stars! and exit from the splash screen without saving a game, the file isn’t written. You can delete this file, if you find a need. This will cause Stars! to ask for your serial number again, however. An absent ini file is just one of the conditions that causes Stars! to ask you for your serial number.

- Protection, p
