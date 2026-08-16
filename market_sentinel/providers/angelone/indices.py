"""
providers/angelone/indices.py

Downloads all configured Indian indices from Angel One.

Author : Market Sentinel
Version : 2.0.0
"""

from __future__ import annotations

from loguru import logger

from market_sentinel.providers.angelone.constants import (
    INDIAN_INDICES,
)
from market_sentinel.providers.angelone.mapper import (
    AngelOneMapper,
)
from market_sentinel.providers.angelone.market_data import (
    AngelOneMarketData,
)
from market_sentinel.providers.angelone.models import (
    IndexSnapshot,
)
from market_sentinel.providers.angelone.token_registry import (
    TokenRegistry,
)


class IndianIndicesProvider:
    """
    Downloads all configured Indian indices from Angel One.
    """

    def __init__(self) -> None:

        self.market = AngelOneMarketData()

        self.registry = TokenRegistry()

    def fetch(self) -> list[IndexSnapshot]:

        logger.info(
            "Downloading Indian indices..."
        )

        exchange_tokens: dict[str, list[str]] = {}

        # -----------------------------------------------------
        # Resolve names -> tokens
        # -----------------------------------------------------

        for symbol in INDIAN_INDICES:

            instrument = self.registry.find(
                exchange="NSE",
                symbol=symbol,
            )

            if instrument is None:

                logger.warning(
                    "Instrument not found: {}",
                    symbol,
                )

                continue

            exchange_tokens.setdefault(
                instrument.exchange,
                [],
            ).append(
                instrument.token,
            )

        logger.info(
            "Fetching {} exchange(s).",
            len(exchange_tokens),
        )

        if not exchange_tokens:

            logger.warning(
                "No valid instruments found."
            )

            return []

        # -----------------------------------------------------
        # Download Market Data
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
            "Downloaded {} indices.",
            len(fetched),
        )

        indices = AngelOneMapper.map_indices(
            fetched,
        )

        DISPLAY_ORDER = [
            "NIFTY",
            "SENSEX",
            "BANKNIFTY",
            "FINNIFTY",
            "NIFTY MIDCAP 50",
            "NIFTY SMALLCAP 100",
            "NIFTY IT",
            "NIFTY PHARMA",
            "GIFT NIFTY",
            "INDIA VIX",
        ]

        order = {
            name.upper(): i
            for i, name in enumerate(DISPLAY_ORDER)
        }

        indices.sort(
            key=lambda item: order.get(
                item.name.upper(),
                999,
            )
        )

        return indices