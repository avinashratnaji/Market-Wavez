"""
providers/angelone/sectors.py

Downloads Indian sector indices from Angel One.

Author : Market Sentinel
Version : 1.0.0
"""

from __future__ import annotations

from loguru import logger

from market_sentinel.providers.angelone.constants import (
    SECTOR_INDICES,
)

from market_sentinel.providers.angelone.market_data import (
    AngelOneMarketData,
)

from market_sentinel.providers.angelone.mapper import (
    AngelOneMapper,
)

from market_sentinel.providers.angelone.models import (
    IndexSnapshot,
)

from market_sentinel.providers.angelone.token_registry import (
    TokenRegistry,
)


class SectorProvider:
    """
    Downloads all configured sector indices.
    """

    def __init__(self):

        self.market = AngelOneMarketData()

        self.registry = TokenRegistry()

    def fetch(self) -> list[IndexSnapshot]:

        logger.info(
            "Downloading sector indices..."
        )

        exchange_tokens: dict[str, list[str]] = {}

        # -----------------------------------------------------
        # Resolve sector names -> tokens
        # -----------------------------------------------------

        for symbol in SECTOR_INDICES:

            instrument = self.registry.find(
                exchange="NSE",
                symbol=symbol,
            )

            if instrument is None:

                logger.warning(
                    "Sector not found: {}",
                    symbol,
                )

                continue

            exchange_tokens.setdefault(
                instrument.exchange,
                [],
            ).append(
                instrument.token,
            )

        if not exchange_tokens:

            logger.warning(
                "No sector indices found."
            )

            return []

        # -----------------------------------------------------
        # Download market data
        # -----------------------------------------------------

        response = self.market.full(
            exchange_tokens,
        )

        if not response.get("status"):

            raise RuntimeError(
                f"Angel One Error : {response}"
            )

        fetched = (
            response
            .get("data", {})
            .get("fetched", [])
        )

        logger.success(
            "Downloaded {} sector indices.",
            len(fetched),
        )

        return AngelOneMapper.map_indices(
            fetched,
        )