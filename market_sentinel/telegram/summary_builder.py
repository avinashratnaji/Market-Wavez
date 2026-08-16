"""
telegram/summary_builder.py

Builds a structured market summary from analytics results.

Author : Market Sentinel
Version : 1.0.0
"""

from dataclasses import dataclass

from market_sentinel.services.analytics_service import AnalyticsService


@dataclass(slots=True)
class MarketSummary:
    """
    Structured summary of the current market.
    """

    generated_at: str

    assets: list

    total_assets: int


class SummaryBuilder:
    """
    Builds a structured market summary.
    """

    def __init__(self):
        self.analytics = AnalyticsService()

    def build(self) -> MarketSummary:

        analytics = self.analytics.analyze_latest()

        return MarketSummary(
            generated_at=(
                analytics[0].last_updated.strftime("%d-%m-%Y %H:%M")
                if analytics and analytics[0].last_updated
                else ""
            ),
            assets=analytics,
            total_assets=len(analytics),
        )