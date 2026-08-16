"""
analytics/models.py

Data models used by the Analytics Engine.

Author : Market Sentinel
Version: 0.4.0
"""

from dataclasses import dataclass
from datetime import datetime

from .enums import (
    Trend,
    Momentum,
    RiskLevel,
    MarketType,
    Signal, VolumeSignal,
)


@dataclass(slots=True)
class AssetAnalytics:
    """
    Standard analytics model shared across the application.

    Every analytics calculation should produce one AssetAnalytics object.
    """

    symbol: str
    name: str

    market: MarketType

    current_price: float

    daily_change_pct: float = 0.0
    weekly_change_pct: float = 0.0
    monthly_change_pct: float = 0.0

    trend: Trend = Trend.SIDEWAYS
    trend_reason: str = ""
    momentum: Momentum = Momentum.MODERATE
    momentum_reason: str = ""
    risk: RiskLevel = RiskLevel.MEDIUM

    importance_score: float = 0.0
    score_reasons: list[str] | None = None
    market_health_score: float = 0.0

    signal: Signal = Signal.WATCH

    last_updated: datetime | None = None

    # =========================
    # Volume Intelligence
    # =========================

    current_volume: float = 0.0

    average_volume_5d: float = 0.0
    average_volume_20d: float = 0.0
    average_volume_50d: float = 0.0

    volume_ratio: float = 0.0

    relative_volume: float = 0.0

    volume_signal: VolumeSignal = VolumeSignal.NORMAL
    volume_reason: str = ""