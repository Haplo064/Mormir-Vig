import time
import json
import ijson
import os
import requests
from datetime import datetime
import math
import pathlib
import ast
import urllib.request
from wand.image import Image

option = "N"
creatures = {}
counter = 0
loop_counter = 0
payload = {'identifiers': []}
image_urls = []
count = 0
prev_cre = False
done_creatures = []


def get_image_url(pld, urls):
    time.sleep(0.1)
    response = requests.post('https://api.scryfall.com/cards/collection', json=pld)
    response_dict = json.loads(response.text)
    for item in response_dict["data"]:
        try:
            if (item["layout"] == "transform" or item["layout"] == "modal_dfc"):
                urls.append({"name": item["name"], "image_url": item["card_faces"][0]["image_uris"]["large"],
                             "cmc": item["cmc"]})
            else:
                urls.append({"name": item["name"], "image_url": item["image_uris"]["large"], "cmc": item["cmc"]})
        except Exception as e:
            print("ERROR: ", e)


# Get Atomic Cards JSON
if os.path.isfile(str(pathlib.Path().resolve()) + "/AtomicCards.json"):
    print("Atomic Cards file located.")
    if (int(datetime.fromtimestamp(
            time.time() - os.path.getmtime(str(pathlib.Path().resolve()) + "/AtomicCards.json")).strftime('%d')) < 10):
        option = "N"
    else:
        print("This file is ",
              datetime.fromtimestamp(
                  time.time() - os.path.getmtime(str(pathlib.Path().resolve()) + "AtomicCards.json")).strftime('%d'),
              " days old, would you like to update it?")
        option = input("(Y/N): ")

if option == "Y" or option == "y" or not os.path.isfile(str(pathlib.Path().resolve()) + "/AtomicCards.json"):
    print("Downloading AtomicCards.json")
    url = "https://mtgjson.com/api/v5/AtomicCards.json"
    response = requests.get(url, stream=True)
    with open(str(pathlib.Path().resolve()) + "/AtomicCards.json", mode="wb") as file:
        file.write(response.content)
    print("Download of AtomicCards.json completed.")

if os.path.isfile(str(pathlib.Path().resolve()) + "/creatures_image_urls.json"):
    print("Previous creature list already exists.")
    prev_cre = True
    file = open(str(pathlib.Path().resolve()) + "/creatures_image_urls.json", 'r', encoding='utf-8')
    crFile = json.load(file)
    for c in crFile:
        ccard = c["name"]
        if (ccard.find("//")):
            ccard = ccard.split("//")[0].rstrip()
        done_creatures.append(ccard)
    image_urls = crFile

print("Loading in creatures")
with open(str(pathlib.Path().resolve()) + "/AtomicCards.json", 'r', encoding='utf-8') as file:
    acFile = ijson.items(file, "data")

    # Grab creatures from Atomic Cards
    for item in acFile:
        if prev_cre:
            for key, value in item.items():
                card = value[0]['name']
                if (value[0]['name'].find("//")):
                    card = value[0]['name'].split("//")[0].rstrip()

                if str(card) not in done_creatures:
                    if ("Creature" in value[0]['type'] and value[0]['legalities'] and "A-" not in card):
                        creatures[card] = value
                        count += 1
        else:
            for key, value in item.items():
                if "Creature" in value[0]['type'] and value[0]['legalities'] and "A-" not in value[0]['name']:
                    creatures[value[0]["name"]] = value
                    count += 1
print("Creatures loaded")

print(count, " creature's image url missing.")
loops = math.ceil(count / 70)

# Download images
for creature in creatures:
    counter += 1
    payload["identifiers"].append({'oracle_id': creatures[creature][0]["identifiers"]["scryfallOracleId"]})
    if counter >= 70:
        get_image_url(payload, image_urls)
        counter = 0
        payload = {'identifiers': []}
        loop_counter += 1
        print(loop_counter, "/", loops)

# Final loop
if counter > 0:
    get_image_url(payload, image_urls)
    loop_counter += 1
    print(loop_counter, "/", loops)

# Save creature image urls json
with open(str(pathlib.Path().resolve()) + "/creatures_image_urls.json", 'w') as fout:
    json.dump(image_urls, fout)

print("Creature image urls complete.")

# Make directories for card art if they don't exist
for i in range(17):
    path = str(pathlib.Path().resolve()) + "/cards/jpg/" + str(i) + "/"
    pathlib.Path(path).mkdir(parents=True, exist_ok=True)
    path = str(pathlib.Path().resolve()) + "/cards/png/" + str(i) + "/"
    pathlib.Path(path).mkdir(parents=True, exist_ok=True)

# Downloading art
with open(str(pathlib.Path().resolve()) + "/creatures_image_urls.json", 'r', encoding='utf-8') as file:
    # Parse the JSON objects one by one
    parser = ast.literal_eval(file.read())

    total = 0

    for item in parser:
        total += 1

    tracker = 0
    for item in parser:
        url = item["image_url"]
        cmc = int(item["cmc"])
        name = item["name"]
        tracker += 1
        save_path = str(pathlib.Path().resolve()) + "/cards/jpg/" + str(
            str(cmc) + '/' + name.replace("'", "").replace('"', "").replace("/", "") + ".jpg")
        if (os.path.isfile(save_path)):
            print(tracker, "/", total, " (", f"{tracker / total * 100:.2f}", "%) ", name, " already exists, skipping.")
        else:
            urllib.request.urlretrieve(url, save_path)
            print(tracker, "/", total, " (", f"{tracker / total * 100:.2f}", "%) card arts downloaded.")
    tracker = 0

    # get count of images in sub-folders
    imageTotal = 0
    for i in range(17):
        imageTotal += len(os.listdir(str(pathlib.Path().resolve()) + "/cards/jpg/" + str(i) + "/"))

    # Convert Images
    base_width = 384
    for i in range(17):
        for image in os.listdir(str(pathlib.Path().resolve()) + "/cards/jpg/" + str(i) + "/"):
            tracker += 1
            fileP = str(pathlib.Path().resolve()) + "/cards/png/" + str(i) + "/" + str(os.path.basename(image))[
                                                                                   :-4] + ".png"
            if (os.path.isfile(fileP)):
                print(tracker, "/", imageTotal, " (", f"{tracker / total * 100:.2f}", "%) | Already Exists")

            else:
                with Image(filename=str(pathlib.Path().resolve()) + "/cards/jpg/" + str(i) + "/" + image) as img:
                    y = math.ceil(img.height * (384 / img.width))
                    img.resize(width=384, height=y)
                    img.format = 'png'
                    img.transform_colorspace("gray")
                    img.save(filename=str(pathlib.Path().resolve()) + "/cards/png/" + str(i) + "/" + str(
                        os.path.basename(image))[:-4] + ".png")

                    print(tracker, "/", imageTotal, " (", f"{tracker / total * 100:.2f}", "%) | Saved ",
                          str(pathlib.Path().resolve()) + "/cards/png/" + str(i) + "/" + str(os.path.basename(image))[
                                                                                         :-4] + ".png")
