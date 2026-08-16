from market_sentinel.providers.angelone.sectors import (
    SectorProvider,
)

provider = SectorProvider()

sectors = provider.fetch()

print()

print("=" * 80)
print("TOTAL")
print("=" * 80)

print(len(sectors))

print()

print("=" * 80)
print("SECTORS")
print("=" * 80)

for sector in sectors:
    print(sector.telegram_line)