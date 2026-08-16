"""
analytics/analyzers/scoring.py

Market Intelligence Scoring Engine

Calculates how important an asset is today based on
price movement, trend, momentum and volume.

Author : Market Sentinel
Version : 0.4.0
"""

from market_sentinel.analytics.enums import (
    Trend,
    Momentum,
    VolumeSignal,
)


class ScoringAnalyzer:
    """
    Calculates the Market Intelligence Score (0–100).
    """

    @staticmethod
    def calculate(
        daily_change: float,
        weekly_change: float,
        monthly_change: float,
        trend: Trend,
        momentum: Momentum,
        volume_signal: VolumeSignal,
    ) -> tuple[float, list[str]]:

        score = 0
        reasons = []

        # ----------------------------------
        # Daily Move
        # ----------------------------------

        if abs(daily_change) >= 5:
            score += 20
            reasons.append("Large daily price movement")

        elif abs(daily_change) >= 2:
            score += 10
            reasons.append("Moderate daily movement")

        # ----------------------------------
        # Weekly Trend
        # ----------------------------------

        if abs(weekly_change) >= 8:
            score += 15
            reasons.append("Strong weekly trend")

        elif abs(weekly_change) >= 4:
            score += 8

        # ----------------------------------
        # Monthly Trend
        # ----------------------------------

        if abs(monthly_change) >= 15:
            score += 15
            reasons.append("Strong monthly trend")

        elif abs(monthly_change) >= 8:
            score += 8

        # ----------------------------------
        # Trend
        # ----------------------------------

        if trend == Trend.BULLISH:
            score += 10
            reasons.append("Bullish trend")

        elif trend == Trend.BEARISH:
            score += 10
            reasons.append("Bearish trend")

        # ----------------------------------
        # Momentum
        # ----------------------------------

        if momentum == Momentum.STRONG:
            score += 20
            reasons.append("Strong momentum")

        elif momentum == Momentum.MODERATE:
            score += 10

        # ----------------------------------
        # Volume
        # ----------------------------------

        if volume_signal == VolumeSignal.UNUSUAL:
            score += 20
            reasons.append("Unusual trading volume")

        elif volume_signal == VolumeSignal.VERY_HIGH:
            score += 15

        elif volume_signal == VolumeSignal.HIGH:
            score += 10

        return min(score, 100), reasons