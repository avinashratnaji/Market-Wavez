"""
news/relevance_filter.py

Filters and ranks news articles based on
their usefulness for traders and investors.

Author : Market Sentinel
Version : 1.0.0
"""

from __future__ import annotations

from market_sentinel.news.models import NewsEvent


class NewsRelevanceFilter:
    """
    Removes low-value news and ranks useful news.

    This filter is intentionally conservative.
    Routine operational notices are discarded while
    market-moving news is retained.
    """

    # ------------------------------------------------------------------
    # Routine news that should never reach Morning Brief
    # ------------------------------------------------------------------

    BLOCK_KEYWORDS = (
        "treasury bill",
        "t-bill",
        "auction result",
        "auction schedule",
        "cut-off",
        "money market operation",
        "variable rate repo",
        "vrr",
        "laf",
        "liquidity adjustment facility",
        "overnight repo",
        "reverse repo",
        "91-day",
        "182-day",
        "364-day",
    )

    # ------------------------------------------------------------------
    # High quality news sources
    # ------------------------------------------------------------------

    SOURCE_SCORE = {
        "Bloomberg": 100,
        "Financial Times": 98,
        "Yahoo Finance": 96,
        "Moneycontrol": 95,
        "Reuters": 94,
        "Economic Times": 90,
        "CNBC": 88,
        "Business Standard": 85,
        "RBI": 20,
        "SEBI": 20,
    }

    MINIMUM_SCORE = 70

    def process(
        self,
        events: list[NewsEvent],
    ) -> list[NewsEvent]:

        ranked = []

        for event in events:

            if self._should_ignore(event):
                continue

            score = self._score(event)

            if score < self.MINIMUM_SCORE:
                continue

            ranked.append((score, event))

        ranked.sort(
            key=lambda x: x[0],
            reverse=True,
        )

        return [event for _, event in ranked]

    # ------------------------------------------------------------------

    def _should_ignore(
        self,
        event: NewsEvent,
    ) -> bool:

        text = f"{event.title} {event.summary}".lower()

        for keyword in self.BLOCK_KEYWORDS:

            if keyword in text:
                return True

        return False

    # ------------------------------------------------------------------

    def _score(
        self,
        event: NewsEvent,
    ) -> int:

        score = self.SOURCE_SCORE.get(
            event.source,
            50,
        )

        title = event.title.lower()

        # --------------------------------------------------------------
        # High impact keywords
        # --------------------------------------------------------------

        HIGH_IMPACT = (
            "earnings",
            "acquisition",
            "merger",
            "profit",
            "loss",
            "inflation",
            "cpi",
            "gdp",
            "interest rate",
            "repo rate",
            "tariff",
            "war",
            "oil",
            "crude",
            "gold",
            "bitcoin",
            "ethereum",
            "nifty",
            "sensex",
            "bank nifty",
            "fii",
            "dii",
            "fed",
            "rbi",
        )

        for keyword in HIGH_IMPACT:

            if keyword in title:
                score += 8

        return min(score, 100)