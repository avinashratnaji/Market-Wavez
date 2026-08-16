from market_sentinel.providers.angelone.downloader import (
    InstrumentDownloader,
)

downloader = InstrumentDownloader()

path = downloader.download()

print(path)