"""
market_sentinel/providers/news/indian_market_news.py

Production-grade Indian Market News Intelligence Collector.

Responsibilities
----------------
1. Collect RSS articles from configured Indian feeds.
2. Normalize article text.
3. Detect Indian-market relevance.
4. Detect market, corporate and macro signals.
5. Reject obvious non-market / personal-finance noise.
6. Reject global-only stories without Indian relevance.
7. Give title signals higher importance than summary signals.
8. Detect India-specific financial terminology.
9. Detect corporate-event terminology.
10. Detect regulatory / policy events.
11. Preserve source and article metadata.
12. Provide diagnostics for downstream ranking engines.

Important
---------
This module DOES NOT perform final market-news ranking.

Final ranking belongs to:
    market_sentinel.providers.news.news_ranker

The collector answers:

    "Is this article relevant to the Indian market?"

The ranker answers:

    "How important is this article?"

Author  : Market Sentinel
Version : 3.0.0
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable
from urllib.parse import quote_plus

from market_sentinel.news.models import NewsArticle
from market_sentinel.providers.rss_collector import RSSCollector
from market_sentinel.providers.rss_feeds import indian_feeds


class IndianMarketNews:
    """
    Production-grade Indian market news collector.

    The collector performs high-quality relevance filtering before
    articles reach the ranking engine.

    Pipeline:

        RSS
          ↓
        normalization
          ↓
        exclusion filter
          ↓
        Indian signal detection
          ↓
        market signal detection
          ↓
        corporate signal detection
          ↓
        macro signal detection
          ↓
        global-only rejection
          ↓
        source validation
          ↓
        relevance decision
          ↓
        NewsRanker
    """

    VERSION = "3.0.0"

    # ==========================================================
    # CONFIGURATION
    # ==========================================================

    MAX_TEXT_LENGTH = 25_000

    # ==========================================================
    # STRONG INDIAN MARKET SIGNALS
    #
    # These are strong enough that an article normally qualifies
    # immediately as Indian-market related.
    # ==========================================================

    STRONG_MARKET_KEYWORDS = {
        "nifty",
        "nifty 50",
        "nifty50",
        "sensex",
        "bank nifty",
        "banknifty",
        "nifty bank",
        "nifty midcap",
        "nifty smallcap",
        "indian stock market",
        "indian share market",
        "indian stocks",
        "indian equities",
        "indian equity market",
        "indian markets",
        "indian market",
        "india stocks",
        "india stock market",
        "india equities",
        "nse",
        "bse",
        "sebi",
        "rbi",
        "fii",
        "fpi",
        "dii",
    }

    # ==========================================================
    # INDIA PRIORITY SIGNALS
    # ==========================================================

    INDIA_PRIORITY_KEYWORDS = {
        # Indices
        "nifty",
        "nifty 50",
        "nifty50",
        "sensex",
        "bank nifty",
        "banknifty",
        "nifty bank",
        "nifty midcap",
        "nifty smallcap",

        # Indian market
        "indian stocks",
        "indian stock",
        "indian market",
        "indian markets",
        "indian equities",
        "indian equity",
        "india stocks",
        "india stock",
        "india equities",
        "india shares",

        # Exchanges / regulators
        "nse",
        "bse",
        "sebi",
        "rbi",

        # Institutional flows
        "fii",
        "fpi",
        "dii",
        "foreign institutional",
        "foreign portfolio investor",
        "domestic institutional",

        # Currency
        "indian rupee",
        "rupee",
        "inr",
        "rs.",
        "rs ",
        "₹",

        # Indian financial terminology
        "crore",
        "crores",
        "lakh crore",
        "lakh crores",
        "million crore",

        # Indian earnings terminology
        "q1 results",
        "q2 results",
        "q3 results",
        "q4 results",
        "q1 earnings",
        "q2 earnings",
        "q3 earnings",
        "q4 earnings",
        "quarterly results",
    }

    # ==========================================================
    # INDIAN MACRO SIGNALS
    # ==========================================================

    INDIA_MACRO_KEYWORDS = {
        "rbi",
        "reserve bank of india",
        "monetary policy",
        "repo rate",
        "reverse repo",
        "cash reserve ratio",
        "crr",
        "statutory liquidity ratio",
        "slr",
        "inflation",
        "cpi",
        "consumer price index",
        "wpi",
        "wholesale price index",
        "gdp",
        "gross domestic product",
        "india gdp",
        "indian inflation",
        "fiscal deficit",
        "current account deficit",
        "trade deficit",
        "government borrowing",
        "bond yield",
        "10-year bond",
        "government securities",
        "rupee",
        "inr",
        "crude oil",
        "oil prices",
        "import duty",
        "export duty",
        "tariff",
        "trade policy",
        "union budget",
        "budget",
        "economic survey",
    }

    # ==========================================================
    # CORPORATE EVENT SIGNALS
    # ==========================================================

    CORPORATE_KEYWORDS = {
        # Results
        "q1 results",
        "q2 results",
        "q3 results",
        "q4 results",
        "q1 earnings",
        "q2 earnings",
        "q3 earnings",
        "q4 earnings",
        "quarterly results",
        "quarterly earnings",
        "earnings",
        "results",

        # Financial performance
        "profit",
        "loss",
        "net profit",
        "net loss",
        "revenue",
        "sales",
        "ebitda",
        "ebit",
        "margin",
        "operating margin",
        "profit margin",
        "guidance",
        "outlook",

        # M&A
        "acquisition",
        "acquires",
        "acquired",
        "merger",
        "merges",
        "takeover",
        "buyout",

        # Ownership / capital
        "stake",
        "stake sale",
        "stake purchase",
        "fundraise",
        "fundraising",
        "funding",
        "capital raise",
        "rights issue",
        "preferential issue",
        "qip",
        "qualified institutional placement",

        # Shareholder actions
        "buyback",
        "share buyback",
        "dividend",
        "interim dividend",
        "final dividend",
        "bonus",
        "bonus issue",
        "stock split",
        "share split",

        # Promoter / institutional activity
        "promoter",
        "promoter selling",
        "promoter buying",
        "promoter stake",
        "pledge",
        "promoter pledge",
        "block deal",
        "bulk deal",
        "institutional buying",
        "institutional selling",

        # Business activity
        "order win",
        "order book",
        "major order",
        "large order",
        "contract",
        "contract win",
        "new contract",
        "capex",
        "capital expenditure",
        "expansion",
        "capacity expansion",
        "plant expansion",
        "new facility",
        "joint venture",
        "partnership",
    }

    # ==========================================================
    # GENERAL MARKET SIGNALS
    # ==========================================================

    MARKET_KEYWORDS = {
        "stock market",
        "share market",
        "equity market",
        "equity markets",
        "equities",
        "stocks",
        "shares",
        "indices",
        "index",
        "ipo",
        "listing",
        "listed company",
        "market cap",
        "market capitalisation",
        "valuation",
        "trading",
        "investors",
        "investment",
        "institutional buying",
        "institutional selling",
        "foreign investors",
        "domestic investors",
        "delivery",
        "volume",
        "turnover",
        "market breadth",
        "advance decline",
        "gainers",
        "losers",
        "bullish",
        "bearish",
        "rally",
        "selloff",
        "sell-off",
        "correction",
        "volatility",
    }

    # ==========================================================
    # REGULATORY / POLICY SIGNALS
    # ==========================================================

    REGULATORY_KEYWORDS = {
        "sebi",
        "rbi",
        "nse",
        "bse",
        "regulation",
        "regulatory",
        "regulator",
        "regulatory framework",
        "new norms",
        "new rules",
        "rules",
        "circular",
        "circulars",
        "notification",
        "guidelines",
        "compliance",
        "position limits",
        "margin norms",
        "margin requirement",
        "disclosure norms",
        "disclosure requirements",
        "insider trading",
        "listing regulations",
        "market surveillance",
        "investor protection",
    }

    # ==========================================================
    # GLOBAL SIGNALS
    #
    # These do NOT automatically make an article irrelevant.
    # They become a problem only when there is no Indian signal.
    # ==========================================================

    GLOBAL_ONLY_KEYWORDS = {
        "japanese bond",
        "japanese bonds",
        "boj",
        "bank of japan",
        "wall street",
        "nasdaq",
        "dow jones",
        "s&p 500",
        "sp 500",
        "us stocks",
        "us stock market",
        "american stocks",
        "american stock market",
        "european stocks",
        "european market",
        "euro zone",
        "eurozone",
        "german stocks",
        "german market",
        "uk stocks",
        "uk market",
        "china stocks",
        "china stock market",
        "hong kong stocks",
        "hong kong market",
        "nikkei",
        "hang seng",
        "ftse",
        "dax",
    }

    # ==========================================================
    # EXCLUSION / NOISE
    # ==========================================================

    EXCLUDE_KEYWORDS = {
        "personal finance",
        "personal-finance",
        "savings account",
        "savings accounts",
        "credit card",
        "credit cards",
        "credit card tips",
        "insurance tips",
        "insurance guide",
        "insurance plans",
        "how to save",
        "how to invest",
        "mutual fund guide",
        "mutual fund guides",
        "tax saving tips",
        "tax-saving tips",
        "personal loan",
        "personal loans",
        "home loan",
        "home loans",
        "car loan",
        "car loans",
        "retirement planning",
        "financial planning",
        "best savings",
        "best savings account",
        "best credit card",
        "best credit cards",
        "loan calculator",
        "emi calculator",
        "investment calculator",
        "budgeting tips",
        "money saving tips",
        "wealth management tips",
        "how to build wealth",
    }

    # ==========================================================
    # LOW-VALUE MARKET CONTENT
    #
    # These are not necessarily rejected, but require stronger
    # Indian signals to qualify.
    # ==========================================================

    LOW_VALUE_KEYWORDS = {
        "what is",
        "how to",
        "explained",
        "guide",
        "beginner",
        "beginners",
        "meaning",
        "definition",
        "should you buy",
        "should you sell",
        "best stocks to buy",
        "stocks to watch",
        "stocks for tomorrow",
        "stocks for today",
        "multibagger",
        "wealth creation",
    }

    # ==========================================================
    # SOURCE CLASSIFICATION
    # ==========================================================

    INDIA_FOCUSED_SOURCES = {
        "economic times",
        "markets-economic times",
        "moneycontrol",
        "business standard",
        "times of india",
        "rbi",
        "reserve bank of india",
        "sebi",
        "nse",
        "bse",
    }

    REGULATORY_SOURCES = {
        "rbi",
        "reserve bank of india",
        "sebi",
        "nse",
        "bse",
    }

    # ==========================================================
    # SOURCE ALIASES
    # ==========================================================

    SOURCE_ALIASES = {
        "markets-economic times": "economic times",
        "business news today: stock markets, financial news, india business & world business news":
            "times of india",
    }

    # ==========================================================
    # INIT
    # ==========================================================

    def __init__(
        self,
        feeds: Iterable[str] | None = None,
    ) -> None:
        """
        Initialize the Indian market news collector.

        Parameters
        ----------
        feeds:
            Optional custom RSS feed list.

        If omitted, the configured Indian RSS feeds are used.
        """

        self.feeds = list(
            feeds
            if feeds is not None
            else indian_feeds()
        )

        self.collector = RSSCollector(self.feeds)

    # ==========================================================
    # PUBLIC API
    # ==========================================================

    def collect(self, extra_symbols: Iterable[str] = ()) -> list[NewsArticle]:
        """
        Collect and filter Indian-market relevant articles.

        Returns
        -------
        list[NewsArticle]
            Articles that passed the relevance filter.
        """

        raw_articles = self.collector.collect()

        # The fixed finance feeds can miss a fast-moving mid-cap catalyst.
        # Add one bounded Google News query for the actual live NSE movers so
        # names such as Ather are discoverable without maintaining a static
        # hand-written watchlist.
        symbols = [str(symbol).replace("-EQ", "").strip() for symbol in extra_symbols if symbol]
        symbols = list(dict.fromkeys(symbols))[:20]
        if symbols:
            query = "(" + " OR ".join(symbols) + ") (shares OR stock OR results OR order OR acquisition OR volume OR rally) when:2d"
            url = (
                "https://news.google.com/rss/search?q=" + quote_plus(query)
                + "&hl=en-IN&gl=IN&ceid=IN:en"
            )
            raw_articles.extend(RSSCollector((url,)).collect())
            raw_articles = RSSCollector._deduplicate(raw_articles)

        relevant_articles: list[NewsArticle] = []

        for article in raw_articles:

            if self._is_relevant(article):
                relevant_articles.append(article)

        return relevant_articles

    # ==========================================================
    # DIAGNOSTIC API
    # ==========================================================

    def analyze(
        self,
        article: NewsArticle,
    ) -> dict[str, object]:
        """
        Analyze an article without modifying it.

        This is intended for:

        - debugging
        - ranking calibration
        - unit tests
        - logging
        - future AI pipeline
        """

        text = self._article_text(article)

        title = self._normalize_text(
            getattr(article, "title", "")
        )

        summary = self._normalize_text(
            getattr(article, "summary", "")
        )

        source = self._normalize_text(
            getattr(article, "source", "")
        )

        signals = {
            "strong_indian": self._contains_any(
                text,
                self.STRONG_MARKET_KEYWORDS,
            ),
            "india_priority": self._contains_any(
                text,
                self.INDIA_PRIORITY_KEYWORDS,
            ),
            "market": self._contains_any(
                text,
                self.MARKET_KEYWORDS,
            ),
            "corporate": self._contains_any(
                text,
                self.CORPORATE_KEYWORDS,
            ),
            "macro": self._contains_any(
                text,
                self.INDIA_MACRO_KEYWORDS,
            ),
            "regulatory": self._contains_any(
                text,
                self.REGULATORY_KEYWORDS,
            ),
            "global": self._contains_any(
                text,
                self.GLOBAL_ONLY_KEYWORDS,
            ),
            "excluded": self._contains_any(
                text,
                self.EXCLUDE_KEYWORDS,
            ),
            "low_value": self._contains_any(
                title,
                self.LOW_VALUE_KEYWORDS,
            ),
        }

        title_signals = {
            "strong_indian": self._contains_any(
                title,
                self.STRONG_MARKET_KEYWORDS,
            ),
            "india_priority": self._contains_any(
                title,
                self.INDIA_PRIORITY_KEYWORDS,
            ),
            "market": self._contains_any(
                title,
                self.MARKET_KEYWORDS,
            ),
            "corporate": self._contains_any(
                title,
                self.CORPORATE_KEYWORDS,
            ),
            "macro": self._contains_any(
                title,
                self.INDIA_MACRO_KEYWORDS,
            ),
            "regulatory": self._contains_any(
                title,
                self.REGULATORY_KEYWORDS,
            ),
        }

        return {
            "source": source,
            "title": title,
            "signals": signals,
            "title_signals": title_signals,
            "source_india_focused":
                self._is_india_related_source(source),
            "source_regulatory":
                self._is_regulatory_source(source),
            "is_relevant":
                self._is_relevant(article),
            "relevance_profile":
                self._relevance_profile(article),
        }

    # ==========================================================
    # RELEVANCE ENGINE
    # ==========================================================

    def _is_relevant(
        self,
        article: NewsArticle,
    ) -> bool:
        """
        Determine whether an article is relevant to Indian markets.

        Logic is intentionally conservative.

        We prefer:

            high-quality Indian market news

        over:

            generic global finance content.
        """

        text = self._article_text(article)

        if not text:
            return False

        title = self._normalize_text(
            getattr(article, "title", "")
        )

        source = self._normalize_text(
            getattr(article, "source", "")
        )

        # ------------------------------------------------------
        # HARD EXCLUSION
        # ------------------------------------------------------

        if self._contains_any(
            text,
            self.EXCLUDE_KEYWORDS,
        ):
            return False

        # ------------------------------------------------------
        # SIGNAL DETECTION
        # ------------------------------------------------------

        has_strong_indian = self._contains_any(
            text,
            self.STRONG_MARKET_KEYWORDS,
        )

        has_indian_signal = self._contains_any(
            text,
            self.INDIA_PRIORITY_KEYWORDS,
        )

        has_market_signal = self._contains_any(
            text,
            self.MARKET_KEYWORDS,
        )

        has_corporate_signal = self._contains_any(
            text,
            self.CORPORATE_KEYWORDS,
        )

        has_macro_signal = self._contains_any(
            text,
            self.INDIA_MACRO_KEYWORDS,
        )

        has_regulatory_signal = self._contains_any(
            text,
            self.REGULATORY_KEYWORDS,
        )

        has_global_signal = self._contains_any(
            text,
            self.GLOBAL_ONLY_KEYWORDS,
        )

        has_low_value_signal = self._contains_any(
            title,
            self.LOW_VALUE_KEYWORDS,
        )

        source_is_india = self._is_india_related_source(
            source
        )

        source_is_regulatory = self._is_regulatory_source(
            source
        )

        # ------------------------------------------------------
        # HARD GLOBAL REJECTION
        # ------------------------------------------------------
        #
        # Example:
        #
        # "Nasdaq rises as US inflation falls"
        #
        # If there is no India connection, reject it.
        # ------------------------------------------------------

        if (
            has_global_signal
            and not has_indian_signal
            and not has_strong_indian
        ):
            return False

        # ------------------------------------------------------
        # REGULATORY NEWS
        # ------------------------------------------------------
        #
        # RBI / SEBI / NSE / BSE material is inherently relevant.
        # ------------------------------------------------------

        if source_is_regulatory:
            return True

        if (
            has_regulatory_signal
            and has_indian_signal
        ):
            return True

        # ------------------------------------------------------
        # STRONG INDIAN MARKET SIGNAL
        # ------------------------------------------------------

        if has_strong_indian:
            return True

        # ------------------------------------------------------
        # INDIAN MACRO NEWS
        # ------------------------------------------------------

        if (
            has_indian_signal
            and has_macro_signal
        ):
            return True

        # ------------------------------------------------------
        # INDIAN CORPORATE NEWS
        # ------------------------------------------------------

        if (
            has_indian_signal
            and has_corporate_signal
        ):
            return True

        # ------------------------------------------------------
        # INDIA + MARKET
        # ------------------------------------------------------

        if (
            has_indian_signal
            and has_market_signal
        ):
            return True

        # ------------------------------------------------------
        # INDIA-FOCUSED SOURCE + MARKET NEWS
        # ------------------------------------------------------

        if (
            source_is_india
            and has_market_signal
        ):
            return True

        # ------------------------------------------------------
        # LOW-VALUE GENERIC ARTICLES
        # ------------------------------------------------------
        #
        # Example:
        #
        # "What is a good stock to buy?"
        #
        # Do not allow these unless they contain a strong
        # Indian-market signal.
        # ------------------------------------------------------

        if has_low_value_signal:
            return False

        # ------------------------------------------------------
        # DEFAULT REJECTION
        # ------------------------------------------------------

        return False

    # ==========================================================
    # RELEVANCE PROFILE
    # ==========================================================

    def _relevance_profile(
        self,
        article: NewsArticle,
    ) -> str:
        """
        Return a human-readable classification.

        Used by diagnostics and future ranking systems.
        """

        text = self._article_text(article)

        if self._contains_any(
            text,
            self.REGULATORY_KEYWORDS,
        ):
            return "REGULATORY"

        if self._contains_any(
            text,
            self.INDIA_MACRO_KEYWORDS,
        ):
            return "INDIAN_MACRO"

        if self._contains_any(
            text,
            self.CORPORATE_KEYWORDS,
        ):
            return "CORPORATE"

        if self._contains_any(
            text,
            self.MARKET_KEYWORDS,
        ):
            return "MARKET"

        return "GENERAL"

    # ==========================================================
    # SOURCE FILTER
    # ==========================================================

    @classmethod
    def _is_india_related_source(
        cls,
        source: str,
    ) -> bool:
        """
        Check whether the source is primarily India-focused.
        """

        normalized = cls._normalize_text(source)

        if not normalized:
            return False

        canonical = cls.SOURCE_ALIASES.get(
            normalized,
            normalized,
        )

        return any(
            name in canonical
            for name in cls.INDIA_FOCUSED_SOURCES
        )

    @classmethod
    def _is_regulatory_source(
        cls,
        source: str,
    ) -> bool:
        """
        Determine whether an article comes from a regulatory
        / exchange source.
        """

        normalized = cls._normalize_text(source)

        if not normalized:
            return False

        canonical = cls.SOURCE_ALIASES.get(
            normalized,
            normalized,
        )

        return any(
            name in canonical
            for name in cls.REGULATORY_SOURCES
        )

    # ==========================================================
    # TEXT NORMALIZATION
    # ==========================================================

    @staticmethod
    def _normalize_text(
        value: object,
    ) -> str:
        """
        Normalize arbitrary text into a predictable searchable form.

        Handles:

        - None
        - HTML fragments
        - excessive whitespace
        - Unicode currency symbols
        - case normalization
        """

        if value is None:
            return ""

        text = str(value)

        # Remove HTML tags.
        text = re.sub(
            r"<[^>]+>",
            " ",
            text,
        )

        # Normalize common HTML entities.
        text = (
            text.replace("&nbsp;", " ")
            .replace("&amp;", "&")
            .replace("&quot;", '"')
            .replace("&#39;", "'")
        )

        # Normalize whitespace.
        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text.strip().lower()

    @classmethod
    def _article_text(
        cls,
        article: NewsArticle,
    ) -> str:
        """
        Build normalized searchable article text.

        Title is deliberately placed twice.

        This makes title-driven detection stronger while preserving
        compatibility with the existing relevance engine.
        """

        title = cls._normalize_text(
            getattr(article, "title", "")
        )

        summary = cls._normalize_text(
            getattr(article, "summary", "")
        )

        # Limit input size so pathological RSS descriptions
        # cannot produce excessive processing.
        summary = summary[: cls.MAX_TEXT_LENGTH]

        return f"{title} {title} {summary}".strip()

    # ==========================================================
    # KEYWORD MATCHING
    # ==========================================================

    @staticmethod
    def _contains_any(
        text: str,
        keywords: set[str],
    ) -> bool:
        """
        Return True when at least one keyword is present.

        Uses normalized substring matching because many financial
        terms naturally occur as phrases.
        """

        if not text:
            return False

        return any(
            keyword in text
            for keyword in keywords
        )

    @staticmethod
    def _matching_keywords(
        text: str,
        keywords: set[str],
    ) -> list[str]:
        """
        Return all matching keywords.

        Useful for diagnostics and future explainable ranking.
        """

        if not text:
            return []

        return sorted(
            keyword
            for keyword in keywords
            if keyword in text
        )

    # ==========================================================
    # PUBLIC DIAGNOSTIC HELPERS
    # ==========================================================

    def matching_signals(
        self,
        article: NewsArticle,
    ) -> dict[str, list[str]]:
        """
        Return all detected signal keywords.

        Example output:

        {
            "indian": ["nifty", "sebi"],
            "market": ["stocks"],
            "corporate": ["profit"],
            "macro": ["inflation"],
            "regulatory": ["sebi"]
        }

        This is extremely useful when calibrating the ranker.
        """

        text = self._article_text(article)

        return {
            "indian": self._matching_keywords(
                text,
                self.INDIA_PRIORITY_KEYWORDS,
            ),
            "strong_indian": self._matching_keywords(
                text,
                self.STRONG_MARKET_KEYWORDS,
            ),
            "market": self._matching_keywords(
                text,
                self.MARKET_KEYWORDS,
            ),
            "corporate": self._matching_keywords(
                text,
                self.CORPORATE_KEYWORDS,
            ),
            "macro": self._matching_keywords(
                text,
                self.INDIA_MACRO_KEYWORDS,
            ),
            "regulatory": self._matching_keywords(
                text,
                self.REGULATORY_KEYWORDS,
            ),
            "global": self._matching_keywords(
                text,
                self.GLOBAL_ONLY_KEYWORDS,
            ),
            "excluded": self._matching_keywords(
                text,
                self.EXCLUDE_KEYWORDS,
            ),
        }

    # ==========================================================
    # CONVERSION
    # ==========================================================

    @staticmethod
    def convert(
        article: NewsArticle,
    ) -> NewsArticle:
        """
        Normalize an article into the project's NewsArticle model.

        Scoring is intentionally NOT performed here.

        NewsRanker remains responsible for:

            - market impact
            - importance
            - source quality
            - recency
            - final score
            - Top 5 selection
        """

        return NewsArticle(
            title=article.title,
            summary=article.summary,
            source=article.source,
            url=article.url,
            published_at=article.published_at,
            impact=getattr(article, "impact", 0),
            sentiment=getattr(
                article,
                "sentiment",
                "Neutral",
            ),
            sectors=getattr(
                article,
                "sectors",
                None,
            ),
            symbols=getattr(
                article,
                "symbols",
                None,
            ),
            duplicate=getattr(
                article,
                "duplicate",
                False,
            ),
            category=getattr(
                article,
                "category",
                None,
            ),
            importance=getattr(
                article,
                "importance",
                0,
            ),
            entities=getattr(
                article,
                "entities",
                [],
            ),
            score=getattr(
                article,
                "score",
                0,
            ),
        )


# ==============================================================
# OPTIONAL FUNCTION-LEVEL API
# ==============================================================

def collect_indian_market_news(
    feeds: Iterable[str] | None = None,
) -> list[NewsArticle]:
    """
    Convenience function for callers that do not need to
    instantiate IndianMarketNews directly.
    """

    collector = IndianMarketNews(
        feeds=feeds,
    )

    return collector.collect()
