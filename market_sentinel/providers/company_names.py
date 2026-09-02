"""Attach readable company names to exchange tickers used in mover panels."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import quote

import requests


class CompanyNameProvider:
    def enrich(self, stocks: list) -> None:
        missing = [stock for stock in stocks if not getattr(stock, "company_name", "")]
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = {executor.submit(self._name, stock.name): stock for stock in missing}
            for future in as_completed(futures):
                try:
                    futures[future].company_name = future.result()
                except Exception:
                    continue

    @staticmethod
    def _name(symbol: str) -> str:
        clean = str(symbol).replace("-EQ", "").strip()
        response = requests.get(
            f"https://query1.finance.yahoo.com/v8/finance/chart/{quote(clean + '.NS', safe='')}",
            params={"range": "1d", "interval": "1d"},
            headers={"User-Agent": "Mozilla/5.0"}, timeout=8,
        )
        response.raise_for_status()
        result = response.json().get("chart", {}).get("result") or []
        meta = result[0].get("meta", {}) if result else {}
        return str(meta.get("longName") or meta.get("shortName") or "").strip()
