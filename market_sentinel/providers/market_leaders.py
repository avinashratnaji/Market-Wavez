"""Readable quote panels for systemically important Indian and US companies."""

from __future__ import annotations

from market_sentinel.briefs.models import ExternalMarketQuote
from market_sentinel.providers.external_markets import ExternalMarketsProvider


class MarketLeadersProvider:
    INDIA = {
        "RELIANCE.NS": ("RELIANCE", "Reliance Industries"),
        "HDFCBANK.NS": ("HDFCBANK", "HDFC Bank"),
        "BHARTIARTL.NS": ("BHARTIARTL", "Bharti Airtel"),
        "TCS.NS": ("TCS", "Tata Consultancy Services"),
        "ICICIBANK.NS": ("ICICIBANK", "ICICI Bank"),
        "SBIN.NS": ("SBIN", "State Bank of India"),
        "INFY.NS": ("INFY", "Infosys"),
        "BAJFINANCE.NS": ("BAJFINANCE", "Bajaj Finance"),
        "LICI.NS": ("LICI", "Life Insurance Corporation of India"),
        "HINDUNILVR.NS": ("HINDUNILVR", "Hindustan Unilever"),
    }
    MAGNIFICENT_SEVEN = {
        "AAPL": ("AAPL", "Apple"), "MSFT": ("MSFT", "Microsoft"),
        "GOOGL": ("GOOGL", "Alphabet"), "AMZN": ("AMZN", "Amazon"),
        "NVDA": ("NVDA", "NVIDIA"), "META": ("META", "Meta Platforms"),
        "TSLA": ("TSLA", "Tesla"),
    }

    def fetch_india(self) -> list[ExternalMarketQuote]:
        return self._fetch(self.INDIA, "₹")

    def fetch_us(self) -> list[ExternalMarketQuote]:
        return self._fetch(self.MAGNIFICENT_SEVEN, "$")

    @staticmethod
    def _fetch(universe: dict[str, tuple[str, str]], unit: str) -> list[ExternalMarketQuote]:
        data = ExternalMarketsProvider._yahoo_charts(list(universe))
        output: list[ExternalMarketQuote] = []
        for yahoo_symbol, (ticker, company) in universe.items():
            value, percent = data.get(yahoo_symbol, (None, None))
            if value is None or percent is None:
                continue
            output.append(ExternalMarketQuote(ticker, value, percent, unit, company))
        return output
