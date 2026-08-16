"""
services/news_telegram_service.py

Sends newly collected news articles to Telegram.

Author : Market Sentinel
Version : 1.1.0
"""

from __future__ import annotations

from loguru import logger

from market_sentinel.database.session import SessionLocal
from market_sentinel.news.engine import NewsEngine
from market_sentinel.news.postgres_repository import PostgresNewsRepository
from market_sentinel.telegram.news_formatter import NewsFormatter
from market_sentinel.telegram.notifier import TelegramNotifier


# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------

MAX_TELEGRAM_ALERTS = 5


class NewsTelegramService:

    def __init__(self) -> None:
        self.notifier = TelegramNotifier()

    def run(self) -> None:

        logger.info("Starting News Telegram Service")

        session = SessionLocal()

        try:

            repository = PostgresNewsRepository(session)
            engine = NewsEngine(repository)

            new_events = engine.run()

            if not new_events:
                logger.info("No new articles to send.")
                return

            logger.info(
                "{} new article(s) available.",
                len(new_events),
            )

            # ------------------------------------------------------------------
            # Send only highest priority alerts
            # ------------------------------------------------------------------

            events = sorted(
                new_events,
                key=lambda event: getattr(event, "score", 0),
                reverse=True,
            )[:MAX_TELEGRAM_ALERTS]

            logger.info(
                "Sending {} of {} article(s) to Telegram.",
                len(events),
                len(new_events),
            )

            messages = [
                NewsFormatter.format(event)
                for event in events
            ]

            self.notifier.notify_all(messages)

            logger.success(
                "Telegram notifications sent successfully."
            )

        except Exception:
            logger.exception(
                "News Telegram Service failed."
            )

        finally:
            session.close()