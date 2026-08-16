import json

from market_sentinel.providers.angelone.downloader import (
    InstrumentDownloader,
)

downloader = InstrumentDownloader()

path = downloader.download()

with open(path, "r", encoding="utf-8") as f:
    rows = json.load(f)

for row in rows:

    text = (
        f"{row.get('name','')} "
        f"{row.get('symbol','')}"
    ).upper()

    if "FIN" in text:

        print(row)