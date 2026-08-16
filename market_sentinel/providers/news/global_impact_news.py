"""High-conviction global market news, ranked for traders."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Iterable

from market_sentinel.news.models import NewsArticle
from market_sentinel.providers.news.news_intelligence import NewsPortfolioSelector
from market_sentinel.providers.rss_collector import RSSCollector


class GlobalImpactNews:
    """Select the most market-relevant global stories, regardless of region."""

    TRUSTED_SOURCES = frozenset({
        "Reuters", "BBC News", "BBC", "Financial Times", "Bloomberg",
        "The Wall Street Journal", "Wall Street Journal", "Associated Press",
        "Yahoo Finance", "MarketWatch", "CNBC", "The Economist",
        "Barron's", "The Guardian", "CNN", "CNN Business", "Fortune",
    })
    # Reuters' legacy RSS host is unreliable. BBC Business is a stable primary
    # newsroom feed; the transmission filter below remains the gatekeeper.
    DEFAULT_FEEDS = (
        "https://feeds.bbci.co.uk/news/business/rss.xml",
        "https://finance.yahoo.com/news/rssindex",
        "https://news.google.com/rss/search?q=(stocks+OR+Federal+Reserve+OR+earnings+OR+crude+oil+OR+tariffs+OR+China+economy)+when:2d&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=(global+markets+OR+Wall+Street+OR+Nasdaq+OR+S%26P+500+OR+bond+yields)+when:2d&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=(oil+OR+OPEC+OR+inflation+OR+Federal+Reserve+OR+Treasury+yields)+when:2d&hl=en-US&gl=US&ceid=US:en",
    )
    MAX_AGE_HOURS = 36
    MINIMUM_SCORE = 38
    _TOKEN_RE = re.compile(r"\b[a-z0-9]+\b")

    MARKET_RULES: tuple[tuple[str, tuple[str, ...], int], ...] = (
        ("US monetary policy", ("federal reserve", "fed", "treasury yield", "us inflation", "us cpi"), 42),
        ("energy shock", ("brent crude", "crude oil", "opec", "oil supply", "oil prices"), 44),
        ("trade disruption", ("tariff", "trade war", "export controls", "sanctions"), 42),
        ("risk event", ("middle east", "iran", "red sea", "taiwan", "russia"), 28),
        ("equity-market move", ("s&p 500", "nasdaq", "dow jones", "wall street", "stocks", "equities"), 36),
        ("rates and currencies", ("dollar index", "bond yields", "treasury yields", "currency", "yen", "yuan"), 34),
        ("China growth", ("china economy", "chinese economy", "china growth", "pbo c"), 34),
        ("major corporate event", ("earnings", "guidance", "chip", "semiconductor", "nvidia", "apple", "tesla"), 26),
    )

    def __init__(self, feeds: Iterable[str] | None = None) -> None:
        self.collector = RSSCollector(feeds if feeds is not None else self.DEFAULT_FEEDS)

    def collect(self, limit: int = 3) -> list[NewsArticle]:
        candidates: list[NewsArticle] = []
        for article in self.collector.collect():
            score = self._score(article)
            if score >= self.MINIMUM_SCORE:
                article.score = score
                candidates.append(article)
        candidates.sort(key=self._sort_key, reverse=True)
        return NewsPortfolioSelector().select(candidates, limit=limit)

    def _score(self, article: NewsArticle) -> int:
        if article.source.strip() not in self.TRUSTED_SOURCES:
            return 0
        age = self._age_hours(article.published_at)
        if age is None or age > self.MAX_AGE_HOURS:
            return 0

        text = f"{article.title or ''} {article.summary or ''}".lower()
        matched = [
            (label, score)
            for label, triggers, score in self.MARKET_RULES
            if any(trigger in text for trigger in triggers)
        ]
        if not matched:
            return 0

        labels = {label for label, _ in matched}
        # A generic geopolitical headline needs a second market route.
        if labels == {"risk event"}:
            return 0
        base = max(score for _, score in matched)
        corroborating_route_bonus = min(12, (len(labels) - 1) * 6)
        freshness = 12 if age <= 6 else 7 if age <= 18 else 3
        return min(100, base + corroborating_route_bonus + freshness + 12)

    @staticmethod
    def _age_hours(published_at: datetime | None) -> float | None:
        if published_at is None:
            return None
        if published_at.tzinfo is None:
            published_at = published_at.replace(tzinfo=timezone.utc)
        return max(0, (datetime.now(timezone.utc) - published_at).total_seconds() / 3600)

    @staticmethod
    def _sort_key(article: NewsArticle) -> tuple[int, float]:
        timestamp = article.published_at.timestamp() if article.published_at else 0.0
        return article.score, timestamp
