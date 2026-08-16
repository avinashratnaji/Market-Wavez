"""
news/aggregator.py

Collects news from all providers.

Author : Market Sentinel
"""

from __future__ import annotations

from market_sentinel.news.classifier import (
    NewsClassifier,
)
from market_sentinel.news.importance import (
    NewsImportanceScorer,
)
from market_sentinel.news.models import (
    NewsArticle,
)
from market_sentinel.news.provider import (
    NewsProvider,
)
from market_sentinel.news.entity_extractor import (
    EntityExtractor,
)

class NewsAggregator:

    def __init__(
        self,
        providers: list[NewsProvider],
    ) -> None:

        self.providers = providers

        self.scorer = NewsImportanceScorer()

    def fetch(
        self,
    ) -> list[NewsArticle]:

        articles: list[NewsArticle] = []

        # -------------------------------------------------
        # Collect
        # -------------------------------------------------

        for provider in self.providers:

            try:

                articles.extend(
                    provider.fetch()
                )

            except Exception as ex:

                print(
                    f"{provider.__class__.__name__}: {ex}"
                )

        # -------------------------------------------------
        # Classify
        # -------------------------------------------------

        articles = NewsClassifier.classify(
            articles,
        )

        articles = EntityExtractor.extract(
            articles,
        )

        # -------------------------------------------------
        # Score
        # -------------------------------------------------

        for article in articles:

            self.scorer.score(
                article,
            )

        # -------------------------------------------------
        # Rank
        # -------------------------------------------------

        articles.sort(

            key=lambda x: x.importance,

            reverse=True,

        )

        return articles