"""
config/news_sources.py

Central configuration for all Market Sentinel news sources.

Each news source is defined once here and reused by providers.

Author : Market Sentinel
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RSSFeed:
    """
    Represents a single RSS feed.
    """

    name: str
    url: str
    category: str
    country: str = "India"
    enabled: bool = True


# =============================================================================
# RBI
# =============================================================================

RBI_PRESS_RELEASES = RSSFeed(
    name="RBI Press Releases",
    url="https://rbi.org.in/pressreleases_rss.xml",
    category="PRESS_RELEASE",
)

RBI_NOTIFICATIONS = RSSFeed(
    name="RBI Notifications",
    url="https://rbi.org.in/notifications_rss.xml",
    category="NOTIFICATION",
)

RBI_SPEECHES = RSSFeed(
    name="RBI Speeches",
    url="https://rbi.org.in/speeches_rss.xml",
    category="SPEECH",
)

RBI_TENDERS = RSSFeed(
    name="RBI Tenders",
    url="https://rbi.org.in/tenders_rss.xml",
    category="TENDER",
)

RBI_PUBLICATIONS = RSSFeed(
    name="RBI Publications",
    url="https://rbi.org.in/Publication_rss.xml",
    category="PUBLICATION",
)