"""
news/models.py

News models.

Author : Market Sentinel
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from market_sentinel.news.enums import (
    NewsCategory,
    NewsImportance,
)


@dataclass(slots=True)
class NewsArticle:

    title: str

    summary: str

    source: str

    url: str

    published_at: datetime | None = None

    impact: int = 0

    sentiment: str = "Neutral"

    sectors: list[str] | None = None

    symbols: list[str] | None = None

    duplicate: bool = False

    category: NewsCategory = NewsCategory.GENERAL

    importance: int = 0

    entities: list[str] = field(
        default_factory=list
    )

    score: int = 0

    normalized_score: int = 0


@dataclass(slots=True)
class NewsEvent:
    """
    Raw news event collected from external providers.

    RSS providers populate this model before the event
    enters classification, relevance, scoring and
    Telegram formatting.
    """

    title: str

    source: str

    url: str

    published_at: datetime | None = None

    category: str = "GENERAL"

    subcategory: str = "RSS"

    summary: str = ""

    content: str = ""

    author: str = ""

    language: str = "en"

    tags: list[str] = field(
        default_factory=list
    )

    provider: str = "RSS"

    provider_id: str = ""

    # ------------------------------------------------------
    # Optional enrichment fields
    # ------------------------------------------------------

    impact: int = 0

    sentiment: str = "Neutral"

    sectors: list[str] = field(
        default_factory=list
    )

    symbols: list[str] = field(
        default_factory=list
    )

    entities: list[str] = field(
        default_factory=list
    )

    importance: int = 0

    score: int = 0

    normalized_score: int = 0

    duplicate: bool = False