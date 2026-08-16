"""
Market Sentinel
Indian Market News Ranker

Production-grade news importance scoring engine.

Purpose
-------
Ranks Indian financial-market news using multiple independent
signals instead of simply adding keyword weights.

The final score is ALWAYS 0-100.

Scoring dimensions
------------------
1. Market impact
2. Event importance
3. Indian-market relevance
4. Corporate significance
5. Earnings significance
6. Macro significance
7. Source credibility
8. Recency
9. Headline signal
10. Noise / educational-content penalty

Design principles
-----------------
- A large number of weak keywords must NOT automatically produce 100.
- High-impact events receive stronger scores.
- Official regulatory sources receive high credibility.
- Major corporate transactions receive high scores.
- Earnings are evaluated according to magnitude/significance.
- Generic "market outlook" articles are useful but cannot dominate.
- Old news naturally decays.
- Personal-finance / educational articles are heavily penalized.
- Final score is deterministic and explainable.

Author  : Market Sentinel
Version : 4.0.0
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Iterable

from market_sentinel.news.models import NewsArticle
from market_sentinel.providers.news.news_intelligence import NewsPortfolioSelector


class NewsRanker:
    """
    Production-grade Indian market news ranking engine.

    Final score:
        0   = irrelevant / very low importance
        25  = low importance
        50  = relevant
        75  = important
        90  = very important
        100 = exceptional market-moving event
    """

    VERSION = "4.0.0"

    # ==========================================================
    # SCORE WEIGHTS
    # ==========================================================

    # Total = 100
    WEIGHTS = {
        "market_impact": 22,
        "event_importance": 20,
        "india_relevance": 14,
        "corporate_significance": 10,
        "earnings_significance": 10,
        "macro_significance": 8,
        "source_quality": 7,
        "recency": 5,
        "headline_signal": 4,
    }

    # ==========================================================
    # EVENT CLASSIFICATION
    # ==========================================================

    # Exceptional events.
    # These are intentionally separated from ordinary keywords.
    EXCEPTIONAL_EVENTS = {
        "emergency rate cut",
        "emergency rate hike",
        "rbi emergency",
        "sovereign downgrade",
        "sovereign upgrade",
        "major regulatory action",
        "ban on",
        "trading ban",
        "fraud",
        "accounting fraud",
        "bank failure",
        "default",
        "insolvency",
        "bankruptcy",
        "major acquisition",
        "mega acquisition",
        "hostile takeover",
        "open offer",
        "major stake sale",
        "promoter exit",
        "promoter resignation",
        "ceo resignation",
        "cfo resignation",
    }

    # ==========================================================
    # HIGH IMPACT EVENTS
    # ==========================================================

    HIGH_IMPACT_EVENTS = {
        "rbi": 90,
        "sebi": 90,
        "repo rate": 95,
        "rate cut": 90,
        "rate hike": 90,
        "monetary policy": 85,

        "block deal": 82,
        "bulk deal": 78,
        "stake sale": 82,
        "stake acquisition": 84,
        "promoter selling": 80,
        "promoter stake": 76,
        "promoter exit": 92,

        "acquisition": 82,
        "merger": 84,
        "demerger": 72,
        "takeover": 88,
        "open offer": 90,

        "buyback": 68,
        "fundraise": 65,
        "funding": 55,

        "major order": 78,
        "large order": 74,
        "order win": 70,
        "major contract": 72,
        "contract win": 68,

        "tariff": 72,
        "trade war": 78,
        "import duty": 70,
        "export duty": 65,

        "regulatory action": 88,
        "regulation": 62,
        "regulatory": 60,

        "government policy": 68,
        "policy change": 70,

        "ipo": 55,
        "listing": 48,
    }

    # ==========================================================
    # MARKET SIGNALS
    # ==========================================================

    MARKET_SIGNALS = {
        "nifty 50": 100,
        "nifty50": 100,
        "nifty": 88,
        "sensex": 88,
        "bank nifty": 88,
        "banknifty": 88,

        "indian stock market": 100,
        "indian markets": 92,
        "indian stocks": 90,
        "indian equities": 90,
        "indian equity": 88,
        "indian market": 85,

        "stock market": 72,
        "share market": 72,
        "equity market": 70,
        "equities": 55,
        "stocks": 45,
        "shares": 40,

        "institutional buying": 78,
        "institutional selling": 78,
        "foreign investors": 75,
        "domestic investors": 68,

        "fii": 78,
        "fpi": 78,
        "dii": 72,

        "market breadth": 72,
        "advance decline": 68,
        "market turnover": 62,
        "trading volume": 60,
        "volume": 40,

        "delivery": 50,
        "market cap": 52,
        "valuation": 48,
    }

    # ==========================================================
    # INDIA RELEVANCE
    # ==========================================================

    INDIA_SIGNALS = {
        "india": 100,
        "indian": 100,

        "nifty": 100,
        "sensex": 100,
        "bank nifty": 100,
        "banknifty": 100,

        "nse": 100,
        "bse": 100,

        "sebi": 100,
        "rbi": 100,

        "indian rupee": 100,
        "rupee": 92,
        "inr": 90,

        "fii": 90,
        "fpi": 90,
        "dii": 88,

        "india gdp": 100,
        "indian economy": 100,

        "mumbai": 70,
        "delhi": 55,
        "bengaluru": 55,
        "bangalore": 55,
    }

    # ==========================================================
    # CORPORATE EVENTS
    # ==========================================================

    CORPORATE_EVENTS = {
        "acquisition": 95,
        "merger": 95,
        "takeover": 100,
        "open offer": 100,
        "demerger": 82,

        "stake sale": 94,
        "stake acquisition": 94,
        "promoter stake": 90,
        "promoter selling": 94,
        "promoter exit": 100,
        "pledge": 80,

        "block deal": 95,
        "bulk deal": 88,

        "major order": 88,
        "large order": 84,
        "order win": 80,
        "contract win": 78,
        "order book": 65,

        "fundraise": 72,
        "funding": 60,

        "buyback": 80,
        "dividend": 60,
        "bonus": 55,
        "stock split": 58,
        "share split": 58,

        "capex": 60,
        "expansion": 52,
        "joint venture": 65,
        "partnership": 45,

        "ceo resignation": 90,
        "cfo resignation": 92,
        "management change": 72,
    }

    # ==========================================================
    # EARNINGS
    # ==========================================================

    EARNINGS_EVENTS = {
        "q1 results": 85,
        "q2 results": 85,
        "q3 results": 85,
        "q4 results": 90,

        "quarterly results": 82,
        "earnings": 70,
        "results": 68,

        "net profit": 65,
        "profit rises": 78,
        "profit jumps": 84,
        "profit surges": 88,

        "profit falls": 82,
        "profit declines": 82,
        "profit drops": 84,

        "net loss": 85,
        "loss widens": 88,
        "loss narrows": 70,

        "revenue rises": 68,
        "revenue jumps": 74,
        "revenue surges": 78,

        "revenue falls": 75,
        "revenue declines": 75,
        "revenue drops": 78,

        "ebitda": 62,
        "margin": 55,
        "guidance": 72,

        "outlook": 48,
        "forecast": 45,
    }

    # ==========================================================
    # MACRO
    # ==========================================================

    MACRO_EVENTS = {
        "repo rate": 100,
        "rate cut": 100,
        "rate hike": 100,
        "interest rate": 90,
        "monetary policy": 98,

        "inflation": 82,
        "cpi": 88,
        "wpi": 82,

        "gdp": 92,
        "economic growth": 82,
        "growth": 52,

        "rupee": 72,
        "indian rupee": 88,
        "inr": 68,

        "crude oil": 78,
        "oil prices": 72,

        "gold prices": 45,

        "bond yield": 70,
        "bond yields": 70,

        "tariff": 84,
        "trade war": 90,
        "import duty": 78,
        "export duty": 72,

        "government policy": 82,
        "fiscal policy": 80,
        "budget": 78,

        "regulation": 72,
        "regulatory": 72,
    }

    # ==========================================================
    # SOURCE QUALITY
    # ==========================================================

    SOURCE_QUALITY = {
        # Official primary sources
        "rbi": 100,
        "reserve bank of india": 100,

        "sebi": 100,
        "securities and exchange board of india": 100,

        "nse": 100,
        "national stock exchange": 100,

        "bse": 100,
        "bombay stock exchange": 100,

        # High-quality financial journalism
        "reuters": 94,
        "business standard": 92,
        "economic times": 90,
        "markets-economic times": 90,
        "moneycontrol": 88,

        "cnbc": 84,
        "financial express": 84,
        "mint": 84,

        "times of india": 76,

        # Aggregators
        "investing.com": 68,
        "yahoo finance": 60,
    }

    DEFAULT_SOURCE_SCORE = 55

    # ==========================================================
    # RECENCY
    # ==========================================================

    RECENCY_SCORE = (
        (1, 100),       # <= 1 hour
        (3, 92),        # <= 3 hours
        (6, 82),        # <= 6 hours
        (12, 68),       # <= 12 hours
        (24, 52),       # <= 24 hours
        (48, 30),       # <= 48 hours
        (72, 15),       # <= 72 hours
    )

    # ==========================================================
    # HEADLINE SIGNALS
    # ==========================================================

    HEADLINE_SIGNALS = {
        "breaks": 100,
        "breaking": 100,
        "exclusive": 92,
        "update": 72,

        "jumps": 82,
        "surges": 88,
        "soars": 88,
        "plunges": 88,
        "falls": 72,
        "drops": 72,

        "invest": 70,
        "invests": 70,
        "investment": 72,

        "acquire": 88,
        "acquires": 88,
        "acquisition": 90,

        "merger": 92,
        "takeover": 96,

        "stake": 82,
        "deal": 68,

        "results": 78,
        "profit": 72,
        "revenue": 62,

        "rbi": 92,
        "sebi": 92,

        "rate cut": 98,
        "rate hike": 98,

        "tariff": 82,
        "trade war": 88,

        "ipo": 62,
    }

    # ==========================================================
    # LOW VALUE / NOISE
    # ==========================================================

    LOW_VALUE_KEYWORDS = {
        "personal finance",
        "savings account",
        "credit card",
        "insurance tips",
        "insurance guide",
        "personal loan",
        "home loan",
        "car loan",
        "retirement planning",
        "financial planning",
        "tax saving tips",
        "how to save",
        "how to invest",
        "mutual fund guide",
        "best savings",
        "best credit card",
        "what is a good",
        "beginner guide",
        "explained",
    }

    # ==========================================================
    # GLOBAL-ONLY NOISE
    # ==========================================================

    GLOBAL_ONLY_KEYWORDS = {
        "nasdaq",
        "dow jones",
        "s&p 500",
        "wall street",
        "japanese stocks",
        "japanese bond",
        "bank of japan",
        "boj",
        "german stocks",
        "european stocks",
        "european market",
        "uk stocks",
        "hong kong stocks",
    }

    # ==========================================================
    # PUBLIC API
    # ==========================================================

    def rank(
        self,
        articles: Iterable[NewsArticle],
        limit: int = 5,
    ) -> list[NewsArticle]:
        """
        Rank articles and return the top N.

        Existing NewsArticle.score is populated with the
        final 0-100 score.
        """

        articles = list(articles)

        if not articles:
            return []

        scored: list[NewsArticle] = []

        for article in articles:
            article.score = self._calculate_score(article)
            scored.append(article)

        # ------------------------------------------------------
        # Sort by:
        #
        # 1. score
        # 2. newest publication time
        # ------------------------------------------------------

        scored.sort(
            key=self._sort_key,
            reverse=True,
        )

        # A daily brief should report distinct events, not ten versions of the
        # same headline.  The selector preserves this ranker's score while
        # clustering duplicate coverage and applying transparent diversity.
        return NewsPortfolioSelector().select(
            scored,
            limit=limit,
        )

    # ==========================================================
    # MAIN SCORING ENGINE
    # ==========================================================

    def _calculate_score(
        self,
        article: NewsArticle,
    ) -> int:
        """
        Calculate final 0-100 score.

        This is a weighted model, NOT a raw keyword sum.
        """

        title = self._normalize(
            article.title
        )

        summary = self._normalize(
            article.summary
        )

        source = self._normalize(
            article.source
        )

        text = f"{title} {summary}"

        # ------------------------------------------------------
        # Detect obvious low-value content.
        # ------------------------------------------------------

        noise_penalty = self._noise_penalty(
            text
        )

        # ------------------------------------------------------
        # Detect global-only articles.
        # ------------------------------------------------------

        global_penalty = self._global_penalty(
            text
        )

        # ------------------------------------------------------
        # Calculate individual dimensions.
        # ------------------------------------------------------

        market_impact = self._market_impact_score(
            text
        )

        event_importance = self._event_importance_score(
            text
        )

        india_relevance = self._india_relevance_score(
            text
        )

        corporate_significance = self._corporate_score(
            text
        )

        earnings_significance = self._earnings_score(
            text
        )

        macro_significance = self._macro_score(
            text
        )

        source_quality = self._source_score(
            source
        )

        recency = self._recency_score(
            article.published_at
        )

        headline_signal = self._headline_score(
            title
        )

        # ------------------------------------------------------
        # Weighted score.
        #
        # Every component is 0-100.
        # WEIGHTS total exactly 100.
        # ------------------------------------------------------

        weighted_score = (
            market_impact
            * self.WEIGHTS["market_impact"]
            / 100
        )

        weighted_score += (
            event_importance
            * self.WEIGHTS["event_importance"]
            / 100
        )

        weighted_score += (
            india_relevance
            * self.WEIGHTS["india_relevance"]
            / 100
        )

        weighted_score += (
            corporate_significance
            * self.WEIGHTS["corporate_significance"]
            / 100
        )

        weighted_score += (
            earnings_significance
            * self.WEIGHTS["earnings_significance"]
            / 100
        )

        weighted_score += (
            macro_significance
            * self.WEIGHTS["macro_significance"]
            / 100
        )

        weighted_score += (
            source_quality
            * self.WEIGHTS["source_quality"]
            / 100
        )

        weighted_score += (
            recency
            * self.WEIGHTS["recency"]
            / 100
        )

        weighted_score += (
            headline_signal
            * self.WEIGHTS["headline_signal"]
            / 100
        )

        # ------------------------------------------------------
        # Penalties.
        # ------------------------------------------------------

        weighted_score -= noise_penalty
        weighted_score -= global_penalty

        # ------------------------------------------------------
        # Special event boost.
        #
        # This is applied AFTER weighted scoring so a genuine
        # market-moving event can reach the 90-100 range.
        # ------------------------------------------------------

        if self._contains_any(
            text,
            self.EXCEPTIONAL_EVENTS,
        ):
            weighted_score += 8

        # ------------------------------------------------------
        # Strong official source + strong event combination.
        #
        # Example:
        # RBI rate decision
        # SEBI major regulation
        # NSE emergency action
        # ------------------------------------------------------

        if (
            source_quality >= 95
            and event_importance >= 80
        ):
            weighted_score += 5

        # ------------------------------------------------------
        # Strong corporate event + Indian company signal.
        # ------------------------------------------------------

        if (
            corporate_significance >= 85
            and india_relevance >= 80
        ):
            weighted_score += 4

        # ------------------------------------------------------
        # Clamp.
        # ------------------------------------------------------

        final_score = round(
            max(
                0,
                min(
                    100,
                    weighted_score,
                ),
            )
        )

        return final_score

    # ==========================================================
    # MARKET IMPACT
    # ==========================================================

    def _market_impact_score(
        self,
        text: str,
    ) -> int:
        """
        Estimate how strongly the article can affect markets.
        """

        matches = self._matched_values(
            text,
            self.MARKET_SIGNALS,
        )

        if not matches:
            return 10

        highest = max(matches)
        count = len(matches)

        # Highest signal is primary.
        score = highest

        # Additional signals improve confidence but with
        # diminishing returns.
        if count >= 2:
            score += 5

        if count >= 4:
            score += 5

        if count >= 7:
            score += 3

        return min(
            100,
            score,
        )

    # ==========================================================
    # EVENT IMPORTANCE
    # ==========================================================

    def _event_importance_score(
        self,
        text: str,
    ) -> int:
        """
        Determine importance of the actual event.
        """

        matches = self._matched_values(
            text,
            self.HIGH_IMPACT_EVENTS,
        )

        if not matches:
            return 15

        highest = max(matches)

        # Multiple strong events indicate a complex event,
        # but should not automatically become 100.
        count = len(matches)

        if count >= 2:
            highest += 4

        if count >= 4:
            highest += 3

        return min(
            100,
            highest,
        )

    # ==========================================================
    # INDIA RELEVANCE
    # ==========================================================

    def _india_relevance_score(
        self,
        text: str,
    ) -> int:
        """
        Determine how directly the article relates to India.
        """

        matches = self._matched_values(
            text,
            self.INDIA_SIGNALS,
        )

        if not matches:
            return 0

        highest = max(matches)

        count = len(matches)

        if count >= 2:
            highest += 3

        if count >= 4:
            highest += 3

        return min(
            100,
            highest,
        )

    # ==========================================================
    # CORPORATE SIGNIFICANCE
    # ==========================================================

    def _corporate_score(
        self,
        text: str,
    ) -> int:
        """Score corporate actions."""

        matches = self._matched_values(
            text,
            self.CORPORATE_EVENTS,
        )

        if not matches:
            return 5

        score = max(matches)

        # Combination such as:
        # BofA + investment + 49.9% stake
        # is stronger than a single generic keyword.
        if len(matches) >= 2:
            score += 5

        if len(matches) >= 4:
            score += 3

        return min(
            100,
            score,
        )

    # ==========================================================
    # EARNINGS
    # ==========================================================

    def _earnings_score(
        self,
        text: str,
    ) -> int:
        """Score earnings-related news."""

        matches = self._matched_values(
            text,
            self.EARNINGS_EVENTS,
        )

        if not matches:
            return 5

        score = max(matches)

        if len(matches) >= 2:
            score += 4

        if len(matches) >= 4:
            score += 3

        # Strong language generally indicates a larger
        # earnings surprise.
        strong_result_terms = (
            "jumps",
            "surges",
            "soars",
            "plunges",
            "falls",
            "drops",
            "widens",
            "narrows",
        )

        if any(
            term in text
            for term in strong_result_terms
        ):
            score += 5

        return min(
            100,
            score,
        )

    # ==========================================================
    # MACRO
    # ==========================================================

    def _macro_score(
        self,
        text: str,
    ) -> int:
        """Score macroeconomic significance."""

        matches = self._matched_values(
            text,
            self.MACRO_EVENTS,
        )

        if not matches:
            return 5

        score = max(matches)

        if len(matches) >= 2:
            score += 4

        if len(matches) >= 4:
            score += 3

        return min(
            100,
            score,
        )

    # ==========================================================
    # SOURCE
    # ==========================================================

    def _source_score(
        self,
        source: str,
    ) -> int:
        """
        Score source credibility.

        Official sources receive the highest score.
        """

        if not source:
            return self.DEFAULT_SOURCE_SCORE

        for name, score in sorted(
            self.SOURCE_QUALITY.items(),
            key=lambda item: len(item[0]),
            reverse=True,
        ):
            if name in source:
                return score

        return self.DEFAULT_SOURCE_SCORE

    # ==========================================================
    # RECENCY
    # ==========================================================

    @classmethod
    def _recency_score(
        cls,
        published_at: datetime | None,
    ) -> int:
        """
        Score freshness.

        <= 1 hour     : 100
        <= 3 hours    : 92
        <= 6 hours    : 82
        <= 12 hours   : 68
        <= 24 hours   : 52
        <= 48 hours   : 30
        <= 72 hours   : 15
        > 72 hours    : 0
        """

        if published_at is None:
            return 15

        now = datetime.now(timezone.utc)

        if published_at.tzinfo is None:
            published_at = published_at.replace(
                tzinfo=timezone.utc
            )
        else:
            published_at = published_at.astimezone(
                timezone.utc
            )

        age_hours = (
            now - published_at
        ).total_seconds() / 3600

        # Future timestamps.
        if age_hours < 0:
            age_hours = 0

        for hours, score in cls.RECENCY_SCORE:
            if age_hours <= hours:
                return score

        return 0

    # ==========================================================
    # HEADLINE SCORE
    # ==========================================================

    def _headline_score(
        self,
        title: str,
    ) -> int:
        """
        Score how strongly the headline itself signals an
        important event.
        """

        matches = self._matched_values(
            title,
            self.HEADLINE_SIGNALS,
        )

        if not matches:
            return 20

        score = max(matches)

        # Multiple strong headline signals increase confidence.
        if len(matches) >= 2:
            score += 5

        if len(matches) >= 3:
            score += 3

        return min(
            100,
            score,
        )

    # ==========================================================
    # NOISE PENALTY
    # ==========================================================

    @staticmethod
    def _noise_penalty(
        text: str,
    ) -> int:
        """
        Penalize content that is not useful for a market brief.
        """

        penalty = 0

        for keyword in NewsRanker.LOW_VALUE_KEYWORDS:

            if keyword in text:

                if keyword in {
                    "personal finance",
                    "savings account",
                    "credit card",
                    "personal loan",
                    "home loan",
                    "car loan",
                }:
                    penalty += 25

                elif keyword in {
                    "how to save",
                    "how to invest",
                    "mutual fund guide",
                    "tax saving tips",
                }:
                    penalty += 20

                else:
                    penalty += 10

        return min(
            40,
            penalty,
        )

    # ==========================================================
    # GLOBAL PENALTY
    # ==========================================================

    def _global_penalty(
        self,
        text: str,
    ) -> int:
        """
        Penalize stories that are clearly global-only.

        Indian relevance cancels this penalty.
        """

        has_global = self._contains_any(
            text,
            self.GLOBAL_ONLY_KEYWORDS,
        )

        if not has_global:
            return 0

        has_india = self._contains_any(
            text,
            self.INDIA_SIGNALS,
        )

        if has_india:
            return 0

        return 18

    # ==========================================================
    # HELPERS
    # ==========================================================

    @staticmethod
    def _normalize(
        text: str | None,
    ) -> str:
        """Normalize text for reliable matching."""

        if not text:
            return ""

        text = text.lower()

        # Normalize HTML-ish whitespace.
        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text.strip()

    @staticmethod
    def _contains_any(
        text: str,
        keywords: set[str],
    ) -> bool:
        """Return True when at least one keyword exists."""

        return any(
            keyword in text
            for keyword in keywords
        )

    @staticmethod
    def _matched_values(
        text: str,
        mapping: dict[str, int],
    ) -> list[int]:
        """
        Return scores for matched keywords.

        Each keyword is counted only once.
        """

        matches: list[int] = []

        for keyword, value in mapping.items():

            if keyword in text:
                matches.append(value)

        return matches

    @staticmethod
    def _sort_key(
        article: NewsArticle,
    ) -> tuple[int, datetime]:
        """
        Stable ranking key.

        Primary:
            score

        Secondary:
            publication time
        """

        published_at = article.published_at

        if published_at is None:
            published_at = datetime.min.replace(
                tzinfo=timezone.utc
            )

        elif published_at.tzinfo is None:
            published_at = published_at.replace(
                tzinfo=timezone.utc
            )

        else:
            published_at = published_at.astimezone(
                timezone.utc
            )

        return (
            article.score,
            published_at,
        )

    # ==========================================================
    # DEBUG / EXPLANATION API
    # ==========================================================

    def explain(
        self,
        article: NewsArticle,
    ) -> dict[str, int]:
        """
        Return score components for debugging.

        This does NOT modify article.score.

        Useful for understanding why an article ranked
        higher or lower.
        """

        title = self._normalize(
            article.title
        )

        summary = self._normalize(
            article.summary
        )

        source = self._normalize(
            article.source
        )

        text = f"{title} {summary}"

        components = {
            "market_impact": self._market_impact_score(
                text
            ),
            "event_importance": self._event_importance_score(
                text
            ),
            "india_relevance": self._india_relevance_score(
                text
            ),
            "corporate_significance": self._corporate_score(
                text
            ),
            "earnings_significance": self._earnings_score(
                text
            ),
            "macro_significance": self._macro_score(
                text
            ),
            "source_quality": self._source_score(
                source
            ),
            "recency": self._recency_score(
                article.published_at
            ),
            "headline_signal": self._headline_score(
                title
            ),
            "noise_penalty": self._noise_penalty(
                text
            ),
            "global_penalty": self._global_penalty(
                text
            ),
        }

        return components
