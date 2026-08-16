"""
news/deduplicator.py

Removes duplicate or near-duplicate NewsEvent objects.

The deduplicator is responsible for identifying articles that
represent the same underlying event and returning a unique list.

Author : Market Sentinel
Version: 1.0.0
"""

from __future__ import annotations

from typing import Iterable

from loguru import logger

from market_sentinel.news.models import NewsEvent


class NewsDeduplicator:
    """
    Removes duplicate news articles.

    Current implementation performs exact matching based on URL.
    Future versions will support fuzzy matching using titles,
    content similarity, and event clustering.
    """

    def process(
        self,
        events: Iterable[NewsEvent],
    ) -> list[NewsEvent]:
        """
        Remove duplicate news events.

        Parameters
        ----------
        events
            Iterable of NewsEvent objects.

        Returns
        -------
        list[NewsEvent]
            Unique news events.
        """

        unique_events: list[NewsEvent] = []
        seen_urls: set[str] = set()

        for event in events:

            url = event.url.strip()

            if not url:
                logger.debug("Skipping article with empty URL.")
                continue

            if url in seen_urls:
                logger.debug(f"Duplicate article ignored: {url}")
                continue

            seen_urls.add(url)
            unique_events.append(event)

        logger.info(
            f"Deduplicated {len(unique_events)} unique article(s)."
        )

        return unique_events