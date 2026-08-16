from market_sentinel.news.aggregator import NewsAggregator
from market_sentinel.news.sources.yahoo_finance.provider import YahooFinanceProvider

articles = NewsAggregator(
    [YahooFinanceProvider()]
).fetch()

for article in articles[:20]:

    print()

    print(article.title)

    print(article.entities)