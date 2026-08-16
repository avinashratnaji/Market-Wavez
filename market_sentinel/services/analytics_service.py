"""
analytics_service.py

Service responsible for converting raw market data
into AssetAnalytics objects.

Author : Market Sentinel
Version : 0.5.0
"""

from __future__ import annotations

from market_sentinel.analytics.engine import AnalyticsEngine
from market_sentinel.analytics.models import AssetAnalytics
from market_sentinel.repositories.market_data_repository import (
    MarketDataRepository,
)


class AnalyticsService:
    """
    Coordinates analytics execution.

    Responsibilities
    ----------------
    - Fetch latest market snapshot
    - Execute analytics engine
    - Return analysed assets
    """

    def __init__(self) -> None:
        self.repository = MarketDataRepository()
        self.engine = AnalyticsEngine()

    def analyze_latest(self) -> list[AssetAnalytics]:
        """
        Analyse the latest collected market snapshot.
        """

        records = self.repository.get_latest_snapshot()

        if not records:
            return []

        return self.engine.analyze(records)