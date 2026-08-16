"""
briefs/health.py

Calculates overall market health.

Author : Market Sentinel
Version : 1.0.0
"""

from __future__ import annotations

from market_sentinel.briefs.models import (
    MorningBrief,
)


class MarketHealthEngine:
    """
    Calculates market health score.
    """

    def calculate(
        self,
        brief: MorningBrief,
    ) -> MorningBrief:

        score = 50

        # =====================================================
        # Indices
        # =====================================================

        positive = sum(
            1
            for index in brief.indices
            if index.percent_change > 0
        )

        negative = len(brief.indices) - positive

        score += positive * 3
        score -= negative * 3

        # =====================================================
        # Sectors
        # =====================================================

        positive = sum(
            1
            for sector in brief.sectors
            if sector.percent_change > 0
        )

        negative = len(brief.sectors) - positive

        score += positive * 2
        score -= negative * 2

        # =====================================================
        # Gainers vs Losers
        # =====================================================

        score += len(brief.gainers)
        score -= len(brief.losers)

        # =====================================================
        # Clamp
        # =====================================================

        score = max(0, min(score, 100))

        brief.health_score = score

        if score >= 75:
            brief.market_sentiment = "Bullish"

        elif score >= 55:
            brief.market_sentiment = "Neutral"

        else:
            brief.market_sentiment = "Bearish"

        brief.confidence = score

        return brief