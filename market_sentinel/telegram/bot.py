"""
telegram/bot.py

Low-level Telegram Bot wrapper.

Responsible only for communicating with Telegram.

Author : Market Sentinel
Version : 2.1.0
"""

from telegram import Bot
from telegram.constants import ParseMode
from telegram.error import TelegramError

from market_sentinel.config.settings import settings
from market_sentinel.utils.logger import logger


class TelegramBot:
    """
    Low-level Telegram Bot wrapper.
    """

    def __init__(self):

        if not settings.TELEGRAM_BOT_TOKEN:
            raise ValueError(
                "Telegram token is missing. Set TELEGRAM_BOT_TOKEN in .env."
            )

        if not settings.TELEGRAM_CHAT_ID:
            raise ValueError(
                "Telegram chat ID is missing. Set TELEGRAM_CHAT_ID in .env."
            )

        self.bot = Bot(
            token=settings.TELEGRAM_BOT_TOKEN
        )

        self.chat_id = settings.TELEGRAM_CHAT_ID

    async def send_message(
        self,
        message: str,
    ) -> None:
        """
        Send an HTML formatted Telegram message.
        """

        try:

            for chunk in self._message_chunks(message):
                await self.bot.send_message(
                    chat_id=self.chat_id,
                    text=chunk,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True,
                )

            logger.success(
                "Telegram message sent successfully."
            )

        except TelegramError as ex:

            logger.exception(
                f"Telegram Error: {ex}"
            )

            raise

    async def send_sticker(
        self,
        sticker_id: str,
    ) -> None:
        """
        Send an animated Telegram sticker.
        """

        try:

            await self.bot.send_sticker(
                chat_id=self.chat_id,
                sticker=sticker_id,
            )

            logger.success(
                "Telegram sticker sent successfully."
            )

        except TelegramError as ex:

            logger.exception(
                f"Telegram Sticker Error: {ex}"
            )

            raise

    async def send_photo(self, photo_path: str) -> None:
        """Send a generated briefing card before detailed text panels."""
        try:
            with open(photo_path, "rb") as photo:
                await self.bot.send_photo(chat_id=self.chat_id, photo=photo)
            logger.success("Telegram briefing card sent successfully.")
        except (OSError, TelegramError) as ex:
            logger.exception(f"Telegram photo error: {ex}")
            raise

    @staticmethod
    def _message_chunks(message: str, limit: int = 3900) -> list[str]:
        """Split long brief sections on line boundaries below Telegram's cap."""
        if len(message) <= limit:
            return [message]
        chunks: list[str] = []
        current = ""
        for line in message.splitlines(keepends=True):
            if current and len(current) + len(line) > limit:
                chunks.append(current.rstrip())
                current = ""
            # A single summary line is deliberately capped by the formatter;
            # this fallback protects custom callers as well.
            if len(line) > limit:
                line = line[:limit]
            current += line
        if current.strip():
            chunks.append(current.rstrip())
        return chunks or [message[:limit]]
