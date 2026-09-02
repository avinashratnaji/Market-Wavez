"""Resilient global, commodity, crypto, and Indian ADR market snapshots."""

from __future__ import annotations

from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
from urllib.parse import quote

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
    CRYPTO = {
        "Bitcoin": "BTC-USD", "Ethereum": "ETH-USD",
        "Solana": "SOL-USD", "XRP": "XRP-USD",
        "BNB": "BNB-USD", "Dogecoin": "DOGE-USD",
        "Cardano": "ADA-USD", "Chainlink": "LINK-USD",
    }
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
            symbols = list(self.GLOBAL.values()) + list(self.ADRS.values()) + list(self.CRYPTO.values()) + list(self.COMMODITIES.values()) + [self.FX, self.GOLD, self.SILVER]
            data = self._yahoo_charts(symbols)
            quote = lambda name, symbol, unit="", note="": self._chart_quote(data, name, symbol, unit, note)
            global_indices = self._present(quote(name, symbol) for name, symbol in self.GLOBAL.items())
            adrs = self._present(quote(name, symbol) for name, symbol in self.ADRS.items())
            crypto = self._present(quote(name, symbol, "$") for name, symbol in self.CRYPTO.items())
            commodities = self._present(quote(name, symbol, "$", "Higher crude can pressure India") for name, symbol in self.COMMODITIES.items())
            inr = data.get(self.FX, (None, None))[0]
            gold = data.get(self.GOLD, (None, None))[0]
            silver = data.get(self.SILVER, (None, None))[0]
            # Jewellery-market rates must not be labelled as an Indian price
            # when they are only a COMEX USD quote converted to INR.
            commodities[0:0] = self._fetch_indian_bullion()
            if inr and gold:
                commodities.append(ExternalMarketQuote(
                    "Gold (COMEX INR equiv.)", gold * inr / 31.1035 * 10,
                    data.get(self.GOLD, (None, None))[1] or 0.0, "₹/10g", "International futures converted to INR",
                ))
            if inr and silver:
                commodities.append(ExternalMarketQuote(
                    "Silver (COMEX INR equiv.)", silver * inr / 31.1035 * 1000,
                    data.get(self.SILVER, (None, None))[1] or 0.0, "₹/kg", "International futures converted to INR",
                ))
            return global_indices, adrs, commodities, crypto
        except Exception as exc:
            logger.warning("Global market snapshot unavailable: {}", exc)
            return [], [], [], []

    @classmethod
    def _yahoo_charts(cls, symbols: list[str]) -> dict[str, tuple[float | None, float | None]]:
        """Fetch stateless Yahoo daily bars without yfinance's local cache."""
        results: dict[str, tuple[float | None, float | None]] = {}
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = {executor.submit(cls._one_yahoo_chart, symbol): symbol for symbol in symbols}
            for future in as_completed(futures):
                symbol = futures[future]
                try:
                    results[symbol] = future.result()
                except Exception as exc:
                    logger.warning("Yahoo quote unavailable for {}: {}", symbol, exc)
                    results[symbol] = (None, None)
        return results

    @staticmethod
    def _one_yahoo_chart(symbol: str) -> tuple[float | None, float | None]:
        response = requests.get(
            f"https://query1.finance.yahoo.com/v8/finance/chart/{quote(symbol, safe='')}",
            params={"range": "5d", "interval": "1d"},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=12,
        )
        response.raise_for_status()
        result = (response.json().get("chart") or {}).get("result") or []
        rows = ((result[0].get("indicators") or {}).get("quote") or []) if result else []
        closes = [float(value) for value in (rows[0].get("close", []) if rows else []) if value is not None]
        if len(closes) < 2 or closes[-2] == 0:
            return None, None
        return closes[-1], (closes[-1] / closes[-2] - 1) * 100

    @staticmethod
    def _chart_quote(data, name: str, symbol: str, unit: str = "", note: str = "") -> ExternalMarketQuote | None:
        value, percent = data.get(symbol, (None, None))
        if value is None or percent is None:
            return None
        return ExternalMarketQuote(name, value, percent, unit, note)

    @staticmethod
    def _clean_text(html: str) -> str:
        return BeautifulSoup(html, "html.parser").get_text(" ", strip=True).replace("\xa0", " ")

    @classmethod
    def _parse_indian_gold(
        cls,
        html: str,
    ) -> ExternalMarketQuote | None:
        """
        Parse the current India 24K gold retail rate
        from the Goodreturns gold-rate page.
        """

        text = cls._clean_text(html)

        # Goodreturns currently exposes:
        #
        # 24K Gold /g ₹15,513
        #
        # The daily change is not always present next
        # to this value, so only the price is mandatory.
        match = re.search(
            r"24K\s*Gold\s*/\s*g"
            r".{0,50}?"
            r"₹\s*([\d,]+)",
            text,
            re.I | re.S,
        )

        if not match:
            logger.warning(
                "Unable to parse India 24K gold rate "
                "from Goodreturns."
            )
            return None

        per_gram = float(
            match.group(1).replace(",", "")
        )

        # --------------------------------------------------
        # DAILY CHANGE
        # --------------------------------------------------

        # Try to find a +/- movement immediately following
        # the current 24K price. This is optional because
        # Goodreturns may omit/rearrange it.
        price_end = match.end()

        nearby_text = text[
            price_end:
            price_end + 100
        ]

        change_match = re.search(
            r"([+-])\s*([\d,]+)",
            nearby_text,
        )

        percent = 0.0

        if change_match:

            change = float(
                change_match.group(2).replace(",", "")
            )

            if change_match.group(1) == "-":
                change = -change

            previous = per_gram - change

            if previous:
                percent = (
                    change / previous
                ) * 100

        value_10g = per_gram * 10

        logger.success(
            "Parsed India 24K Gold: "
            "₹{:,.0f}/10g ({:+.2f}%)",
            value_10g,
            percent,
        )

        return ExternalMarketQuote(
            "Gold 24K INDIA",
            value_10g,
            percent,
            "₹/10g",
            "India retail rate; Goodreturns",
        )

    @classmethod
    def _fetch_indian_bullion(cls) -> list[ExternalMarketQuote]:
        """
        Fetch India retail bullion rates from Goodreturns.

        Includes diagnostics so GitHub Actions logs show whether
        the source page is being fetched correctly.
        """

        results: list[ExternalMarketQuote] = []

        # ==========================================================
        # GOLD
        # ==========================================================

        try:
            gold_response = requests.get(
                cls.INDIA_GOLD_URL,
                headers=cls.REQUEST_HEADERS,
                timeout=10,
            )

            gold_response.raise_for_status()

            logger.info(
                "Gold response status={} url={} length={}",
                gold_response.status_code,
                gold_response.url,
                len(gold_response.text),
            )

            gold_text = cls._clean_text(
                gold_response.text
            )

            contains_24k = "24K" in gold_text.upper()

            logger.info(
                "Contains 24K Gold data: {}",
                contains_24k,
            )

            gold_position = gold_text.upper().find("24K")

            if gold_position >= 0:

                sample = gold_text[
                         gold_position:
                         gold_position + 350
                         ]

                logger.info(
                    "Gold parsed sample: {}",
                    sample,
                )

            else:

                logger.warning(
                    "24K Gold text NOT FOUND in Goodreturns response."
                )

                logger.warning(
                    "Gold response sample: {}",
                    gold_text[:500],
                )

            gold = cls._parse_indian_gold(
                gold_response.text
            )

            if gold is not None:

                logger.success(
                    "Indian Gold fetched successfully: "
                    "{} = ₹{:,.0f} ({:+.2f}%)",
                    gold.name,
                    gold.value,
                    gold.percent_change,
                )

                results.append(
                    gold
                )

            else:

                logger.warning(
                    "Indian Gold parser returned no result."
                )

        except requests.RequestException as exc:

            logger.warning(
                "Indian Gold source unavailable: {}",
                exc,
            )

        except Exception as exc:

            logger.warning(
                "Unexpected error while fetching Indian Gold: {}",
                exc,
            )

        # ==========================================================
        # SILVER
        # ==========================================================

        try:
            silver_response = requests.get(
                cls.INDIA_SILVER_URL,
                headers=cls.REQUEST_HEADERS,
                timeout=10,
            )

            silver_response.raise_for_status()

            logger.info(
                "Silver response status={} url={} length={}",
                silver_response.status_code,
                silver_response.url,
                len(silver_response.text),
            )

            silver = cls._parse_indian_silver(
                silver_response.text
            )

            if silver is not None:

                logger.success(
                    "Indian Silver fetched successfully: "
                    "{} = ₹{:,.0f} ({:+.2f}%)",
                    silver.name,
                    silver.value,
                    silver.percent_change,
                )

                results.append(
                    silver
                )

            else:

                logger.warning(
                    "Indian Silver parser returned no result."
                )

        except requests.RequestException as exc:

            logger.warning(
                "Indian Silver source unavailable: {}",
                exc,
            )

        except Exception as exc:

            logger.warning(
                "Unexpected error while fetching Indian Silver: {}",
                exc,
            )

        # ==========================================================
        # RESULT
        # ==========================================================

        logger.info(
            "Indian bullion quotes collected: {}",
            len(results),
        )

        for quote in results:
            logger.info(
                "Bullion quote -> {} | value={} | change={:+.2f}%",
                quote.name,
                quote.value,
                quote.percent_change,
            )

        return results

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
