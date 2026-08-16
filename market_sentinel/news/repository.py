"""
news/repository.py

Repository abstraction for news articles.

Defines the persistence contract for NewsEvent objects.
Concrete implementations (e.g. PostgreSQL) are responsible
for storing and retrieving articles.

Author : Market Sentinel
Version: 1.0.0
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from market_sentinel.news.models import NewsEvent


class NewsRepository(ABC):
    """
    Abstract repository for news articles.
    """

    @abstractmethod
    def exists_by_url(
        self,
        url: str,
    ) -> bool:
        """
        Return True if an article with the given URL already exists.
        """
        raise NotImplementedError

    @abstractmethod
    def save(
        self,
        event: NewsEvent,
    ) -> None:
        """
        Persist a single news article.
        """
        raise NotImplementedError

    @abstractmethod
    def save_all(
        self,
        events: list[NewsEvent],
    ) -> None:
        """
        Persist multiple news articles.
        """
        raise NotImplementedError

    @abstractmethod
    def recent(
        self,
        limit: int = 100,
    ) -> list[NewsEvent]:
        """
        Return the most recent news articles.
        """
        raise NotImplementedError

    @abstractmethod
    def delete_older_than(
        self,
        days: int,
    ) -> int:
        """
        Delete articles older than the specified number of days.

        Returns
        -------
        int
            Number of deleted articles.
        """
        raise NotImplementedError