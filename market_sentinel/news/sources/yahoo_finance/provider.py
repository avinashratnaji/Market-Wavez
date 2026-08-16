"""
Yahoo Finance News Provider.

Author : Market Sentinel
"""

from __future__ import annotations

from market_sentinel.news.rss_provider import (
    RSSProvider,
)


class YahooFinanceProvider(RSSProvider):

    SOURCE = "Yahoo Finance"

    RSS_URL = "https://finance.yahoo.com/news/rssindex"