"""
market_data.py

Market Data wrapper.

Author : Market Sentinel
Version : 2.0.0
"""

from __future__ import annotations

from loguru import logger

from market_sentinel.providers.angelone.client import (
    AngelOneClient,
)


class AngelOneMarketData:

    def __init__(self):

        self.client = AngelOneClient()

    def full(
        self,
        tokens: dict,
    ):

        logger.info(
            "Downloading FULL market snapshot..."
        )

        return self.client.api.getMarketData(
            mode="FULL",
            exchangeTokens=tokens,
        )

    def ohlc(
        self,
        tokens: dict,
    ):

        return self.client.api.getMarketData(
            mode="OHLC",
            exchangeTokens=tokens,
        )

    def ltp(
        self,
        tokens: dict,
    ):

        return self.client.api.getMarketData(
            mode="LTP",
            exchangeTokens=tokens,
        )

    # ======================================================
    # Top Price Gainers
    # ======================================================

    def top_price_gainers(
            self,
            expiry: str = "NEAR",
    ):
        logger.info(
            "Downloading Top Price Gainers..."
        )

        return self.client.api.gainersLosers(
            {
                "datatype": "PercPriceGainers",
                "expirytype": expiry,
            }
        )

    # ======================================================
    # Top Price Losers
    # ======================================================

    def top_price_losers(
            self,
            expiry: str = "NEAR",
    ):
        logger.info(
            "Downloading Top Price Losers..."
        )

        return self.client.api.gainersLosers(
            {
                "datatype": "PercPriceLosers",
                "expirytype": expiry,
            }
        )