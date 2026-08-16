from datetime import datetime, timedelta, timezone

from market_sentinel.news.models import NewsArticle
from market_sentinel.providers.news.global_impact_news import GlobalImpactNews


def _article(title: str, source: str = "Reuters") -> NewsArticle:
    return NewsArticle(
        title=title,
        summary="",
        source=source,
        url="https://example.com/article",
        published_at=datetime.now(timezone.utc) - timedelta(hours=2),
    )


def test_global_impact_rejects_cnbc_and_generic_geopolitics():
    collector = GlobalImpactNews(feeds=[])

    assert collector._score(_article("Oil rises as supply risk grows", source="CNBC")) == 0
    assert collector._score(_article("Iran tensions continue")) == 0


def test_global_impact_accepts_reuters_crude_supply_shock():
    collector = GlobalImpactNews(feeds=[])

    assert collector._score(_article("Brent crude oil rises after OPEC supply disruption")) >= collector.MINIMUM_SCORE
