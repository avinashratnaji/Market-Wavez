"""
news/market_impact.py

Calculates the intrinsic market impact of a news article.

This analyzer estimates how strongly a piece of news is
likely to move financial markets irrespective of source
or recency.

Author : Market Sentinel
Version : 1.0.0
"""

from __future__ import annotations

from market_sentinel.news.models import NewsEvent


class MarketImpactAnalyzer:
    """
    Calculates market impact score.

    Returns
    -------
    int
        Score between 0 and 30.
    """

    HIGH_IMPACT = {
        "interest rate": 30,
        "repo": 30,
        "repo rate": 30,
        "fed": 30,
        "fomc": 30,
        "inflation": 28,
        "cpi": 28,
        "gdp": 26,
        "recession": 26,
        "war": 30,
        "sanction": 24,
        "tariff": 22,
        "oil": 22,
        "crude": 22,
        "natural gas": 20,
        "gold": 18,
        "silver": 16,
        "bitcoin": 18,
        "ethereum": 16,
    }

    CORPORATE = {
        "earnings": 22,
        "quarterly results": 22,
        "q1": 18,
        "q2": 18,
        "q3": 18,
        "q4": 18,
        "guidance": 18,
        "acquisition": 20,
        "merger": 20,
        "bankruptcy": 25,
        "ipo": 18,
        "buyback": 16,
        "dividend": 14,
    }

    MEDIUM_IMPACT = {
        "investment": 12,
        "expansion": 10,
        "production": 10,
        "exports": 8,
        "imports": 8,
        "manufacturing": 8,
        "factory": 8,
        "plant": 8,
    }

    LOW_IMPACT = {
        "conference": 2,
        "speech": 2,
        "interview": 2,
        "award": 1,
    }

    def score(self, event: NewsEvent) -> int:
        """
        Calculate market impact score.
        """

        text = (
            f"{event.title} "
            f"{event.summary}"
        ).lower()

        score = 0

        score += self._lookup(text, self.HIGH_IMPACT)
        score += self._lookup(text, self.CORPORATE)
        score += self._lookup(text, self.MEDIUM_IMPACT)
        score += self._lookup(text, self.LOW_IMPACT)

        return min(score, 30)

    @staticmethod
    def _lookup(
        text: str,
        mapping: dict[str, int],
    ) -> int:

        score = 0

        for keyword, value in mapping.items():

            if keyword in text:
                score += value

        return score