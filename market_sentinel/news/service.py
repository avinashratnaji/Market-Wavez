"""
news/service.py

Business service for news operations.

Coordinates business logic between the News Engine
and the persistence layer.

Author : Market Sentinel
Version: 2.0.0
"""

from __future__ import annotations

from loguru import logger

from market_sentinel.news.intelligence import NewsIntelligenceEngine
from market_sentinel.news.models import (
    NewsEvent,
    NewsIntelligence,
)
from market_sentinel.news.repository import NewsRepository


class NewsService:
    """
    Business service for NewsEvent operations.
    """

    def __init__(
        self,
        repository: NewsRepository,
    ) -> None:

        self._repository = repository
        self._engine = NewsIntelligenceEngine()

    # ==========================================================
    # INGEST
    # ==========================================================

    def ingest(
        self,
        events: list[NewsEvent],
    ) -> list[NewsIntelligence]:
        """
        Save only new articles and return enriched news.
        """

        intelligence: list[NewsIntelligence] = []

        inserted = 0
        skipped = 0

        for event in events:

            if self._repository.exists_by_url(event.url):
                skipped += 1
                continue

            self._repository.save(event)

            intelligence.append(
                self._engine.analyze(event)
            )

            inserted += 1

        logger.info(
            "News ingestion completed. Inserted={}, Skipped={}",
            inserted,
            skipped,
        )

        return intelligence

    # ==========================================================
    # SAVE
    # ==========================================================

    def save_new_articles(
        self,
        events: list[NewsEvent],
    ) -> list[NewsEvent]:
        """
        Backward-compatible API.
        """

        new_events: list[NewsEvent] = []

        for event in events:

            if self._repository.exists_by_url(event.url):
                continue

            self._repository.save(event)

            new_events.append(event)

        logger.info(
            "Inserted {} new article(s).",
            len(new_events),
        )

        return new_events

    # ==========================================================
    # QUERY
    # ==========================================================

    def recent(
        self,
        limit: int = 100,
    ) -> list[NewsEvent]:
        """
        Return recent news articles.
        """

        return self._repository.recent(limit)

    def recent_intelligence(
        self,
        limit: int = 100,
    ) -> list[NewsIntelligence]:
        """
        Return enriched recent news.
        """

        return [
            self._engine.analyze(article)
            for article in self._repository.recent(limit)
        ]

    # ==========================================================
    # MAINTENANCE
    # ==========================================================

    def cleanup(
        self,
        days: int = 365,
    ) -> int:
        """
        Delete archived articles.
        """

        deleted = self._repository.delete_older_than(days)

        logger.info(
            "Deleted {} archived article(s).",
            deleted,
        )

        return deleted