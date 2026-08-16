"""Resilient global, commodity, crypto, and Indian ADR market snapshots."""

from __future__ import annotations

from collections.abc import Iterable
import re

import requests
from bs4 import BeautifulSoup
from loguru import logger

from market_sentinel.briefs.models import ExternalMarketQuote


class ExternalMarketsProvider:
    """Fetch a coherent cross-market snapshot from Yahoo Finance.

    One batched request keeps quotes internally consistent and avoids mixing
    different timestamps from multiple unrelated web pages.
    """

    GLOBAL = {
        "NASDAQ": "^IXIC", "S&P 500": "^GSPC", "DOW JONES": "^DJI",
        "KOSPI": "^KS11", "NIKKEI": "^N225", "DAX": "^GDAXI", "FTSE 100": "^FTSE",
    }
    ADRS = {"INFY ADR": "INFY", "HDFC Bank ADR": "HDB", "ICICI Bank ADR": "IBN"}
    CRYPTO = {"BTC": "BTC-USD", "ETH": "ETH-USD", "SOL": "SOL-USD", "XRP": "XRP-USD"}
    COMMODITIES = {"Brent": "BZ=F"}
    FX = "INR=X"
    GOLD = "GC=F"
    SILVER = "SI=F"
    INDIA_GOLD_URL = "https://www.goodreturns.in/gold-rates/"
    INDIA_SILVER_URL = "https://www.goodreturns.in/silver-rates/"
    REQUEST_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131 Safari/537.36",
        "Accept-Language": "en-IN,en;q=0.9",
    }

    def fetch(self) -> tuple[list[ExternalMarketQuote], list[ExternalMarketQuote], list[ExternalMarketQuote], list[ExternalMarketQuote]]:
        try:
            import yfinance as yf

            symbols = list(self.GLOBAL.values()) + list(self.ADRS.values()) + list(self.CRYPTO.values()) + list(self.COMMODITIES.values()) + [self.FX, self.GOLD, self.SILVER]
            data = yf.download(symbols, period="5d", interval="1d", group_by="ticker", auto_adjust=False, progress=False, threads=True)
            quote = lambda name, symbol, unit="", note="": self._quote(data, name, symbol, unit, note)
            global_indices = self._present(quote(name, symbol) for name, symbol in self.GLOBAL.items())
            adrs = self._present(quote(name, symbol) for name, symbol in self.ADRS.items())
            crypto = self._present(quote(name, symbol, "$") for name, symbol in self.CRYPTO.items())
            commodities = self._present(quote(name, symbol, "$", "Higher crude can pressure India") for name, symbol in self.COMMODITIES.items())
            inr = self._last(data, self.FX)
            gold = self._last(data, self.GOLD)
            silver = self._last(data, self.SILVER)
            # Jewellery-market rates must not be labelled as an Indian price
            # when they are only a COMEX USD quote converted to INR.
            commodities[0:0] = self._fetch_indian_bullion()
            if inr and gold:
                commodities.append(ExternalMarketQuote(
                    "Gold (COMEX INR equiv.)", gold * inr / 31.1035 * 10,
                    self._percent(data, self.GOLD), "₹/10g", "International futures converted to INR",
                ))
            if inr and silver:
                commodities.append(ExternalMarketQuote(
                    "Silver (COMEX INR equiv.)", silver * inr / 31.1035 * 1000,
                    self._percent(data, self.SILVER), "₹/kg", "International futures converted to INR",
                ))
            return global_indices, adrs, commodities, crypto
        except Exception as exc:
            logger.warning("Global market snapshot unavailable: {}", exc)
            return [], [], [], []

    @classmethod
    def _fetch_indian_bullion(cls) -> list[ExternalMarketQuote]:
        """Fetch India retail bullion rates; never substitute a USD conversion."""
        try:
            gold_html = requests.get(cls.INDIA_GOLD_URL, headers=cls.REQUEST_HEADERS, timeout=10).text
            silver_html = requests.get(cls.INDIA_SILVER_URL, headers=cls.REQUEST_HEADERS, timeout=10).text
            gold = cls._parse_indian_gold(gold_html)
            silver = cls._parse_indian_silver(silver_html)
            return [quote for quote in (gold, silver) if quote is not None]
        except requests.RequestException as exc:
            logger.warning("Indian bullion source unavailable: {}", exc)
            return []

    @staticmethod
    def _clean_text(html: str) -> str:
        return BeautifulSoup(html, "html.parser").get_text(" ", strip=True).replace("\xa0", " ")

    @classmethod
    def _parse_indian_gold(cls, html: str) -> ExternalMarketQuote | None:
        text = cls._clean_text(html)

        match = re.search(
            r"24K[\s\xa0]*Gold[\s\xa0]*/[\s\xa0]*g"
            r"[\s\xa0]*₹[\s\xa0]*([\d,]+)"
            r"[\s\xa0]*([+-])[\s\xa0]*([\d,]+)",
            text,
            re.I,
        )

        if not match:
            logger.warning("Unable to parse India 24K gold rate from Goodreturns")
            return None

        per_gram = float(
            match.group(1).replace(",", "")
        )

        change = float(
            match.group(3).replace(",", "")
        )

        if match.group(2) == "-":
            change = -change

        previous = per_gram - change

        percent = (
            change / previous * 100
            if previous
            else 0.0
        )

        return ExternalMarketQuote(
            "Gold 24K INDIA",
            per_gram * 10,
            percent,
            "₹/10g",
            "India retail rate; Goodreturns",
        )

    @classmethod
    def _parse_indian_silver(cls, html: str) -> ExternalMarketQuote | None:
        text = cls._clean_text(html)
        match = re.search(r"Silver\s*/\s*kg\s*₹\s*([\d,]+)", text, re.I)
        if not match:
            return None
        per_kg = float(match.group(1).replace(",", ""))
        day_match = re.search(r"1000\s*₹\s*([\d,]+)\s*₹\s*([\d,]+)", text)
        yesterday = float(day_match.group(2).replace(",", "")) if day_match else per_kg
        percent = (per_kg / yesterday - 1) * 100 if yesterday else 0.0
        return ExternalMarketQuote("Silver INDIA", per_kg, percent, "₹/kg", "India retail rate; Goodreturns")

    @classmethod
    def _present(cls, quotes: Iterable[ExternalMarketQuote | None]) -> list[ExternalMarketQuote]:
        return [item for item in quotes if item is not None]

    @classmethod
    def _quote(cls, data, name: str, symbol: str, unit: str = "", note: str = "") -> ExternalMarketQuote | None:
        value = cls._last(data, symbol)
        percent = cls._percent(data, symbol)
        if value is None or percent is None:
            return None
        return ExternalMarketQuote(name, value, percent, unit, note)

    @staticmethod
    def _series(data, symbol: str):
        try:
            series = data[symbol]["Close"].dropna()
            return series
        except (KeyError, TypeError, AttributeError):
            return None

    @classmethod
    def _last(cls, data, symbol: str) -> float | None:
        series = cls._series(data, symbol)
        return float(series.iloc[-1]) if series is not None and not series.empty else None

    @classmethod
    def _percent(cls, data, symbol: str) -> float | None:
        series = cls._series(data, symbol)
        if series is None or len(series) < 2 or not float(series.iloc[-2]):
            return None
        return (float(series.iloc[-1]) / float(series.iloc[-2]) - 1) * 100
