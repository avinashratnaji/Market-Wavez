"""Official-NSE cash-equity movers with an Angel One fallback."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import requests
from loguru import logger

from market_sentinel.providers.angelone.models import StockSnapshot


class NseMoversProvider:
    """Merge NSE top movers, volume spurts and most-active cash equities."""

    URL = "https://www.nseindia.com/api/live-analysis-variations"
    VOLUME_URL = "https://www.nseindia.com/api/live-analysis-volume-gainers"
    ACTIVE_URL = "https://www.nseindia.com/api/live-analysis-most-active-securities"

    def fetch(self, direction: str, limit: int = 10) -> list[StockSnapshot]:
        try:
            session = requests.Session()
            session.headers.update({"User-Agent": "Mozilla/5.0", "Accept": "application/json", "Referer": "https://www.nseindia.com/market-data/live-equity-market"})
            session.get("https://www.nseindia.com", timeout=10)
            response = session.get(
                self.URL,
                # NSE intentionally spells this route value ``loosers``.
                params={"index": "loosers" if direction == "losers" else "gainers", "type": "allSec", "key": "allSec"},
                timeout=12,
            )
            response.raise_for_status()
            payload = response.json()
            rows = payload.get("data", []) if isinstance(payload, dict) and isinstance(payload.get("data"), list) else []
            # Add high relative-volume and high absolute-volume names. This
            # expands discovery beyond the 20 largest percentage movers while
            # keeping every input on a current official NSE feed.
            for url, params in ((self.VOLUME_URL, None), (self.ACTIVE_URL, {"index": "volume"})):
                try:
                    extra_response = session.get(url, params=params, timeout=12)
                    extra_response.raise_for_status()
                    extra_payload = extra_response.json()
                    if isinstance(extra_payload, dict) and isinstance(extra_payload.get("data"), list):
                        rows.extend(extra_payload["data"])
                except Exception as exc:
                    logger.debug("Supplemental NSE discovery feed unavailable: {}", exc)
            # NSE may include metadata strings alongside quote mappings.  One
            # malformed entry must not make the whole movers panel fall back.
            snapshots = [
                item for row in rows
                if isinstance(row, dict) and (item := self._snapshot(row)) is not None
            ]
            # A constituent can be present in both NSE feeds. Preserve one
            # current quote per symbol before ranking.
            snapshots = list({item.name: item for item in snapshots}.values())
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
        series = str(row.get("series") or "EQ").upper()
        if series != "EQ":
            return None
        price = cls._number(row, "ltP", "ltp", "lastPrice", "last")
        percent = cls._number(row, "pChange", "perChange", "percentChange", "net_price")
        if not row.get("symbol") or price is None or percent is None:
            return None
        previous = price / (1 + percent / 100) if percent != -100 else price
        meta = row.get("meta") if isinstance(row.get("meta"), dict) else {}
        company_name = str(
            row.get("companyName") or row.get("company") or meta.get("companyName") or ""
        ).strip()
        return StockSnapshot(
            name=str(row["symbol"]), exchange="NSE", token=str(row.get("identifier", "")),
            value=price, change=price - previous, percent_change=percent,
            open=cls._number(row, "open", "open_price") or 0,
            high=cls._number(row, "dayHigh", "high", "high_price") or 0,
            low=cls._number(row, "dayLow", "low", "low_price") or 0,
            close=cls._number(row, "prev_price") or previous,
            volume=cls._number(row, "totalTradedVolume", "quantityTraded", "volume", "trade_quantity") or 0,
            updated_at=datetime.now(),
            company_name=company_name,
        )
