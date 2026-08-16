"""
news/scoring_engine.py

Calculates a final ranking score for every news article.

Author : Market Sentinel
"""

from __future__ import annotations

from datetime import datetime, timezone

from market_sentinel.news.enums import (
    NewsCategory,
)

from market_sentinel.news.models import (
    NewsArticle,
)


class NewsScoringEngine:

    CATEGORY_BONUS = {

        NewsCategory.EARNINGS: 25,

        NewsCategory.MERGER: 24,

        NewsCategory.ACQUISITION: 24,

        NewsCategory.CAPEX: 22,

        NewsCategory.DEBT: 20,

        NewsCategory.REGULATION: 20,

        NewsCategory.GEOPOLITICS: 18,

        NewsCategory.MACRO: 18,

        NewsCategory.COMPETITION: 17,

        NewsCategory.PRODUCT: 16,

        NewsCategory.COMMODITIES: 15,

        NewsCategory.ANALYST: 8,

        NewsCategory.TECHNICAL: 5,

        NewsCategory.PERSONAL_FINANCE: -40,

        NewsCategory.GENERAL: 0,

    }

    SOURCE_BONUS = {

        "Reuters": 10,

        "Bloomberg": 10,

        "SEBI": 10,

        "RBI": 10,

        "Economic Times": 8,

        "Moneycontrol": 8,

        "Yahoo Finance": 5,

    }

    @classmethod
    def score(
        cls,
        articles: list[NewsArticle],
    ) -> list[NewsArticle]:

        now = datetime.now(timezone.utc)

        for article in articles:

            score = article.importance

            # ----------------------------------------
            # Category
            # ----------------------------------------

            score += cls.CATEGORY_BONUS.get(
                article.category,
                0,
            )

            # ----------------------------------------
            # Entities
            # ----------------------------------------

            score += min(
                len(article.entities) * 2,
                10,
            )

            # ----------------------------------------
            # Source
            # ----------------------------------------

            score += cls.SOURCE_BONUS.get(
                article.source,
                0,
            )

            # ----------------------------------------
            # Freshness
            # ----------------------------------------

            if article.published_at:

                try:

                    published = article.published_at

                    if published.tzinfo is None:
                        published = published.replace(tzinfo=timezone.utc)

                    age = (
                                  now - published
                          ).total_seconds() / 3600

                    if age <= 1:
                        score += 10
                    elif age <= 6:
                        score += 7
                    elif age <= 24:
                        score += 5
                    elif age <= 72:
                        score += 2

                except Exception:
                    pass

            article.score = min(
                score,
                100,
            )

        articles = [

            article

            for article in articles

            if article.score >= 50

        ]

        articles = [

            article

            for article in articles

            if article.score >= 50

        ]

        articles = [

            article

            for article in articles

            if article.score >= 50

        ]

        articles = [

            article

            for article in articles

            if article.score >= 50

        ]

        articles.sort(

            key=lambda x: x.score,

            reverse=True,

        )

        return articles