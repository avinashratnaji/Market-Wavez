"""
analytics/enums.py

Common enumerations used by the Analytics Engine.

Author : Market Sentinel
Version: 0.4.0
"""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class Trend(str, Enum):
    """Overall price trend."""
    BULLISH = "Bullish"
    BEARISH = "Bearish"
    SIDEWAYS = "Sideways"


class Momentum(str, Enum):
    """Momentum strength."""
    STRONG = "Strong"
    MODERATE = "Moderate"
    WEAK = "Weak"


class RiskLevel(str, Enum):
    """Risk classification."""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class MarketType(str, Enum):
    """Supported market categories."""
    INDIAN = "Indian Market"
    US = "US Market"
    CRYPTO = "Cryptocurrency"
    COMMODITY = "Commodity"
    KOREA = "KOSPI"
    GLOBAL = "Global"


class Signal(str, Enum):
    """Trading/Monitoring signal."""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    WATCH = "WATCH"

class VolumeSignal(str, Enum):
    """Volume activity classification."""
    NORMAL = "Normal"
    ABOVE_AVERAGE = "Above Average"
    HIGH = "High"
    VERY_HIGH = "Very High"
    UNUSUAL = "Unusual Activity"

class ActivityType(str, Enum):
    """
    Type of market activity.
    """
    NORMAL = "Normal"
    ACCUMULATION = "Accumulation"
    DISTRIBUTION = "Distribution"
    PANIC_SELLING = "Panic Selling"
    PANIC_BUYING = "Panic Buying"
    BREAKOUT = "Breakout"
    BREAKDOWN = "Breakdown"
    UNUSUAL = "Unusual Activity"

@dataclass(slots=True)
class VolumeAnalysis:
    ratio: float
    signal: VolumeSignal
    activity: ActivityType
    confidence: float
    reason: str

@dataclass(slots=True)
class MarketEvent:
    title: str
    description: str
    severity: int
    confidence: float
    asset: str
    category: str
    timestamp: datetime

