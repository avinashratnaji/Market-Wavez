"""
providers/angelone/losers.py

Top Price Losers Provider.

Author : Market Sentinel
Version : 1.0.0
"""

from __future__ import annotations

from loguru import logger
from market_sentinel.providers.angelone.mapper import (
    AngelOneMapper,
)
from market_sentinel.providers.angelone.market_data import (
    AngelOneMarketData,
)


class LosersProvider:

    def __init__(self):

        self.market = AngelOneMarketData()

    def fetch(
        self,
        expiry: str = "NEAR",
    ) -> list[dict]:

        logger.info(
            "Downloading Top Price Losers..."
        )

        response = self.market.top_price_losers(
            expiry=expiry,
        )

        if not response.get("status"):

            raise RuntimeError(response)

        losers = response.get(
            "data",
            [],
        )

        logger.success(
            "Downloaded {} losers.",
            len(losers),
        )

        return AngelOneMapper.map_stocks(
            losers,
        )