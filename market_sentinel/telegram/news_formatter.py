"""
telegram/news_formatter.py

Formats news alerts for Telegram.

Author : Market Sentinel
Version : 1.0.0
"""

from __future__ import annotations

from market_sentinel.news.models import NewsArticle


class NewsFormatter:

    @staticmethod
    def format(event: NewsArticle) -> str:

        lines = []

        lines.append("📰 <b>BREAKING NEWS</b>")
        lines.append("")
        lines.append(f"<b>{event.title}</b>")

        if getattr(event, "source", None):
            lines.append(f"🏛 Source : {event.source}")

        if getattr(event, "published_at", None):
            lines.append(f"🕒 {event.published_at}")

        if getattr(event, "summary", None):
            lines.append("")
            lines.append(event.summary)

        if getattr(event, "url", None):
            lines.append("")
            lines.append(event.url)

        return "\n".join(lines)