from pprint import pprint

from market_sentinel.providers.angelone.losers import (
    LosersProvider,
)

provider = LosersProvider()

losers = provider.fetch()

print()

print("=" * 80)
print("TOTAL")
print("=" * 80)

print(len(losers))

print()

print("=" * 80)
print("FIRST 10")
print("=" * 80)

for item in losers[:10]:
    pprint(item)