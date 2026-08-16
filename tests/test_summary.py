from market_sentinel.news.aggregator import NewsAggregator
from market_sentinel.news.classifier import NewsClassifier
from market_sentinel.news.entity_extractor import EntityExtractor
from market_sentinel.news.sector_mapper import SectorMapper
from market_sentinel.news.scoring_engine import NewsScoringEngine
from market_sentinel.news.summary_builder import NewsSummaryBuilder

from market_sentinel.news.sources.yahoo_finance.provider import (
    YahooFinanceProvider,
)

articles = NewsAggregator(
    [
        YahooFinanceProvider(),
    ]
).fetch()

articles = NewsClassifier.classify(articles)
articles = EntityExtractor.extract(articles)
articles = SectorMapper.map(articles)
articles = NewsScoringEngine.score(articles)

top = NewsSummaryBuilder.build(
    articles,
    limit=10,
)

print()
print("=" * 80)
print("TOP MARKET MOVERS")
print("=" * 80)

for article in top:

    print(
        f"[{article.score:03d}] "
        f"[{article.category.value}] "
        f"{', '.join(article.entities)}"
    )

    print(article.title)

    print()