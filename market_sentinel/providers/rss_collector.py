"""
providers/rss_collector.py

Production-grade RSS / Atom collector.

Responsibilities:
    - Fetch RSS / Atom feeds concurrently
    - Parse feed entries
    - Normalize dates to UTC
    - Preserve missing publication dates as None
    - Normalize source names
    - Remove duplicate articles
    - Reject malformed entries
    - Provide deterministic output

Author : Market Sentinel
Version : 3.0.0
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from typing import Any, Iterable
from urllib.parse import urlparse

import feedparser
import requests
from loguru import logger

from market_sentinel.news.models import NewsArticle


class RSSCollector:
    """
    Collect articles from RSS / Atom feeds.
    """

    USER_AGENT = (
        "MarketSentinel/3.0 "
        "(Indian Market Intelligence Engine)"
    )

    REQUEST_TIMEOUT = 15
    MAX_WORKERS = 8

    def __init__(
        self,
        feeds: Iterable[str],
    ) -> None:
        self._feeds = list(
            dict.fromkeys(
                feed.strip()
                for feed in feeds
                if feed and feed.strip()
            )
        )

    # ==========================================================
    # PUBLIC
    # ==========================================================

    def collect(self) -> list[NewsArticle]:
        """
        Fetch all configured feeds and return unique articles.
        """

        logger.info(
            "Collecting {} RSS feeds...",
            len(self._feeds),
        )

        articles: list[NewsArticle] = []

        with ThreadPoolExecutor(
            max_workers=self.MAX_WORKERS,
        ) as executor:

            futures = {
                executor.submit(
                    self._collect_feed,
                    feed_url,
                ): feed_url
                for feed_url in self._feeds
            }

            for future in as_completed(futures):

                feed_url = futures[future]

                try:
                    result = future.result()
                    articles.extend(result)

                except Exception as exc:
                    logger.exception(
                        "RSS worker failed for {}: {}",
                        feed_url,
                        exc,
                    )

        articles = self._deduplicate(articles)

        # Deterministic ordering:
        # newest dated articles first, undated articles last.
        articles.sort(
            key=self._sort_key,
            reverse=True,
        )

        logger.info(
            "Collected {} unique article(s).",
            len(articles),
        )

        return articles

    # ==========================================================
    # FEED COLLECTION
    # ==========================================================

    def _collect_feed(
        self,
        url: str,
    ) -> list[NewsArticle]:
        """
        Download and parse one RSS / Atom feed.
        """

        logger.info(
            "Fetching RSS feed: {}",
            url,
        )

        try:

            response = requests.get(
                url,
                timeout=self.REQUEST_TIMEOUT,
                headers={
                    "User-Agent": self.USER_AGENT,
                    "Accept": (
                        "application/rss+xml, "
                        "application/atom+xml, "
                        "application/xml, "
                        "text/xml, "
                        "*/*"
                    ),
                },
            )

            response.raise_for_status()

            feed = feedparser.parse(
                response.content,
            )

            if getattr(
                feed,
                "bozo",
                False,
            ):
                logger.warning(
                    "Feed parser warning for {}: {}",
                    url,
                    getattr(
                        feed,
                        "bozo_exception",
                        "unknown parser error",
                    ),
                )

            return self._parse_feed(
                feed,
                source_url=url,
            )

        except requests.RequestException as exc:

            logger.error(
                "HTTP error while fetching {}: {}",
                url,
                exc,
            )

        except Exception as exc:

            logger.exception(
                "Failed to process RSS feed {}: {}",
                url,
                exc,
            )

        return []

    # ==========================================================
    # FEED PARSING
    # ==========================================================

    def _parse_feed(
        self,
        feed: Any,
        source_url: str,
    ) -> list[NewsArticle]:
        """
        Convert feed entries into NewsArticle objects.
        """

        articles: list[NewsArticle] = []

        source = self._resolve_source(
            feed=feed,
            source_url=source_url,
        )

        entries = getattr(
            feed,
            "entries",
            [],
        )

        logger.debug(
            "Feed {} contains {} entries.",
            source,
            len(entries),
        )

        for entry in entries:

            try:

                article = self._parse_entry(
                    entry=entry,
                    source=source,
                    source_url=source_url,
                )

                if article is not None:
                    articles.append(article)

            except Exception as exc:

                logger.warning(
                    "Skipping invalid RSS entry from {}: {}",
                    source,
                    exc,
                )

        return articles

    def _parse_entry(
        self,
        entry: Any,
        source: str,
        source_url: str,
    ) -> NewsArticle | None:
        """
        Convert one RSS / Atom entry.
        """

        title = self._clean_text(
            entry.get(
                "title",
                "",
            )
        )

        url = (
            entry.get(
                "link",
                "",
            )
            or ""
        ).strip()

        if not title or not url:
            return None

        summary = self._clean_text(
            entry.get(
                "summary",
                "",
            )
            or entry.get(
                "description",
                "",
            )
            or ""
        )

        published_at = self._parse_date(
            entry,
        )

        author = (
            entry.get(
                "author",
                "",
            )
            or ""
        ).strip()

        # Google News RSS carries the original publisher in entry.source. Use
        # it instead of labelling every article "Google News", so downstream
        # quality filters can reliably accept Reuters/BBC/etc. and reject
        # untrusted publishers.
        publisher = source
        entry_source = entry.get("source")
        if source == "Google News" and entry_source:
            try:
                publisher = self._normalize_source_name(
                    str(entry_source.get("title", "")).strip()
                ) or source
            except (AttributeError, TypeError):
                publisher = source

        return NewsArticle(
            title=title,
            summary=summary,
            source=publisher,
            url=url,
            published_at=published_at,
        )

    # ==========================================================
    # SOURCE NORMALIZATION
    # ==========================================================

    @classmethod
    def _resolve_source(
        cls,
        feed: Any,
        source_url: str,
    ) -> str:
        """
        Resolve a clean, stable source name.

        Feed titles are preferred, but known domains are
        normalized so ranking does not depend on long RSS
        feed titles.
        """

        hostname = (
            urlparse(source_url)
            .hostname
            or ""
        ).lower()

        # ------------------------------------------------------
        # Known Indian sources
        # ------------------------------------------------------

        if "economictimes.indiatimes.com" in hostname:
            return "Economic Times"

        if "timesofindia.indiatimes.com" in hostname:
            return "Times of India"

        if "business-standard.com" in hostname:
            return "Business Standard"

        if "moneycontrol.com" in hostname:
            return "Moneycontrol"

        if "sebi.gov.in" in hostname:
            return "SEBI"

        if "rbi.org.in" in hostname:
            return "RBI"

        if "nseindia.com" in hostname:
            return "NSE"

        if "bseindia.com" in hostname:
            return "BSE"

        # ------------------------------------------------------
        # Global sources
        # ------------------------------------------------------

        if "reuters.com" in hostname:
            return "Reuters"

        if "bbc.co.uk" in hostname or "bbc.com" in hostname:
            return "BBC News"

        if "news.google.com" in hostname:
            return "Google News"

        if "cnbc.com" in hostname:
            return "CNBC"

        if "finance.yahoo.com" in hostname:
            return "Yahoo Finance"

        if "marketwatch.com" in hostname:
            return "MarketWatch"

        if "investing.com" in hostname:
            return "Investing.com"

        # ------------------------------------------------------
        # Feed-provided title
        # ------------------------------------------------------

        feed_title = ""

        try:
            feed_title = (
                feed.feed.get(
                    "title",
                    "",
                )
                or ""
            ).strip()

        except Exception:
            pass

        if feed_title:
            return cls._normalize_source_name(
                feed_title,
            )

        return hostname or "RSS"

    @staticmethod
    def _normalize_source_name(
        source: str,
    ) -> str:
        """
        Normalize common RSS feed title variations.
        """

        value = " ".join(
            source.split()
        ).strip()

        lowered = value.lower()

        aliases = {
            "markets-economic times": "Economic Times",
            "economic times": "Economic Times",
            "business news today: stock markets, financial news, india business & world business news":
                "Times of India",
            "news": "News",
            "sebi rss feed": "SEBI",
            "rbi": "RBI",
        }

        for alias, normalized in aliases.items():

            if lowered == alias:
                return normalized

        return value or "RSS"

    # ==========================================================
    # DATE PARSING
    # ==========================================================

    @staticmethod
    def _parse_date(
        entry: Any,
    ) -> datetime | None:
        """
        Parse publication/update timestamp.

        IMPORTANT:
            Missing dates remain None.

        We deliberately do NOT replace a missing date with
        datetime.now(), because doing so would falsely make
        old/undated articles appear freshly published.
        """

        # ------------------------------------------------------
        # Standard RSS / Atom string fields
        # ------------------------------------------------------

        candidates = (
            entry.get("published"),
            entry.get("updated"),
            entry.get("created"),
            entry.get("pubDate"),
        )

        for value in candidates:

            if not value:
                continue

            parsed = RSSCollector._parse_datetime_value(
                value,
            )

            if parsed is not None:
                return parsed

        # ------------------------------------------------------
        # feedparser structured fields
        # ------------------------------------------------------

        structured_candidates = (
            entry.get("published_parsed"),
            entry.get("updated_parsed"),
            entry.get("created_parsed"),
        )

        for value in structured_candidates:

            if not value:
                continue

            try:

                timestamp = (
                    datetime(
                        value.tm_year,
                        value.tm_mon,
                        value.tm_mday,
                        value.tm_hour,
                        value.tm_min,
                        value.tm_sec,
                        tzinfo=timezone.utc,
                    )
                )

                return timestamp

            except Exception:
                continue

        logger.debug(
            "RSS entry has no valid publication date. "
            "Keeping published_at=None."
        )

        return None

    @staticmethod
    def _parse_datetime_value(
        value: Any,
    ) -> datetime | None:
        """
        Parse common RSS date representations.
        """

        if isinstance(
            value,
            datetime,
        ):

            return RSSCollector._to_utc(
                value,
            )

        if not isinstance(
            value,
            str,
        ):
            return None

        value = value.strip()

        if not value:
            return None

        # RFC 2822 / RSS dates
        try:

            return RSSCollector._to_utc(
                parsedate_to_datetime(
                    value,
                )
            )

        except Exception:
            pass

        # ISO-8601 dates
        try:

            normalized = value.replace(
                "Z",
                "+00:00",
            )

            return RSSCollector._to_utc(
                datetime.fromisoformat(
                    normalized,
                )
            )

        except Exception:
            pass

        return None

    @staticmethod
    def _to_utc(
        value: datetime,
    ) -> datetime:
        """
        Normalize datetime to timezone-aware UTC.
        """

        if value.tzinfo is None:

            value = value.replace(
                tzinfo=timezone.utc,
            )

        return value.astimezone(
            timezone.utc,
        )

    # ==========================================================
    # TEXT CLEANING
    # ==========================================================

    @staticmethod
    def _clean_text(
        value: Any,
    ) -> str:
        """
        Clean HTML entities and excessive whitespace.
        """

        if value is None:
            return ""

        text = str(value)

        text = unescape(
            text,
        )

        # Remove basic HTML tags.
        text = RSSCollector._strip_html(
            text,
        )

        return " ".join(
            text.split()
        ).strip()

    @staticmethod
    def _strip_html(
        text: str,
    ) -> str:
        """
        Remove basic HTML markup.
        """

        import re

        return re.sub(
            r"<[^>]+>",
            " ",
            text,
        )

    # ==========================================================
    # DEDUPLICATION
    # ==========================================================

    @classmethod
    def _deduplicate(
        cls,
        articles: list[NewsArticle],
    ) -> list[NewsArticle]:
        """
        Remove duplicate articles.

        Primary key:
            normalized URL

        Secondary key:
            normalized title

        Preference:
            Keep the article with the best available
            publication timestamp and longer summary.
        """

        by_url: dict[str, NewsArticle] = {}
        by_title: dict[str, NewsArticle] = {}

        for article in articles:

            if not article.url:
                continue

            url_key = cls._normalize_url(
                article.url,
            )

            title_key = cls._normalize_title(
                article.title,
            )

            # ----------------------------------------------
            # URL duplicate
            # ----------------------------------------------

            if url_key in by_url:

                existing = by_url[url_key]

                by_url[url_key] = cls._prefer_article(
                    existing,
                    article,
                )

                continue

            by_url[url_key] = article

            # ----------------------------------------------
            # Title duplicate
            # ----------------------------------------------

            if title_key:

                if title_key in by_title:

                    existing = by_title[title_key]

                    preferred = cls._prefer_article(
                        existing,
                        article,
                    )

                    by_title[title_key] = preferred

                    # Keep URL map consistent.
                    by_url[
                        cls._normalize_url(
                            preferred.url,
                        )
                    ] = preferred

                else:

                    by_title[
                        title_key
                    ] = article

        # Rebuild final list from URL map.
        unique = {}

        for article in by_url.values():

            unique[
                cls._normalize_url(
                    article.url,
                )
            ] = article

        return list(
            unique.values()
        )

    @staticmethod
    def _prefer_article(
        first: NewsArticle,
        second: NewsArticle,
    ) -> NewsArticle:
        """
        Select the better duplicate representation.
        """

        # Prefer dated article.
        if (
            first.published_at is None
            and second.published_at is not None
        ):
            return second

        if (
            first.published_at is not None
            and second.published_at is None
        ):
            return first

        # Prefer longer summary.
        if len(
            second.summary or ""
        ) > len(
            first.summary or ""
        ):
            return second

        return first

    @staticmethod
    def _normalize_url(
        url: str,
    ) -> str:
        """
        Normalize URL for duplicate detection.
        """

        value = (
            url or ""
        ).strip().lower()

        if not value:
            return ""

        # Remove common tracking parameters.
        import re

        value = re.sub(
            r"[?&](utm_[^=&]+|fbclid|gclid)=[^&]*",
            "",
            value,
        )

        return value.rstrip(
            "/"
        )

    @staticmethod
    def _normalize_title(
        title: str,
    ) -> str:
        """
        Normalize title for duplicate detection.
        """

        import re

        value = (
            title or ""
        ).lower()

        value = re.sub(
            r"[^a-z0-9\s]",
            " ",
            value,
        )

        return " ".join(
            value.split()
        ).strip()

    # ==========================================================
    # SORTING
    # ==========================================================

    @staticmethod
    def _sort_key(
        article: NewsArticle,
    ) -> tuple[int, float]:
        """
        Sort dated articles first.

        Undated articles are deliberately placed last.
        """

        if article.published_at is None:
            return (
                0,
                0.0,
            )

        return (
            1,
            article.published_at.timestamp(),
        )
