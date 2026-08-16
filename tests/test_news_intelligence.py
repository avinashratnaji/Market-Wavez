from datetime import datetime, timedelta, timezone

from market_sentinel.news.models import NewsArticle
from market_sentinel.providers.news.news_intelligence import NewsPortfolioSelector


def _article(title: str, source: str, score: int, hours_old: int, url: str) -> NewsArticle:
    return NewsArticle(
        title=title,
        summary="Indian equity market impact is being assessed.",
        source=source,
        url=url,
        published_at=datetime.now(timezone.utc) - timedelta(hours=hours_old),
        score=score,
    )


def test_selector_clusters_cross_publisher_coverage_and_explains_choice():
    rbi_primary = _article(
        "RBI keeps repo rate unchanged, signals liquidity support",
        "Economic Times",
        86,
        2,
        "https://example.com/rbi-et",
    )
    rbi_secondary = _article(
        "RBI keeps repo rate unchanged and signals liquidity support",
        "Business Standard",
        82,
        1,
        "https://example.com/rbi-bs",
    )
    earnings = _article(
        "Tata Motors Q1 profit rises on strong domestic demand",
        "Moneycontrol",
        79,
        1,
        "https://example.com/tata-q1",
    )

    assessments = NewsPortfolioSelector().assess([rbi_secondary, earnings, rbi_primary], limit=10)

    assert len(assessments) == 2
    assert assessments[0].article is rbi_primary
    assert assessments[0].event_type == "MONETARY_POLICY"
    assert assessments[0].cluster_size == 2
    assert assessments[0].corroborating_sources == ("Business Standard", "Economic Times")
    assert "RBI" in assessments[0].entities
    assert any("corroborated" in reason for reason in assessments[0].reasons)


def test_selector_returns_varied_representatives_without_mutating_base_scores():
    articles = [
        _article("SEBI revises margin norms for derivatives", "SEBI", 90, 1, "https://example.com/sebi"),
        _article("RBI liquidity update for banks", "RBI", 89, 2, "https://example.com/rbi"),
        _article("Nifty falls as IT shares decline", "Economic Times", 84, 1, "https://example.com/nifty"),
    ]

    selected = NewsPortfolioSelector().select(articles, limit=3)

    assert [article.score for article in selected] == [90, 89, 84]
    assert len({article.url for article in selected}) == 3
