from market_sentinel.providers.yahoo.collector import YahooCollector

collector = YahooCollector()

quotes = collector.collect()

print()

print("=" * 60)

for q in quotes:
    print(q)