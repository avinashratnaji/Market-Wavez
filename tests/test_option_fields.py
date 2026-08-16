import json

from market_sentinel.providers.angelone.downloader import InstrumentDownloader

path = InstrumentDownloader().download()

with open(path, encoding="utf-8") as f:
    rows = json.load(f)

count = 0

for row in rows:

    if row.get("instrumenttype") == "OPTIDX":

        print(row)

        count += 1

        if count == 3:
            break