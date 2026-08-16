"""
providers/angelone/gainers.py

Top Price Gainers Provider.

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


class GainersProvider:

    def __init__(self):

        self.market = AngelOneMarketData()

    def fetch(
        self,
        expiry: str = "NEAR",
    ) -> list[dict]:

        logger.info(
            "Downloading Top Price Gainers..."
        )

        response = self.market.top_price_gainers(
            expiry=expiry,
        )

        if not response.get("status"):

            raise RuntimeError(response)

        gainers = response.get(
            "data",
            [],
        )

        logger.success(
            "Downloaded {} gainers.",
            len(gainers),
        )

        return AngelOneMapper.map_stocks(
            gainers,
        )