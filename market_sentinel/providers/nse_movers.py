"""Official-NSE cash-equity movers with an Angel One fallback."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import requests
from loguru import logger

from market_sentinel.providers.angelone.models import StockSnapshot


class NseMoversProvider:
    """Use NSE's NIFTY 500 variations for cash-market gainers and losers."""

    URL = "https://www.nseindia.com/api/live-analysis-variations?index=NIFTY%20500"

    def fetch(self, direction: str, limit: int = 10) -> list[StockSnapshot]:
        try:
            session = requests.Session()
            session.headers.update({"User-Agent": "Mozilla/5.0", "Accept": "application/json", "Referer": "https://www.nseindia.com/market-data/live-equity-market"})
            session.get("https://www.nseindia.com", timeout=10)
            response = session.get(self.URL, timeout=12)
            response.raise_for_status()
            payload = response.json()
            rows = payload.get("data", []) if isinstance(payload, dict) else []
            snapshots = [item for row in rows if (item := self._snapshot(row)) is not None]
            snapshots.sort(key=lambda item: item.percent_change, reverse=direction == "gainers")
            filtered = [item for item in snapshots if item.percent_change > 0] if direction == "gainers" else [item for item in snapshots if item.percent_change < 0]
            return filtered[:limit]
        except Exception as exc:
            logger.warning("NSE {} unavailable: {}", direction, exc)
            return []

    @staticmethod
    def _number(row: dict[str, Any], *keys: str) -> float | None:
        for key in keys:
            value = row.get(key)
            if value not in (None, ""):
                try:
                    return float(str(value).replace(",", ""))
                except ValueError:
                    continue
        return None

    @classmethod
    def _snapshot(cls, row: dict[str, Any]) -> StockSnapshot | None:
        price = cls._number(row, "ltP", "lastPrice", "last")
        percent = cls._number(row, "pChange", "perChange", "percentChange")
        if not row.get("symbol") or price is None or percent is None:
            return None
        previous = price / (1 + percent / 100) if percent != -100 else price
        return StockSnapshot(
            name=str(row["symbol"]), exchange="NSE", token=str(row.get("identifier", "")),
            value=price, change=price - previous, percent_change=percent,
            open=cls._number(row, "open") or 0, high=cls._number(row, "dayHigh", "high") or 0,
            low=cls._number(row, "dayLow", "low") or 0, close=previous,
            volume=cls._number(row, "totalTradedVolume", "volume") or 0, updated_at=datetime.now(),
        )
