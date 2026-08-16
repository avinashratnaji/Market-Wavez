"""
news/sources/rbi/press_releases.py

RBI Press Releases RSS provider.

Author : Market Sentinel
Version: 1.0.0
"""

from __future__ import annotations

from market_sentinel.config.news_sources import RBI_PRESS_RELEASES
from market_sentinel.news.rss_provider import RSSNewsProvider


class RBIPressReleaseProvider(RSSNewsProvider):
    """
    RBI Press Releases RSS provider.
    """

    @property
    def name(self) -> str:
        return RBI_PRESS_RELEASES.name

    @property
    def rss_url(self) -> str:
        return RBI_PRESS_RELEASES.url