"""
news/provider_registry.py

Registers all news providers used by Market Sentinel.

Author : Market Sentinel
Version: 1.0.0
"""

from __future__ import annotations

from market_sentinel.news.aggregator import NewsAggregator
from market_sentinel.news.sources.rbi.press_releases import (
    RBIPressReleaseProvider,
)
from market_sentinel.news.sources.yahoo_finance import (
    YahooFinanceProvider,
)


def register_providers(
    aggregator: NewsAggregator,
) -> None:
    """
    Register all enabled news providers.

    Parameters
    ----------
    aggregator : NewsAggregator
        News aggregator instance.
    """

    # ==========================================================================
    # Important News
    # ==========================================================================

    aggregator.register(YahooFinanceProvider())
    #aggregator.register(MoneycontrolProvider())
    #aggregator.register(ReutersProvider())

    aggregator.register(
        RBIPressReleaseProvider()
    )

    # ==========================================================================
    # SEBI
    # ==========================================================================

    # aggregator.register(SEBIProvider())

    # ==========================================================================
    # NSE
    # ==========================================================================

    # aggregator.register(NSEProvider())

    # ==========================================================================
    # BSE
    # ==========================================================================

    # aggregator.register(BSEProvider())

    # ==========================================================================
    # Reuters
    # ==========================================================================

    # aggregator.register(ReutersProvider())

    # ==========================================================================
    # Bloomberg
    # ==========================================================================

    # aggregator.register(BloombergProvider())