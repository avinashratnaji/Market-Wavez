"""
telegram/telegram_service.py

Telegram service for Market Sentinel.

Author : Market Sentinel
Version : 2.0.0
"""

from market_sentinel.telegram.summary_builder import SummaryBuilder
from market_sentinel.telegram.formatter import BroadcastFormatter
from market_sentinel.telegram.notifier import TelegramNotifier
from market_sentinel.utils.logger import logger


class TelegramService:
    """
    High level Telegram service.
    """

    def __init__(self):
        self.summary_builder = SummaryBuilder()
        self.notifier = TelegramNotifier()

    def send_market_summary(self) -> None:
        """
        Build the latest market summary and send it to Telegram.
        """

        logger.info("Building market summary...")

        summary = self.summary_builder.build()

        logger.info(
            "Market summary built successfully (%d assets).",
            summary.total_assets,
        )

        message = BroadcastFormatter.morning(summary)

        logger.info("Sending Telegram notification...")

        self.notifier.notify(message)

        logger.success("Market summary sent successfully.")