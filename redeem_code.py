"""
This script is a Selenium bot that redeems a gift code
for the mobile game Whiteout Survival by using their website

It requires an input file that contains all player IDs and 
tracks its progress in an output file to be able to continue
in case it runs into errors without retrying to redeem a code
for everyone

This script currently only supports Mac OS because it is based
on the Safari browser
"""
import argparse
import json
import sys

from selenium.webdriver.support import ui
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By


def save_results(filename, results_to_save):
    """
    This function was needed to make sure we can save progress on TimeoutExceptions
    """
    with open(filename, 'w', encoding="utf-8") as fp:
        json.dump(results_to_save, fp)


# Handle arguments the script is called with
parser = argparse.ArgumentParser()
parser.add_argument('-c', '--code', required=True)
parser.add_argument('-f', '--player-file',
                    dest='player_file', default='player.json')
parser.add_argument('-r', '--results-file',
                    dest='results_file', default='results.json')
parser.add_argument('--restart', type=bool, dest='restart', default=False)
args = parser.parse_args()

# Open and read the user files
with open(args.player_file, encoding="utf-8") as player_file:
    players = json.loads(player_file.read())

with open(args.results_file, encoding="utf-8") as results_file:
    results = json.loads(results_file.read())

# Retrieve the result set if it exists or create an empty one
# We make sure that we get a view of the dictionary so we can modify
# it in our code and simply write the entire result list to file again later
found_item = next(
    (result for result in results if result["code"] == args.code), None)

if found_item is None:
    new_item = {"code": args.code, "status": {}}
    results.append(new_item)
    result = new_item
else:
    result = found_item

# Setup Selenium
URL = "https://wos-giftcode.centurygame.com"
driver = webdriver.Safari()
driver.get(URL)
wait = ui.WebDriverWait(driver, 30)

# Some variables that are used to tracking progress
session_counter = 1
counter_successfully_claimed = 0
counter_already_claimed = 0
counter_error = 0

for player in players:

    # Check if the code has been redeemed for this player already
    # Continue to the next iteration if it has been
    if result["status"].get(player["id"]) == "Successful":
        continue

    # This is necessary because we reload the page every 5 players
    # and the website isn't sometimes ready before we continue
    try:
        wait.until(lambda driver: driver.find_element(
            By.XPATH, "//input[contains(@placeholder,'Player ID')]"))
    except TimeoutException as e:
        print("Timeout Exception")
        save_results(args.results_file, results)
        sys.exit(1)

    # Enter the player ID
    player_id_input = driver.find_element(
        By.XPATH, "//input[contains(@placeholder,'Player ID')]")
    player_id_input.clear()
    player_id_input.send_keys(player["id"])

    # Login the player by using the login button
    # We are using the Selenium wait feature to make sure the player is logged in before we continue
    # We know the player is logged in, once the exit icon appears
    login_button = driver.find_element(By.CLASS_NAME, "login_btn").click()
    try:
        wait.until(lambda driver: driver.find_element(
            By.CLASS_NAME, "exit_icon"))
    except TimeoutException as e:
        print("Timeout Exception")
        save_results(args.results_file, results)
        sys.exit(1)

    # Now we record the login name for later
    player["name"] = driver.find_element(By.CLASS_NAME, "name").text

    # Enter the gift code and hit confirm
    # We again wait until the request is sent before we continue
    gift_code_input = driver.find_element(
        By.XPATH, "//input[contains(@placeholder,'Enter Gift Code')]")
    gift_code_input.clear()
    gift_code_input.send_keys(args.code)
    redeem_button = driver.find_element(By.CLASS_NAME, "exchange_btn").click()
    try:
        wait.until(lambda driver: driver.find_element(
            By.CLASS_NAME, "confirm_btn"))
    except TimeoutException as e:
        print("Timeout Exception")
        save_results(args.results_file, results)
        sys.exit(1)
    player["status"] = driver.find_element(By.CLASS_NAME, "msg").text

    # In case the gift code is broken, exit straight away
    if player["status"] == "Gift Code not found!":
        print("The gift code doesn't exist!")
        sys.exit(1)
    elif player["status"] == "Expired, unable to claim.":
        print("The gift code is expired!")
        sys.exit(1)
    elif player["status"] == "Already claimed, unable to claim again.":
        counter_already_claimed += 1
        result["status"][player["id"]] = "Successful"
    elif player["status"] == "Redeemed, please claim the rewards in your mail!":
        counter_successfully_claimed += 1
        result["status"][player["id"]] = "Successful"
    else:
        result["status"][player["id"]] = "Unsuccessful"
        counter_error += 1

    driver.find_element(By.CLASS_NAME, "confirm_btn").click()

    # Now we log the user out again before we continue with the next one
    driver.find_element(By.CLASS_NAME, "exit_icon").click()

    # Refresh the webpage every 5 players to avoid getting soft-banned at some point
    if session_counter % 5 == 0:
        driver.refresh()

    session_counter += 1

save_results(args.results_file, results)

# Print general stats
print("\nSuccessfully claimed gift code for " + str(counter_successfully_claimed) + " players.\n" +
      str(counter_already_claimed) + " had already claimed their gift. \nErrors ocurred for " +
      str(counter_error) + " players.")
