"""
news/engine.py

Orchestrates the complete news ingestion pipeline.

Author : Market Sentinel
Version: 1.3.0
"""

from __future__ import annotations

from loguru import logger

from market_sentinel.news.aggregator import NewsAggregator
from market_sentinel.news.classifier import NewsClassifier
from market_sentinel.news.deduplicator import NewsDeduplicator
from market_sentinel.news.models import NewsEvent
from market_sentinel.news.provider_registry import register_providers
from market_sentinel.news.relevance_filter import NewsRelevanceFilter
from market_sentinel.news.repository import NewsRepository
from market_sentinel.news.scoring_engine import NewsScoringEngine
from market_sentinel.news.summary_builder import SummaryBuilder


class NewsEngine:
    """
    Orchestrates the complete news ingestion pipeline.
    """

    def __init__(
        self,
        repository: NewsRepository,
    ) -> None:

        self._repository = repository

        self._aggregator = NewsAggregator()
        register_providers(self._aggregator)

        self._deduplicator = NewsDeduplicator()
        self._classifier = NewsClassifier()
        self._scoring_engine = NewsScoringEngine()
        self._relevance_filter = NewsRelevanceFilter()
        self._summary_builder = SummaryBuilder()

    def run(self) -> list[NewsEvent]:

        logger.info("Starting News Engine")

        # ---------------------------------------------------------
        # Collect
        # ---------------------------------------------------------

        events = self._aggregator.fetch()

        logger.info(
            "Collected {} article(s).",
            len(events),
        )

        # ---------------------------------------------------------
        # Deduplicate
        # ---------------------------------------------------------

        events = self._deduplicator.process(events)

        logger.info(
            "{} article(s) after deduplication.",
            len(events),
        )

        # ---------------------------------------------------------
        # Classify
        # ---------------------------------------------------------

        events = self._classifier.process(events)

        logger.info(
            "News classification completed."
        )

        # ---------------------------------------------------------
        # Score Articles
        # ---------------------------------------------------------

        for event in events:
            event.score = self._scoring_engine.score(event)

        logger.info(
            "Assigned relevance scores to {} article(s).",
            len(events),
        )

        # Highest score first
        events.sort(
            key=lambda event: getattr(event, "score", 0),
            reverse=True,
        )

        # ---------------------------------------------------------
        # Relevance Filter
        # ---------------------------------------------------------

        events = self._relevance_filter.process(events)

        logger.info(
            "{} article(s) after relevance filtering.",
            len(events),
        )

        # ---------------------------------------------------------
        # Build Clean Summaries
        # ---------------------------------------------------------

        for event in events:
            event.summary = self._summary_builder.build(event)

        logger.info(
            "Built summaries for {} article(s).",
            len(events),
        )

        # ---------------------------------------------------------
        # Persist Only New Articles
        # ---------------------------------------------------------

        new_events: list[NewsEvent] = []

        for event in events:

            if self._repository.exists_by_url(event.url):
                logger.debug(
                    "Skipping duplicate article: {}",
                    event.title,
                )
                continue

            self._repository.save(event)
            new_events.append(event)

        logger.info(
            "{} new article(s) stored.",
            len(new_events),
        )

        logger.info(
            "News Engine completed successfully."
        )

        return new_events