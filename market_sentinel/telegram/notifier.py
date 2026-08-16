"""
telegram/notifier.py

Sends notifications through Telegram.

Author : Market Sentinel
Version : 2.3.0
"""

from __future__ import annotations

import asyncio

from market_sentinel.telegram.bot import TelegramBot
from market_sentinel.utils.logger import logger


class TelegramNotifier:
    """
    Sends Telegram notifications.

    All Telegram operations for one notification batch
    run inside the same asyncio event loop.
    """

    def __init__(self):

        self.bot = TelegramBot()

    # ======================================================
    # ASYNC
    # ======================================================

    async def _send_brief_async(
        self,
        messages: list[str],
        sticker_id: str | None = None,
    ) -> None:
        """
        Send the complete Morning Brief using one event loop.

        Order:

            Message 1
            Sticker
            Message 2
            Message 3
            ...
        """

        # --------------------------------------------------
        # STICKER
        # --------------------------------------------------

        if sticker_id:

            await self.bot.send_sticker(
                sticker_id
            )

        # --------------------------------------------------
        # MESSAGE 1
        # --------------------------------------------------

        if messages:
            await self.bot.send_message(
                messages[0]
            )

        # --------------------------------------------------
        # REMAINING MESSAGES
        # --------------------------------------------------

        for message in messages[1:]:

            await self.bot.send_message(
                message
            )

    async def _notify_all_async(
        self,
        messages: list[str],
    ) -> None:

        for message in messages:

            await self.bot.send_message(
                message
            )

    async def _notify_async(
        self,
        message: str,
    ) -> None:

        await self.bot.send_message(
            message
        )

    # ======================================================
    # PUBLIC API
    # ======================================================

    def send_brief(
        self,
        messages: list[str],
        sticker_id: str | None = None,
    ) -> None:
        """
        Send the complete Morning Brief.

        Everything happens inside ONE event loop.
        """

        if not messages and not sticker_id:

            logger.info(
                "Nothing to send."
            )

            return

        try:

            asyncio.run(
                self._send_brief_async(
                    messages=messages,
                    sticker_id=sticker_id,
                )
            )

            logger.success(
                "Complete Telegram brief sent successfully."
            )

        except Exception as ex:

            logger.exception(
                f"Failed to send Telegram brief: {ex}"
            )

            raise

    def notify(
        self,
        message: str,
    ) -> None:
        """
        Send a single Telegram message.
        """

        try:

            asyncio.run(
                self._notify_async(
                    message
                )
            )

            logger.success(
                "Telegram notification sent."
            )

        except Exception as ex:

            logger.exception(
                f"Failed to send Telegram message: {ex}"
            )

            raise

    def notify_all(
        self,
        messages: list[str],
    ) -> None:
        """
        Send multiple Telegram messages.
        """

        if not messages:

            logger.info(
                "No Telegram messages to send."
            )

            return

        try:

            asyncio.run(
                self._notify_all_async(
                    messages
                )
            )

            logger.success(
                "All Telegram notifications sent."
            )

        except Exception as ex:

            logger.exception(
                f"Failed to send Telegram messages: {ex}"
            )

            raise