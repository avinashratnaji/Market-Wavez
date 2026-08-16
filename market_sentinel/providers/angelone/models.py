"""
providers/angelone/models.py

Core models used by the Angel One provider.

Author : Market Sentinel
Version : 2.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


# ==========================================================
# Base Snapshot
# ==========================================================

@dataclass(slots=True)
class MarketSnapshot:
    """
    Base snapshot returned from any market provider.

    Stocks
    Indices
    Commodities
    Crypto
    ETFs
    Futures
    """

    name: str

    exchange: str

    token: str

    value: float

    change: float

    percent_change: float

    open: float

    high: float

    low: float

    close: float

    volume: float

    updated_at: datetime

    # -----------------------------------------------------

    @property
    def is_positive(self) -> bool:
        return self.percent_change >= 0

    @property
    def arrow(self) -> str:
        return "▲" if self.is_positive else "▼"

    @property
    def color(self) -> str:
        return "🟢" if self.is_positive else "🔴"

    @property
    def sign(self) -> str:
        return "+" if self.is_positive else ""

    @property
    def formatted_change(self) -> str:
        return f"{self.arrow} {self.sign}{self.percent_change:.2f}%"

    DISPLAY_NAMES = {
        "NIFTY": "NIFTY 50",
        "BANKNIFTY": "BANK NIFTY",
        "FINNIFTY": "FIN NIFTY",
        "NIFTY MIDCAP 50": "MIDCAP 50",
        "Nifty Midcap 50": "MIDCAP 50",
        "NIFTY IT": "NIFTY IT",
        "Nifty IT": "NIFTY IT",
        "NIFTY PHARMA": "NIFTY PHARMA",
        "Nifty Pharma": "NIFTY PHARMA",
        "INDIA VIX": "INDIA VIX",
        "India VIX": "INDIA VIX",
        "SENSEX": "SENSEX",
    }

    @property
    def telegram_line(self) -> str:
        display_name = self.DISPLAY_NAMES.get(
            self.name,
            self.name,
        )

        return (
            f"{self.color} "
            f"{display_name:<16}"
            f"{self.value:>12,.2f}   "
            f"{self.arrow} "
            f"{self.change:+,.2f} "
            f"({self.percent_change:+.2f}%)"
        )


# ==========================================================
# Index
# ==========================================================

@dataclass(slots=True)
class IndexSnapshot(MarketSnapshot):
    pass


# ==========================================================
# Stock
# ==========================================================

@dataclass(slots=True)
class StockSnapshot(MarketSnapshot):

    sector: str | None = None

    delivery_percentage: float | None = None


# ==========================================================
# Commodity
# ==========================================================

@dataclass(slots=True)
class CommoditySnapshot(MarketSnapshot):

    unit: str = ""


# ==========================================================
# Crypto
# ==========================================================

@dataclass(slots=True)
class CryptoSnapshot(MarketSnapshot):

    market_cap: float | None = None


# ==========================================================
# Market Containers
# ==========================================================

@dataclass(slots=True)
class IndianMarketSnapshot:

    indices: list[IndexSnapshot]

    sectors: list[IndexSnapshot]

    gainers: list[StockSnapshot]

    losers: list[StockSnapshot]


@dataclass(slots=True)
class GlobalMarketSnapshot:

    indices: list[IndexSnapshot]

    gainers: list[StockSnapshot]

    losers: list[StockSnapshot]


@dataclass(slots=True)
class CommodityMarketSnapshot:

    commodities: list[CommoditySnapshot]


@dataclass(slots=True)
class CryptoMarketSnapshot:

    crypto: list[CryptoSnapshot]