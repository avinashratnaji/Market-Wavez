from market_sentinel.briefs.morning import (
    MorningBriefBuilder,
)

builder = MorningBriefBuilder()

brief = builder.build()

print()

print("=" * 80)
print("HEALTH")
print("=" * 80)

print(brief.health_score)
print(brief.market_sentiment)
print(brief.confidence)

print()

print("=" * 80)
print("INDICES")
print("=" * 80)

for index in brief.indices:
    print(index.telegram_line)

print()

print("=" * 80)
print("GAINERS")
print("=" * 80)

for stock in brief.gainers:
    print(stock.telegram_line)

print()

print("=" * 80)
print("LOSERS")
print("=" * 80)

for stock in brief.losers:
    print(stock.telegram_line)