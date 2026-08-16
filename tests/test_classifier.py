from market_sentinel.news.aggregator import (
    NewsAggregator,
)

from market_sentinel.news.classifier import (
    NewsClassifier,
)

from market_sentinel.news.sources.yahoo_finance.provider import (
    YahooFinanceProvider,
)

aggregator = NewsAggregator(

    [

        YahooFinanceProvider(),

    ]

)

articles = aggregator.fetch()

articles = NewsClassifier.classify(

    articles,

)

print()

print("=" * 80)
print("FIRST 20")
print("=" * 80)

for article in articles[:20]:

    print(
        f"[{article.importance:02d}] "
        f"[{article.category.value}] "
        f"{article.title}"
    )