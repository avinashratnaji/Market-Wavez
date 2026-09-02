"""
briefs/models.py

Models used by Market Briefs.

Author : Market Sentinel
Version : 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from market_sentinel.news.models import NewsArticle
from market_sentinel.providers.angelone.models import (
    IndexSnapshot,
)
from market_sentinel.providers.macro_calendar import MacroEvent


# ==========================================================
# News
# ==========================================================

@dataclass(slots=True)
class NewsItem:

    title: str

    summary: str

    source: str

    impact: str

    score: int

    sectors: tuple[str, ...] = ()

    stocks: tuple[str, ...] = ()


# ==========================================================
# Sector
# ==========================================================

@dataclass(slots=True)
class SectorSnapshot:

    name: str

    value: float

    percent_change: float


# ==========================================================
# Stock
# ==========================================================

@dataclass(slots=True)
class StockSnapshot:

    symbol: str

    price: float

    percent_change: float


@dataclass(slots=True)
class InvestorFlowSnapshot:
    """Daily cash-market institutional flow, in INR crore."""

    trade_date: datetime
    fii_buy: float | None = None
    fii_sell: float | None = None
    fii_net: float | None = None
    dii_buy: float | None = None
    dii_sell: float | None = None
    dii_net: float | None = None
    source: str = "NSE"


@dataclass(slots=True)
class IpoGmpSnapshot:
    """Indicative grey-market premium for one active IPO.

    GMP is an informal market indication, not an official exchange price.
    """

    name: str
    gmp: float | None = None
    price_band_high: float | None = None
    issue_type: str = ""
    lot_size: int | None = None
    about: str = ""
    details_url: str = ""
    subscription_open: datetime | None = None
    subscription_close: datetime | None = None
    updated_at: datetime | None = None
    source: str = ""

    @property
    def gmp_percent(self) -> float | None:
        if self.gmp is None or not self.price_band_high:
            return None
        return self.gmp / self.price_band_high * 100


@dataclass(slots=True)
class ExternalMarketQuote:
    """A non-Indian index, ADR, commodity, or crypto spot/futures quote."""

    name: str
    value: float
    percent_change: float
    unit: str = ""
    note: str = ""
    source: str = "Yahoo Finance"


@dataclass(slots=True)
class StockResearchSignal:
    """Explainable stock-screen result, never an execution instruction."""

    symbol: str
    company_name: str
    price: float
    percent_change: float
    bias: str
    horizon: str
    score: int
    reasons: tuple[str, ...]
    source: str = "NSE + Yahoo Finance"
    revenue_growth_yoy: float | None = None
    earnings_improvement_yoy: float | None = None
    research_confidence: int = 0
    growth_score: int = 0
    quality_score: int = 0
    ownership_score: int = 0
    technical_score: int = 0
    catalyst_score: int = 0
    risk_score: int = 0
    key_risks: tuple[str, ...] = ()
    data_gaps: tuple[str, ...] = ()
    metrics: tuple[str, ...] = ()
    report_url: str = ""


# ==========================================================
# Morning Brief
# ==========================================================

@dataclass(slots=True)
class MorningBrief:

    generated_at: datetime

    health_score: int

    market_sentiment: str

    confidence: int

    news: list[NewsItem] = field(default_factory=list)

    indices: list[IndexSnapshot] = field(default_factory=list)

    sectors: list[SectorSnapshot] = field(default_factory=list)

    gainers: list[StockSnapshot] = field(default_factory=list)

    losers: list[StockSnapshot] = field(default_factory=list)

    top_news: list[NewsArticle] = field(default_factory=list)

    indian_news: list[NewsArticle] = field(default_factory=list)

    # Additional unique events after the five detailed India stories.  These
    # are rendered at the appropriate scheduled window, not duplicated.
    indian_events: list[NewsArticle] = field(default_factory=list)

    global_impact_news: list[NewsArticle] = field(default_factory=list)

    # Additional unique US/global market events after the five lead stories.
    us_events: list[NewsArticle] = field(default_factory=list)

    crypto_news: list[NewsArticle] = field(default_factory=list)

    global_indices: list[ExternalMarketQuote] = field(default_factory=list)

    indian_adrs: list[ExternalMarketQuote] = field(default_factory=list)

    commodities: list[ExternalMarketQuote] = field(default_factory=list)

    crypto: list[ExternalMarketQuote] = field(default_factory=list)

    # Fresh 10 AM F&O analysis, optionally compared with the stored previous
    # EOD chain snapshot.  These are factual research cards, not calls.
    option_research: list = field(default_factory=list)
    option_research_failures: list[str] = field(default_factory=list)

    us_gainers: list[ExternalMarketQuote] = field(default_factory=list)

    us_losers: list[ExternalMarketQuote] = field(default_factory=list)

    india_leaders: list[ExternalMarketQuote] = field(default_factory=list)

    us_mega_caps: list[ExternalMarketQuote] = field(default_factory=list)

    macro_events: list[MacroEvent] = field(default_factory=list)

    investor_flows: InvestorFlowSnapshot | None = None

    top_ipos: list[IpoGmpSnapshot] = field(default_factory=list)

    fo_ban_symbols: list[str] = field(default_factory=list)

    fo_ban_available: bool = False

    gift_nifty: ExternalMarketQuote | None = None

    ai_summary: str = ""

    ai_summary_source: str = ""

    today_bullish: list[StockResearchSignal] = field(default_factory=list)

    today_bearish: list[StockResearchSignal] = field(default_factory=list)

    week_bullish: list[StockResearchSignal] = field(default_factory=list)

    week_bearish: list[StockResearchSignal] = field(default_factory=list)

    growth_candidates: list[StockResearchSignal] = field(default_factory=list)

    us_move_reasons: dict[str, str] = field(default_factory=dict)

    crypto_move_reasons: dict[str, str] = field(default_factory=dict)
