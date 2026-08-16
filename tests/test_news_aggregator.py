from market_sentinel.news.aggregator import (
    NewsAggregator,
)

from market_sentinel.news.sources.yahoo_finance.provider import (
    YahooFinanceProvider,
)

aggregator = NewsAggregator(

    providers=[

        YahooFinanceProvider(),

    ],

)

articles = aggregator.fetch()

print()

print("=" * 80)
print("TOTAL ARTICLES")
print("=" * 80)

print(len(articles))

print()

print("=" * 80)
print("FIRST 10")
print("=" * 80)

for article in articles[:20]:

    print(
        article.importance,
        article.category.value,
        article.title,
        article.source,
        article.url
    )