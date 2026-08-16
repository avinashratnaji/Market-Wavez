"""
news/postgres_repository.py

PostgreSQL implementation of the NewsRepository.

Responsible for persisting and retrieving NewsEvent objects.

Author : Market Sentinel
Version: 1.0.0
"""

from __future__ import annotations

from datetime import datetime, timedelta

from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import Session

from market_sentinel.news.models import NewsEvent
from market_sentinel.news.models_db import NewsArticle
from market_sentinel.news.repository import NewsRepository


class PostgresNewsRepository(NewsRepository):
    """
    PostgreSQL implementation of NewsRepository.
    """

    def __init__(
        self,
        session: Session,
    ) -> None:
        self._session = session

    def exists_by_url(
        self,
        url: str,
    ) -> bool:

        statement = (
            select(NewsArticle.id)
            .where(NewsArticle.url == url)
            .limit(1)
        )

        return self._session.execute(statement).scalar_one_or_none() is not None

    def save(
        self,
        event: NewsEvent,
    ) -> None:

        article = self._to_db(event)

        self._session.add(article)
        self._session.commit()

        logger.debug(
            "Saved article: {}",
            event.title,
        )

    def save_all(
        self,
        events: list[NewsEvent],
    ) -> None:

        articles = [
            self._to_db(event)
            for event in events
            if not self.exists_by_url(event.url)
        ]

        if not articles:
            logger.info("No new articles to save.")
            return

        self._session.add_all(articles)
        self._session.commit()

        logger.info(
            "Saved {} article(s).",
            len(articles),
        )

    def recent(
        self,
        limit: int = 100,
    ) -> list[NewsEvent]:

        statement = (
            select(NewsArticle)
            .order_by(NewsArticle.published_at.desc())
            .limit(limit)
        )

        articles = self._session.scalars(statement).all()

        return [
            self._to_domain(article)
            for article in articles
        ]

    def delete_older_than(
        self,
        days: int,
    ) -> int:

        cutoff = datetime.utcnow() - timedelta(days=days)

        statement = (
            select(NewsArticle)
            .where(NewsArticle.published_at < cutoff)
        )

        articles = self._session.scalars(statement).all()

        count = len(articles)

        for article in articles:
            self._session.delete(article)

        self._session.commit()

        logger.info(
            "Deleted {} old article(s).",
            count,
        )

        return count

    @staticmethod
    def _to_db(
        event: NewsEvent,
    ) -> NewsArticle:

        return NewsArticle(
            provider=event.provider,
            provider_id=event.provider_id,
            source=event.source,
            url=event.url,
            title=event.title,
            summary=event.summary,
            content=event.content,
            author=event.author,
            language=event.language,
            category=event.category,
            subcategory=event.subcategory,
            published_at=event.published_at,
        )

    @staticmethod
    def _to_domain(
        article: NewsArticle,
    ) -> NewsEvent:

        return NewsEvent(
            title=article.title,
            source=article.source,
            url=article.url,
            published_at=article.published_at,
            summary=article.summary,
            content=article.content,
            author=article.author,
            language=article.language,
            category=article.category,
            subcategory=article.subcategory,
            tags=[],
            provider=article.provider,
            provider_id=article.provider_id,
        )