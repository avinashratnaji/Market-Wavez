"""
news/parser.py

Normalizes raw provider data into NewsEvent objects.

Each provider (Reuters, RBI, Bloomberg, etc.) may expose
different field names. This parser converts them into the
common NewsEvent model used throughout Market Sentinel.

Author : Market Sentinel
Version: 1.0.0
"""

from __future__ import annotations
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Any
from email.utils import parsedate_to_datetime

from market_sentinel.news.models import NewsEvent


class NewsParser:
    """
    Converts raw provider data into NewsEvent objects.
    """

    def parse(
            self,
            *,
            provider: str,
            raw: dict[str, Any],
    ) -> NewsEvent:
        """
        Parse normalized provider data into a NewsEvent.
        """

        return NewsEvent(
            title=raw.get("title", ""),
            source=provider,
            url=raw.get("url", ""),
            published_at=self._parse_datetime(
                raw.get("published_at")
            ),
            summary=self.clean_html(
                raw.get("summary", "")
            ),
            content=self.clean_html(
                raw.get("content", "")
            ),
            author=raw.get("author", ""),
            language=raw.get("language", "en"),
            category=raw.get("category", ""),
            subcategory=raw.get("subcategory", ""),
            tags=raw.get("tags", []),
            provider=provider,
            provider_id=raw.get("provider_id", ""),
        )

    @staticmethod
    def clean_html(text: str) -> str:
        if not text:
            return ""

        return BeautifulSoup(text, "html.parser").get_text(" ", strip=True)

    @staticmethod
    def _parse_datetime(value: Any) -> datetime | None:
        """
        Convert provider datetime into datetime object.

        Supports datetime objects and ISO-8601 strings.
        """

        if value is None:
            return None

        if isinstance(value, datetime):
            return value

        if isinstance(value, str):
            try:
                return parsedate_to_datetime(value)
            except Exception:
                return None

        return None