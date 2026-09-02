"""Quality-filtered crypto news for the market brief."""

from __future__ import annotations

from datetime import datetime, timezone
from collections import Counter

from market_sentinel.news.models import NewsArticle
from market_sentinel.providers.news.news_intelligence import NewsPortfolioSelector
from market_sentinel.providers.rss_collector import RSSCollector


class CryptoMarketNews:
    """Select fresh, market-relevant crypto events from independent sources."""

    FEEDS = (
        "https://www.coindesk.com/arc/outboundfeeds/rss/",
        "https://cointelegraph.com/rss",
        "https://decrypt.co/feed",
        "https://www.theblock.co/rss.xml",
        "https://news.google.com/rss/search?q=(bitcoin+OR+ethereum+OR+crypto+markets+OR+stablecoin)+when:2d&hl=en-IN&gl=IN&ceid=IN:en",
        "https://news.google.com/rss/search?q=(bitcoin+ETF+OR+crypto+regulation+OR+stablecoin+OR+ethereum)+when:2d&hl=en-US&gl=US&ceid=US:en",
    )
    TRUSTED = frozenset({
        "CoinDesk", "Cointelegraph", "Reuters", "BBC News", "Bloomberg",
        "Financial Times", "Decrypt", "The Block", "DL News", "Yahoo Finance",
        "The Wall Street Journal", "Wall Street Journal",
    })
    SIGNALS = {
        "etf": 28, "sec": 30, "regulation": 28, "stablecoin": 25,
        "bitcoin": 18, "ethereum": 16, "hack": 30, "exploit": 30,
        "liquidation": 26, "exchange": 18, "fed": 20, "tariff": 18,
    }

    def __init__(self) -> None:
        self.collector = RSSCollector(self.FEEDS)

    def collect(self, limit: int = 5) -> list[NewsArticle]:
        selected: list[NewsArticle] = []
        for article in self.collector.collect():
            if article.source not in self.TRUSTED:
                continue
            age = self._age_hours(article)
            if age is None or age > 36:
                continue
            text = f"{article.title} {article.summary}".lower()
            points = sum(weight for term, weight in self.SIGNALS.items() if term in text)
            if points < 18:
                continue
            article.score = min(100, points + (16 if age <= 6 else 8) + 20)
            selected.append(article)
        selected.sort(key=lambda item: (item.score, item.published_at or datetime.min.replace(tzinfo=timezone.utc)), reverse=True)
        portfolio = NewsPortfolioSelector().select(selected, limit=max(limit * 3, limit))
        output: list[NewsArticle] = []
        source_counts: Counter[str] = Counter()
        for article in portfolio:
            source = (article.source or "Unknown").strip().lower()
            if source_counts[source] >= 2:
                continue
            output.append(article)
            source_counts[source] += 1
            if len(output) == limit:
                return output
        # Do not manufacture variety by repeating a single publisher merely
        # to hit the requested count.
        return output[:limit]

    @staticmethod
    def _age_hours(article: NewsArticle) -> float | None:
        if article.published_at is None:
            return None
        published = article.published_at if article.published_at.tzinfo else article.published_at.replace(tzinfo=timezone.utc)
        return max(0, (datetime.now(timezone.utc) - published).total_seconds() / 3600)
