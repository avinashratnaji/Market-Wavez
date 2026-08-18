"""Typed inputs and outputs for the options research radar.

These models describe observed market structure. They do not represent a
recommendation, target price, or instruction to trade.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class OptionContractQuote:
    strike: float
    option_type: str
    open_interest: int = 0
    change_in_open_interest: int = 0
    volume: int = 0
    implied_volatility: float | None = None
    last_price: float | None = None


@dataclass(frozen=True, slots=True)
class OptionChainSnapshot:
    symbol: str
    spot_price: float
    expiry: str
    captured_at: datetime
    contracts: tuple[OptionContractQuote, ...]
    source: str


@dataclass(frozen=True, slots=True)
class TechnicalSnapshot:
    symbol: str
    close: float
    ema_20: float | None
    ema_50: float | None
    rsi_14: float | None
    volume: float | None
    average_volume_20: float | None
    captured_at: datetime

    @property
    def relative_volume(self) -> float | None:
        if not self.volume or not self.average_volume_20:
            return None
        return self.volume / self.average_volume_20


@dataclass(frozen=True, slots=True)
class MarketEvent:
    """A sourced company event or headline relevant to a research card."""

    title: str
    source: str
    url: str = ""
    severity: str = "Medium"
    category: str = "News"
    impact: str = "Review the source before relying on this context"


@dataclass(frozen=True, slots=True)
class OptionResearchSetup:
    symbol: str
    display_name: str
    bias: str
    confidence_score: int
    evidence: tuple[str, ...]
    support: float | None
    resistance: float | None
    pcr: float | None
    invalidation: str
    risk_notes: tuple[str, ...]
    market_events: tuple[MarketEvent, ...]
    source: str
    captured_at: datetime
    data_quality: str
    technicals: TechnicalSnapshot
    chain: OptionChainSnapshot


@dataclass(frozen=True, slots=True)
class WatchlistItem:
    symbol: str
    display_name: str
    yahoo_symbol: str
    nse_option_symbol: str
    event_risk: str = "Check corporate calendar before acting"


DEFAULT_OPTIONS_WATCHLIST: tuple[WatchlistItem, ...] = (
    WatchlistItem("RELIANCE", "Reliance Industries", "RELIANCE.NS", "RELIANCE"),
    WatchlistItem("HDFCBANK", "HDFC Bank", "HDFCBANK.NS", "HDFCBANK"),
    WatchlistItem("ICICIBANK", "ICICI Bank", "ICICIBANK.NS", "ICICIBANK"),
    WatchlistItem("SBIN", "State Bank of India", "SBIN.NS", "SBIN"),
    WatchlistItem("INFY", "Infosys", "INFY.NS", "INFY"),
    WatchlistItem("TCS", "TCS", "TCS.NS", "TCS"),
    WatchlistItem("TMPV", "Tata Motors Passenger Vehicles", "TMPV.NS", "TMPV"),
    WatchlistItem("BAJFINANCE", "Bajaj Finance", "BAJFINANCE.NS", "BAJFINANCE"),
    WatchlistItem("AXISBANK", "Axis Bank", "AXISBANK.NS", "AXISBANK"),
    WatchlistItem("HEROMOTOCO", "Hero MotoCorp", "HEROMOTOCO.NS", "HEROMOTOCO"),
)
