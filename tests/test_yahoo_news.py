from market_sentinel.news.sources.yahoo_finance.provider import (
    YahooFinanceProvider,
)

provider = YahooFinanceProvider()

articles = provider.fetch()

print()
print("=" * 80)
print("TOTAL")
print("=" * 80)
print(len(articles))

print()

for article in articles[:10]:

    print(article.title)
    print(article.url)
    print()