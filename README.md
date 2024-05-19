# Redeem Whiteout Survival Gift Codes

This python script allows to redeem gift codes for Whiteout Survival in an
automated way for a number of players (e.g., all players in an alliance).

It utilizes the REST API that the web page uses that iOS require to redeem their
codes as the app doesn't have an option for it.

## Usage

The script should be called from the command line and only requires to supply the gift code.
The player IDs must be supplied in a json file that per-default is assumed to be `player.json`.
A sample is provided to understand the structure.

`python redeem_code.py -c <gift-code>`

## Notes on the redemption endpoint

The REST API implementation is not exactly straight-forward because it appears the devs try to
hide it so that it is not used for automation scripts like this one is.

Every request is signed with a key that is calculated in a special way. Looking at the JavaScript
code of the page only shows some obfuscated logic. What essentially happens is: The data that is part
of the request is converted into a URL request string, a salt appended and then hashed using MD5.

A request payload may look like this:
```json
{
    "fid": 12345678, 
    "time": 1716126948359,
    "sign": ???
}
```

Now, the sign is calculated using the following logic (pseudo-code) and appended to the payload:
```
("fid=12345678&time=1716126948359" + "tB87#kPtkxqOS2").md5()
```

## Contributions

I don't expect many contributions but if you have suggestions on how to improve this, feel free
to open an issue and send a PR my way.