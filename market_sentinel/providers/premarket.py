"""NSE pre-market reference data for the morning terminal."""

from __future__ import annotations

import re

import requests
from bs4 import BeautifulSoup
from loguru import logger

from market_sentinel.briefs.models import ExternalMarketQuote


class PreMarketProvider:
    """Read the live NSE F&O securities-ban list without estimating it."""

    NSE_HOME = "https://www.nseindia.com"
    FO_BAN_URL = "https://www.nseindia.com/api/foSecBan"
    BAN_FALLBACK_URLS = (
        "https://www.niftytrader.in/ban-list",
        "https://www.kotakneo.com/futures-and-options/nse-fno-ban-list/",
    )
    GIFT_NIFTY_URL = "https://www.niftytrader.in/gift-nifty-live"

    def __init__(self) -> None:
        self.fo_ban_available = False

    def fetch_fo_ban(self) -> list[str]:
        try:
            session = requests.Session()
            session.headers.update({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131 Safari/537.36",
                "Accept": "application/json,text/plain,*/*",
                "Referer": f"{self.NSE_HOME}/",
            })
            session.get(self.NSE_HOME, timeout=10)
            payload = session.get(self.FO_BAN_URL, timeout=10).json()
            records = payload.get("data", payload) if isinstance(payload, dict) else payload
            if not isinstance(records, list):
                raise ValueError("NSE F&O ban response has no list")
            self.fo_ban_available = True
            symbols = []
            for record in records:
                symbol = record.get("symbol") if isinstance(record, dict) else str(record)
                if symbol:
                    symbols.append(str(symbol).strip())
            return sorted(set(symbols))
        except (requests.RequestException, ValueError, TypeError) as exc:
            logger.warning("F&O ban list unavailable: {}", exc)
        for url in self.BAN_FALLBACK_URLS:
            symbols = self._fetch_ban_fallback(url)
            if symbols is not None:
                self.fo_ban_available = True
                return symbols
        return []

    @staticmethod
    def _fetch_ban_fallback(url: str) -> list[str] | None:
        """Parse a visible ban-list table from an independent public page."""
        try:
            response = requests.get(url, timeout=12, headers={"User-Agent": "Mozilla/5.0 (Market Sentinel)"})
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            for table in soup.find_all("table"):
                text = table.get_text(" ", strip=True).lower()
                if "ban" not in text and "mwpl" not in text:
                    continue
                symbols = []
                for cell in table.find_all("td"):
                    value = cell.get_text(" ", strip=True).upper()
                    if re.fullmatch(r"[A-Z][A-Z0-9&-]{1,14}", value):
                        symbols.append(value)
                # A visible but empty list is still a valid no-ban result.
                if symbols or any(term in text for term in ("no stock", "no security", "none")):
                    return sorted(set(symbols))
        except requests.RequestException as exc:
            logger.debug("F&O fallback unavailable at {}: {}", url, exc)
        return None

    def fetch_gift_nifty(self) -> ExternalMarketQuote | None:
        """Read the public NiftyTrader GIFT Nifty snapshot, never synthesize it."""
        try:
            response = requests.get(
                self.GIFT_NIFTY_URL,
                timeout=12,
                headers={"User-Agent": "Mozilla/5.0 (Market Sentinel)", "Accept-Language": "en-IN,en;q=0.9"},
            )
            response.raise_for_status()
            text = re.sub(r"<[^>]+>", " ", response.text)
            text = re.sub(r"\s+", " ", text)
            match = re.search(
                r"GIFT Nifty Futures.*?Latest public snapshot\s*([\d,]+(?:\.\d+)?)\s*([+-]?[\d,]+(?:\.\d+)?)\s*([+-]\d+(?:\.\d+)?)%",
                text,
                flags=re.IGNORECASE,
            )
            if not match:
                logger.warning("GIFT Nifty page did not expose a parseable snapshot")
                return None
            return ExternalMarketQuote(
                name="GIFT Nifty",
                value=float(match.group(1).replace(",", "")),
                percent_change=float(match.group(3)),
                source="NiftyTrader",
            )
        except (requests.RequestException, ValueError) as exc:
            logger.warning("GIFT Nifty quote unavailable: {}", exc)
            return None
