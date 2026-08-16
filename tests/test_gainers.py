from pprint import pprint

from market_sentinel.providers.angelone.gainers import (
    GainersProvider,
)

provider = GainersProvider()

gainers = provider.fetch()

print()

print("=" * 80)
print("TOTAL")
print("=" * 80)

print(len(gainers))

print()

print("=" * 80)
print("FIRST 10")
print("=" * 80)

for item in gainers[:10]:
    pprint(item)