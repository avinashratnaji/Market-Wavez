"""
news/intelligence.py

Market Sentinel News Intelligence Engine

Converts raw NewsEvent objects into enriched NewsIntelligence.

Author : Market Sentinel
Version : 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from market_sentinel.news.models import (
    NewsEvent,
    NewsIntelligence,
)


class NewsIntelligenceEngine:

    POSITIVE = {
        "surge",
        "growth",
        "record",
        "beat",
        "approval",
        "profit",
        "expansion",
        "upgrade",
        "bullish",
        "gain",
        "strong",
        "buyback",
        "dividend",
        "investment",
        "orders",
    }

    NEGATIVE = {
        "fall",
        "loss",
        "downgrade",
        "fraud",
        "war",
        "crash",
        "lawsuit",
        "default",
        "decline",
        "bearish",
        "selloff",
        "bankruptcy",
        "inflation",
        "recession",
        "slowdown",
    }

    IMPACT = {
        "rbi": 95,
        "repo": 95,
        "fed": 98,
        "interest rate": 95,
        "inflation": 90,
        "cpi": 88,
        "gdp": 92,
        "budget": 92,
        "oil": 88,
        "crude": 88,
        "war": 99,
        "bitcoin": 85,
        "ethereum": 82,
        "nifty": 80,
        "banknifty": 82,
    }

    SOURCE_CONFIDENCE = {
        "Reuters": 98,
        "Bloomberg": 98,
        "NSE": 97,
        "BSE": 97,
        "RBI": 99,
        "SEBI": 99,
        "Moneycontrol": 90,
        "CNBC": 90,
    }

    MARKET_KEYWORDS = {
        "INDIA": {"rbi", "nifty", "banknifty", "sensex", "india"},
        "US": {"fed", "dow", "nasdaq", "s&p", "usa"},
        "CRYPTO": {"bitcoin", "ethereum", "crypto"},
        "COMMODITY": {"gold", "silver", "crude", "oil"},
        "GLOBAL": {"world", "global", "g20", "imf"},
    }

    SECTOR_KEYWORDS = {
        "BANKING": {"bank", "rbi", "hdfc", "icici", "sbi"},
        "IT": {"software", "tcs", "infosys", "wipro", "hcl"},
        "AUTO": {"maruti", "tata motors", "mahindra"},
        "PHARMA": {"pharma", "drug", "hospital"},
        "ENERGY": {"oil", "gas", "power", "coal"},
        "METALS": {"steel", "aluminium", "copper"},
        "FMCG": {"hindustan unilever", "itc", "nestle"},
        "REAL ESTATE": {"real estate", "housing"},
        "DEFENCE": {"missile", "defence", "army"},
    }

    ASSET_KEYWORDS = {
        "HDFCBANK": {"hdfc"},
        "ICICIBANK": {"icici"},
        "SBIN": {"sbi"},
        "RELIANCE": {"reliance"},
        "TCS": {"tcs"},
        "INFY": {"infosys"},
        "BANKNIFTY": {"banknifty"},
        "NIFTY": {"nifty"},
        "BTC": {"bitcoin"},
        "ETH": {"ethereum"},
        "GOLD": {"gold"},
    }

    def analyze(self, event: NewsEvent) -> NewsIntelligence:

        text = f"{event.title} {event.summary}".lower()

        sentiment = self._sentiment(text)

        return NewsIntelligence(
            title=event.title,
            summary=event.summary,
            sentiment=sentiment,
            impact_score=self._impact(text),
            confidence=self._confidence(event.source),
            priority=self._priority(text),
            affected_markets=self._match(
                text,
                self.MARKET_KEYWORDS,
            ),
            affected_sectors=self._match(
                text,
                self.SECTOR_KEYWORDS,
            ),
            affected_assets=self._match(
                text,
                self.ASSET_KEYWORDS,
            ),
            keywords=self._keywords(text),
        )

    def analyze_all(
        self,
        events: Iterable[NewsEvent],
    ) -> list[NewsIntelligence]:

        return [
            self.analyze(event)
            for event in events
        ]

    def _sentiment(self, text: str) -> str:

        positive = sum(
            word in text
            for word in self.POSITIVE
        )

        negative = sum(
            word in text
            for word in self.NEGATIVE
        )

        score = positive - negative

        if score >= 2:
            return "VERY_BULLISH"

        if score == 1:
            return "BULLISH"

        if score == 0:
            return "NEUTRAL"

        if score == -1:
            return "BEARISH"

        return "VERY_BEARISH"

    def _impact(self, text: str) -> int:

        score = 30

        for keyword, value in self.IMPACT.items():
            if keyword in text:
                score = max(score, value)

        return score

    def _confidence(self, source: str) -> int:

        return self.SOURCE_CONFIDENCE.get(
            source,
            70,
        )

    def _priority(self, text: str) -> str:

        impact = self._impact(text)

        if impact >= 95:
            return "CRITICAL"

        if impact >= 85:
            return "HIGH"

        if impact >= 70:
            return "MEDIUM"

        return "LOW"

    def _match(
        self,
        text: str,
        mapping: dict[str, set[str]],
    ) -> list[str]:

        matches = []

        for name, words in mapping.items():

            if any(
                word in text
                for word in words
            ):
                matches.append(name)

        return matches

    def _keywords(
        self,
        text: str,
    ) -> list[str]:

        words = []

        for word in text.split():

            word = word.strip(",.:;()[]{}")

            if len(word) >= 5:
                words.append(word)

        return sorted(set(words))[:20]