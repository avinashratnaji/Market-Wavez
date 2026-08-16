"""
analytics/engine.py

Central Analytics Engine.

Responsible for coordinating all analyzers and
producing AssetAnalytics objects from collected
market data.

Author : Market Sentinel
Version : 0.5.0
"""

from datetime import datetime

from market_sentinel.analytics.models import AssetAnalytics
from market_sentinel.analytics.analyzers.trend import TrendAnalyzer
from market_sentinel.analytics.analyzers.momentum import MomentumAnalyzer
from market_sentinel.analytics.analyzers.volume import VolumeAnalyzer
from market_sentinel.analytics.analyzers.scoring import ScoringAnalyzer
from market_sentinel.analytics.enums import MarketType


class AnalyticsEngine:
    """
    Main analytics pipeline.

    Public API:
        analyze(records)

    Input:
        List[MarketData]

    Output:
        List[AssetAnalytics]
    """

    def analyze(self, records):
        """
        Analyse an entire market snapshot.
        """

        return [
            self._analyze_record(record)
            for record in records
        ]

    def _analyze_record(self, record) -> AssetAnalytics:
        """
        Analyse a single market record.
        """

        asset = AssetAnalytics(
            symbol=record.symbol,
            name=record.name,
            market=self._market_type(record.exchange),
            current_price=float(record.price),
            daily_change_pct=float(record.daily_change_pct),
            weekly_change_pct=float(record.weekly_change_pct),
            monthly_change_pct=float(record.monthly_change_pct),
            current_volume=float(record.current_volume),
            average_volume_20d=float(record.average_volume_20d),
            last_updated=datetime.now(),
        )

        # ----------------------------------
        # Trend
        # ----------------------------------
        trend, trend_reason = TrendAnalyzer.calculate(
            asset.daily_change_pct,
            asset.weekly_change_pct,
            asset.monthly_change_pct,
        )

        asset.trend = trend
        asset.trend_reason = trend_reason

        # ----------------------------------
        # Momentum
        # ----------------------------------
        momentum, momentum_reason = MomentumAnalyzer.calculate(
            asset.daily_change_pct,
            asset.weekly_change_pct,
            asset.monthly_change_pct,
        )

        asset.momentum = momentum
        asset.momentum_reason = momentum_reason

        # ----------------------------------
        # Volume
        # ----------------------------------
        volume = VolumeAnalyzer.calculate(
            current_volume=asset.current_volume,
            average_volume=asset.average_volume_20d,
            daily_change=asset.daily_change_pct,
        )

        asset.volume_ratio = volume.ratio
        asset.relative_volume = volume.ratio
        asset.volume_signal = volume.signal
        asset.volume_reason = volume.reason

        # ----------------------------------
        # Market Intelligence Score
        # ----------------------------------
        score, score_reason = ScoringAnalyzer.calculate(
            daily_change=asset.daily_change_pct,
            weekly_change=asset.weekly_change_pct,
            monthly_change=asset.monthly_change_pct,
            trend=trend,
            momentum=momentum,
            volume_signal=volume.signal,
        )

        asset.importance_score = score

        # Optional: store score explanation if your model supports it
        if hasattr(asset, "score_reason"):
            asset.score_reason = score_reason

        return asset

    def _market_type(self, exchange: str) -> MarketType:
        exchange = (exchange or "").upper()

        if exchange in ("NSE", "BSE"):
            return MarketType.INDIAN

        if exchange in ("NYSE", "NASDAQ"):
            return MarketType.US

        if exchange in ("COMEX", "NYMEX"):
            return MarketType.COMMODITY

        if exchange == "CRYPTO":
            return MarketType.CRYPTO

        if exchange == "KOSPI":
            return MarketType.KOREA

        return MarketType.GLOBAL