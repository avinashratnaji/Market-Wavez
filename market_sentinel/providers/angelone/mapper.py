"""
providers/angelone/mapper.py

Converts Angel One API responses into Market Sentinel models.

Author : Market Sentinel
Version : 2.0.0
"""

from __future__ import annotations

from datetime import datetime

from market_sentinel.providers.angelone.models import (
    IndexSnapshot,
    StockSnapshot,
)
import re


class AngelOneMapper:
    """
    Maps Angel One JSON responses into strongly typed
    Market Sentinel models.
    """

    # ---------------------------------------------------------
    # Index Mapper
    # ---------------------------------------------------------

    @staticmethod
    def map_index(raw: dict) -> IndexSnapshot:

        return IndexSnapshot(

            name=raw.get("tradingSymbol", ""),

            exchange=raw.get("exchange", ""),

            token=str(raw.get("symbolToken", "")),

            value=float(raw.get("ltp", 0)),

            change=float(raw.get("netChange", 0)),

            percent_change=float(raw.get("percentChange", 0)),

            open=float(raw.get("open", 0)),

            high=float(raw.get("high", 0)),

            low=float(raw.get("low", 0)),

            close=float(raw.get("close", 0)),

            volume=float(raw.get("tradeVolume", 0)),

            updated_at=datetime.now(),

        )

    # ---------------------------------------------------------
    # Multiple Indices
    # ---------------------------------------------------------

    @classmethod
    def map_indices(
        cls,
        records: list[dict],
    ) -> list[IndexSnapshot]:

        return [
            cls.map_index(record)
            for record in records
        ]

    # ---------------------------------------------------------
    # Multiple Stocks
    # ---------------------------------------------------------

    @staticmethod
    def map_stock(raw: dict) -> StockSnapshot:
        symbol = raw.get(
            "tradingSymbol",
            "",
        )

        symbol = re.sub(
            r"\d{2}[A-Z]{3}\d{2}(FUT|CE|PE)$",
            "",
            symbol,
        )

        return StockSnapshot(

            name=symbol,

            exchange=raw.get(
                "exchange",
                "NFO",
            ),

            token=str(
                raw.get(
                    "symbolToken",
                    "",
                )
            ),

            value=float(
                raw.get(
                    "ltp",
                    0,
                )
            ),

            change=float(
                raw.get(
                    "netChange",
                    0,
                )
            ),

            percent_change=float(
                raw.get(
                    "percentChange",
                    0,
                )
            ),

            open=0.0,

            high=0.0,

            low=0.0,

            close=0.0,

            volume=0.0,

            updated_at=datetime.now(),
        )

    @classmethod
    def map_stocks(
            cls,
            records: list[dict],
    ) -> list[StockSnapshot]:
        return [
            cls.map_stock(record)
            for record in records
        ]

