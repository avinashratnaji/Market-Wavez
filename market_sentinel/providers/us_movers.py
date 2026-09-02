"""Live US equity gainers and losers from Yahoo Finance's public screener."""

from __future__ import annotations

import requests
from loguru import logger

from market_sentinel.briefs.models import ExternalMarketQuote


class UsMarketMoversProvider:
    """Return the leading regular-session US movers without estimating prices."""

    URL = "https://query1.finance.yahoo.com/v1/finance/screener/predefined/saved"
    HEADERS = {"User-Agent": "Mozilla/5.0 (Market Sentinel)", "Accept": "application/json"}

    def fetch(self, direction: str, limit: int = 5) -> list[ExternalMarketQuote]:
        screen = "day_gainers" if direction == "gainers" else "day_losers"
        try:
            response = requests.get(
                self.URL,
                params={"scrIds": screen, "count": limit, "start": 0},
                headers=self.HEADERS,
                timeout=12,
            )
            response.raise_for_status()
            rows = response.json().get("finance", {}).get("result", [{}])[0].get("quotes", [])
            output = []
            for row in rows:
                price = row.get("regularMarketPrice")
                change = row.get("regularMarketChangePercent")
                symbol = str(row.get("symbol") or "").strip()
                if price is None or change is None or not symbol:
                    continue
                output.append(ExternalMarketQuote(
                    name=symbol,
                    value=float(price),
                    percent_change=float(change),
                    unit="$",
                    note=str(row.get("longName") or row.get("shortName") or "").strip(),
                    source="Yahoo Finance",
                ))
            return output[:limit]
        except (requests.RequestException, ValueError, TypeError, IndexError) as exc:
            logger.warning("US {} unavailable: {}", direction, exc)
            return []
