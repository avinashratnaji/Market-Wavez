"""
Telegram Service

Responsible for sending the latest market summary.
"""

from market_sentinel.telegram.summary_builder import SummaryBuilder
from market_sentinel.telegram.formatter import BroadcastFormatter
from market_sentinel.telegram.notifier import TelegramNotifier
from market_sentinel.utils.logger import logger


class TelegramService:

    def __init__(self):
        self.summary_builder = SummaryBuilder()
        self.notifier = TelegramNotifier()

    def send_market_summary(self):

        logger.info("Building market summary...")

        summary = self.summary_builder.build()

        message = BroadcastFormatter.format(summary)

        logger.info("Sending Telegram message...")

        self.notifier.notify(message)

        logger.success("Telegram summary sent.")