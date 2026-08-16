from market_sentinel.news.aggregator import NewsAggregator
from market_sentinel.news.classifier import NewsClassifier
from market_sentinel.news.entity_extractor import EntityExtractor
from market_sentinel.news.scoring_engine import NewsScoringEngine
from market_sentinel.news.sector_mapper import (
    SectorMapper,
)
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

print()
print("=" * 80)
print("TOP 20")
print("=" * 80)

for article in articles[:20]:
    print(
        f"[{article.score:03d}] "
        f"[{article.category.value}] "
        f"{','.join(article.sectors) if article.sectors else '-'} "
        f"{article.title}"
    )