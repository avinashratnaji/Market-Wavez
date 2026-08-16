"""
providers/newsapi_collector.py

Production NewsAPI Collector.

Fetches news from NewsAPI-compatible providers and converts
responses into NewsEvent objects.

Author : Market Sentinel
Version : 1.0.0
"""

from __future__ import annotations

from datetime import datetime

import requests
from loguru import logger

from market_sentinel.news.models import NewsEvent


class NewsAPICollector:
    """
    Collect news using NewsAPI.
    """

    BASE_URL = "https://newsapi.org/v2/top-headlines"

    REQUEST_TIMEOUT = 15

    USER_AGENT = (
        "MarketSentinel/1.0 "
        "(https://marketsentinel.local)"
    )

    def __init__(
        self,
        api_key: str,
        country: str = "in",
        category: str = "business",
        language: str = "en",
    ) -> None:

        self.api_key = api_key
        self.country = country
        self.category = category
        self.language = language

    # ==========================================================
    # PUBLIC
    # ==========================================================

    def collect(self) -> list[NewsEvent]:
        """
        Fetch latest news.
        """

        logger.info(
            "Collecting news from NewsAPI..."
        )

        try:

            response = requests.get(
                self.BASE_URL,
                headers={
                    "User-Agent": self.USER_AGENT,
                },
                params={
                    "apiKey": self.api_key,
                    "country": self.country,
                    "category": self.category,
                    "language": self.language,
                    "pageSize": 100,
                },
                timeout=self.REQUEST_TIMEOUT,
            )

            response.raise_for_status()

            payload = response.json()

            if payload.get("status") != "ok":

                logger.error(
                    "NewsAPI returned error: {}",
                    payload,
                )

                return []

            articles = []

            for item in payload.get(
                "articles",
                [],
            ):

                articles.append(
                    self._to_event(item)
                )

            logger.info(
                "Collected {} article(s).",
                len(articles),
            )

            return articles

        except Exception as exc:

            logger.exception(
                "NewsAPI collection failed: {}",
                exc,
            )

            return []

    # ==========================================================
    # INTERNAL
    # ==========================================================

    def _to_event(
        self,
        article: dict,
    ) -> NewsEvent:

        published = article.get(
            "publishedAt",
            "",
        )

        try:

            published_at = datetime.fromisoformat(
                published.replace(
                    "Z",
                    "+00:00",
                )
            )

        except Exception:

            published_at = datetime.utcnow()

        source = article.get(
            "source",
            {},
        ).get(
            "name",
            "NewsAPI",
        )

        return NewsEvent(
            title=article.get(
                "title",
                "",
            ),
            source=source,
            url=article.get(
                "url",
                "",
            ),
            published_at=published_at,
            category="GENERAL",
            subcategory="NEWSAPI",
            summary=article.get(
                "description",
                "",
            )
            or "",
            content=article.get(
                "content",
                "",
            )
            or "",
            author=article.get(
                "author",
                "",
            )
            or "",
            language=self.language,
            tags=[],
            provider="NewsAPI",
            provider_id=article.get(
                "url",
                "",
            ),
        )