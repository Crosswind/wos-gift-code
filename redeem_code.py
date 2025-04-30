"""
This script redeems a gift code for players of the mobile game
Whiteout Survival by using their API

It requires an input file that contains all player IDs and
tracks its progress in an output file to be able to continue
in case it runs into errors without retrying to redeem a code
for everyone
"""

import argparse
import hashlib
import json
import sys
import time
import base64
import ddddocr
from os.path import exists

import requests
from requests.adapters import HTTPAdapter, Retry

# Handle arguments the script is called with
parser = argparse.ArgumentParser()
parser.add_argument("-c", "--code", required=True)
parser.add_argument("-f", "--player-file", dest="player_file", default="player.json")
parser.add_argument("-r", "--results-file", dest="results_file", default="results.json")
parser.add_argument("--restart", dest="restart", action="store_true")
args = parser.parse_args()

# Open and read the user files
with open(args.player_file, encoding="utf-8") as player_file:
    players = json.loads(player_file.read())

# Initalize results to not error if no results file exists yet
results = []

# If a results file exists, load it
if exists(args.results_file):
    with open(args.results_file, encoding="utf-8") as results_file:
        results = json.loads(results_file.read())

# Retrieve the result set if it exists or create an empty one
# We make sure that we get a view of the dictionary so we can modify
# it in our code and simply write the entire result list to file again later
found_item = next((result for result in results if result["code"] == args.code), None)

if found_item is None:
    print("New code: " + args.code + " adding to results file and processing.")
    new_item = {"code": args.code, "status": {}}
    results.append(new_item)
    result = new_item
else:
    result = found_item

# Some variables that are used to tracking progress
counter_successfully_claimed = 0
counter_already_claimed = 0
counter_error = 0

URL = "https://wos-giftcode-api.centurygame.com/api"
# The salt is appended to the string that is then signed using md5 and sent as part of the request
SALT = "tB87#kPtkxqOS2"
HTTP_HEADER = {
    "Content-Type": "application/x-www-form-urlencoded",
    "Accept": "application/json",
}

i = 0

# Enable retry login and backoff behavior so if you have a large number of players (> 30) it'll not fail
# Default rate limits of WOS API is 30 in 1 min.
r = requests.Session()
retry_config = Retry(
    total=5, backoff_factor=1, status_forcelist=[429], allowed_methods=False
)
r.mount("https://", HTTPAdapter(max_retries=retry_config))


def analyze_captcha_image_and_change_2_text(base64_string):
    # Remove base64 string header
    if "," in base64_string:
        base64_string = base64_string.split(",")[1]

    # Convert base64 to image data
    img_data = base64.b64decode(base64_string)

    # Initialize ddddocr
    ocr = ddddocr.DdddOcr(show_ad=False)

    # Recognize captcha
    result = ocr.classification(img_data)

    # Convert to uppercase
    text = result.upper()

    return text


for player in players:

    # Print progress bar
    i += 1

    print(
        "\x1b[K"
        + str(i)
        + "/"
        + str(len(players))
        + " complete. Redeeming for "
        + player["original_name"],
        end="\r",
        flush=True,
    )

    # Check if the code has been redeemed for this player already
    # Continue to the next iteration if it has been
    if result["status"].get(player["id"]) == "Successful" and not args.restart:
        counter_already_claimed += 1
        continue

    # This is necessary because we reload the page every 5 players
    # and the website isn't sometimes ready before we continue
    timestamp = time.time_ns()
    request_data = {"fid": player["id"], "time": timestamp}
    request_data["sign"] = hashlib.md5(
        (
            "fid=" + request_data["fid"] + "&time=" + str(request_data["time"]) + SALT
        ).encode("utf-8")
    ).hexdigest()

    # Login the player
    # It is enough to send the POST request, we don't need to store any cookies/session tokens
    # to authenticate during the next request
    login_request = r.post(
        URL + "/player", data=request_data, headers=HTTP_HEADER, timeout=30
    )
    login_response = login_request.json()

    # Login failed for user, report, count error and continue gracefully to complete all other players
    if login_response["msg"] != "success":
        print(
            "Login not possible for player: "
            + player["original_name"]
            + " / "
            + player["id"]
            + " - validate their player ID. Skipping."
        )
        counter_error += 1
        continue

    captcha_data = {"fid": player["id"], "time": timestamp, "init": "0"}
    captcha_data["sign"] = hashlib.md5(
        (
            "fid="
            + captcha_data["fid"]
            + "&init="
            + captcha_data["init"]
            + "&time="
            + str(captcha_data["time"])
            + SALT
        ).encode("utf-8")
    ).hexdigest()

    # Login the player - get captcha
    captcha_request = r.post(
        URL + "/captcha", data=captcha_data, headers=HTTP_HEADER, timeout=30
    )
    captcha_response = captcha_request.json()

    # Login failed for user, report, count error and continue gracefully to complete all other players
    if captcha_response["msg"] != "SUCCESS":
        print(
            "Login not possible for player: "
            + player["original_name"]
            + " / "
            + player["id"]
            + " - Captcha failed. Skipping."
        )
        counter_error += 1
        continue

    captcha_img = captcha_response["data"]["img"]

    # Create the request data that contains the signature and the code
    request_data["captcha_code"] = analyze_captcha_image_and_change_2_text(captcha_img)
    request_data["cdk"] = args.code
    request_data["time"] = str(time.time_ns())
    request_data["sign"] = hashlib.md5(
        (
            "captcha_code="
            + request_data["captcha_code"]
            + "&cdk="
            + request_data["cdk"]
            + "&fid="
            + request_data["fid"]
            + "&time="
            + str(request_data["time"])
            + SALT
        ).encode("utf-8")
    ).hexdigest()

    # Send the gif code redemption request
    redeem_request = r.post(
        URL + "/gift_code", data=request_data, headers=HTTP_HEADER, timeout=30
    )
    redeem_response = redeem_request.json()

    # In case the gift code is broken, exit straight away
    if redeem_response["err_code"] == 40014:
        print("\nThe gift code doesn't exist!")
        sys.exit(1)
    elif redeem_response["err_code"] == 40007:
        print("\nThe gift code is expired!")
        sys.exit(1)
    elif redeem_response["err_code"] == 40008:  # ALREADY CLAIMED
        counter_already_claimed += 1
        result["status"][player["id"]] = "Successful"
    elif redeem_response["err_code"] == 20000:  # SUCCESSFULLY CLAIMED
        counter_successfully_claimed += 1
        result["status"][player["id"]] = "Successful"
    elif redeem_response["err_code"] == 40004:  # TIMEOUT RETRY
        result["status"][player["id"]] = "Unsuccessful"
    elif redeem_response["err_code"] == 40101:  # CAPTCHA CHECK TOO FREQUENT.
        result["status"][player["id"]] = "Unsuccessful"
    elif redeem_response["err_code"] == 40103:  # CAPTCHA CHECK ERROR.
        result["status"][player["id"]] = "Unsuccessful"
    else:
        result["status"][player["id"]] = "Unsuccessful"
        print("\nError occurred: " + str(redeem_response))
        counter_error += 1

with open(args.results_file, "w", encoding="utf-8") as fp:
    json.dump(results, fp)

# Print general stats
print(
    "\nSuccessfully claimed gift code for "
    + str(counter_successfully_claimed)
    + " players.\n"
    + str(counter_already_claimed)
    + " had already claimed their gift. \nErrors ocurred for "
    + str(counter_error)
    + " players."
)
