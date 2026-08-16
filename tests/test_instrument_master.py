import json

from market_sentinel.providers.angelone.downloader import (
    InstrumentDownloader,
)

downloader = InstrumentDownloader()

path = downloader.download()

with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

print("Total records:", len(data))
print()

keywords = [
    "Nifty 50",
    "NIFTY",
    "Nifty Bank",
    "Reliance",
    "TCS",
]

for keyword in keywords:

    print("=" * 100)
    print(keyword)
    print("=" * 100)

    count = 0

    for row in data:

        text = (
            f"{row.get('name','')} "
            f"{row.get('symbol','')}"
        ).lower()

        if keyword.lower() in text:

            print(row)

            count += 1

            if count == 10:
                break

    print()