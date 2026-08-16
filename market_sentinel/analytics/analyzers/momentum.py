"""
analytics/momentum.py

Momentum analysis for Market Sentinel.

Determines how strong the current market movement is.

Author : Market Sentinel
Version: 0.4.0
"""

from market_sentinel.analytics.enums import Momentum


class MomentumAnalyzer:
    """
    Determines momentum strength using price changes.
    """

    @staticmethod
    def calculate(
        daily_change: float,
        weekly_change: float,
        monthly_change: float,
    ) -> tuple[Momentum, str]:

        score = (
            abs(daily_change)
            + abs(weekly_change) / 2
            + abs(monthly_change) / 4
        )

        if score >= 8:
            return (
                Momentum.STRONG,
                f"Strong movement detected (Score: {score:.2f})"
            )

        if score >= 4:
            return (
                Momentum.MODERATE,
                f"Moderate movement detected (Score: {score:.2f})"
            )

        return (
            Momentum.WEAK,
            f"Weak movement detected (Score: {score:.2f})"
        )