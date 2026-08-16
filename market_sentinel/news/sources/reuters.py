"""
Reuters RSS Provider.

Author : Market Sentinel
"""

from __future__ import annotations

from market_sentinel.news.rss_provider import (
    RSSProvider,
)


class ReutersProvider(
    RSSProvider,
):

    SOURCE = "Reuters"

    RSS_URL = (
        "https://feeds.reuters.com/reuters/businessNews"
    )