"""
news/summary_builder.py

Builds the Top Market Moving News list.

Author : Market Sentinel
"""

from __future__ import annotations

from market_sentinel.news.models import NewsArticle


class NewsSummaryBuilder:

    @staticmethod
    def build(
        articles: list[NewsArticle],
        limit: int = 10,
    ) -> list[NewsArticle]:

        seen = set()

        summary = []

        for article in articles:

            key = article.title.lower().strip()

            if key in seen:
                continue

            seen.add(key)

            summary.append(article)

            if len(summary) >= limit:
                break

        return summary