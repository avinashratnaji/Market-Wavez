"""
analytics/trend.py

Trend detection for Market Sentinel.

Author : Market Sentinel
Version: 0.4.0
"""

from market_sentinel.analytics.enums import Trend


class TrendAnalyzer:
    """
    Determines market trend using percentage changes.
    """

    @staticmethod
    def calculate(
        daily_change: float,
        weekly_change: float,
        monthly_change: float,
    ) -> tuple[Trend, str]:

        score = 0

        if daily_change > 1:
            score += 1
        elif daily_change < -1:
            score -= 1

        if weekly_change > 2:
            score += 1
        elif weekly_change < -2:
            score -= 1

        if monthly_change > 5:
            score += 1
        elif monthly_change < -5:
            score -= 1

        if score >= 2:
            return (
                Trend.BULLISH,
                f"Daily {daily_change:.2f}% | Weekly {weekly_change:.2f}% | Monthly {monthly_change:.2f}%"
            )

        if score <= -2:
            return (
                Trend.BEARISH,
                f"Daily {daily_change:.2f}% | Weekly {weekly_change:.2f}% | Monthly {monthly_change:.2f}%"
            )

        return (
            Trend.SIDEWAYS,
            f"Daily {daily_change:.2f}% | Weekly {weekly_change:.2f}% | Monthly {monthly_change:.2f}%"
        )