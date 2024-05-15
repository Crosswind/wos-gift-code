# Redeem Whiteout Survival Gift Codes

This python script allows to redeem gift codes for Whiteout Survival in an
automated way for a number of players (e.g., all players in an alliance).

It utilizes the web page from CenturyGames that is typically used by iOS users
because they cannot redeem gift codes in the app itself. While it was difficult
to extract the exact API calls the page is doing I opted for automating it using
the Selenium framework. Selenium is typically used for testing because it allows
to mimic user interactions with a web site. This creates an obvious downside:
The script only is required to run in attended mode on a personal computer and 
currently cannot run on a headless server.

The way it has been implemented works perfectly for my own use case but is far from
perfect. It would ultimately be best if this could run entireliy without Selenium and
call the APIs directly. I suppose that Century Games won't be of much help here so I'll
stick with the current implementation for the time being.

## Usage

The script should be called from the command line and only requires to supply the gift code.
The player IDs must be supplied in a json file that per-default is assumed to be `player.json`.
A sample is provided to understand the structure.

`python redeem_code.py -c <gift-code>`

## Contributions

I don't expect many contributions but if you have suggestions on how to improve this, feel free
to open an issue and send a PR my way.