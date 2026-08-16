"""
news/rss_provider.py

Reusable RSS provider.

Author : Market Sentinel
"""

from __future__ import annotations

from abc import ABC
from datetime import datetime

import feedparser

from market_sentinel.news.models import NewsArticle
from market_sentinel.news.provider import NewsProvider


class RSSProvider(
    NewsProvider,
    ABC,
):

    RSS_URL: str = ""

    SOURCE: str = ""

    def fetch(
        self,
    ) -> list[NewsArticle]:

        feed = feedparser.parse(
            self.RSS_URL,
        )

        articles: list[NewsArticle] = []

        for entry in feed.entries:

            articles.append(

                NewsArticle(

                    title=entry.get(
                        "title",
                        "",
                    ),

                    summary=entry.get(
                        "summary",
                        "",
                    ),

                    source=self.SOURCE,

                    url=entry.get(
                        "link",
                        "",
                    ),

                    published_at=datetime.now(),

                )

            )

        return articles