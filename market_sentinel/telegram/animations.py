"""
market_sentinel/telegram/animations.py

Animated Telegram sticker support for Market Wavez.

This module is intentionally separate from the MorningFormatter.

Supported:
    - Animated .tgs stickers
    - Static/video stickers supported by Telegram
    - Telegram sticker file_ids

Author : Market Wavez
Version: 1.0.0
"""

from __future__ import annotations

from pathlib import Path

from market_sentinel.utils.logger import logger


class TelegramAnimations:
    """
    Handles animated Telegram stickers.

    The actual sticker can be supplied in two ways:

    1. Local .tgs file
    2. Telegram file_id

    File IDs are preferred for GitHub Actions because they avoid
    storing binary sticker files inside the repository.
    """

    # ==========================================================
    # Sticker names
    # ==========================================================

    ALERT = "alert"
    BIG_MOVE = "big_move"
    BREAKOUT = "breakout"
    BULLISH = "bullish"
    BEARISH = "bearish"
    VOLATILITY = "volatility"

    # ==========================================================
    # Constructor
    # ==========================================================

    def __init__(self, bot):
        self.bot = bot

    # ==========================================================
    # Send sticker
    # ==========================================================

    async def send(
        self,
        sticker: str | Path,
    ) -> None:
        """
        Send an animated Telegram sticker.

        Parameters
        ----------
        sticker:
            Either:
                - Telegram file_id
                - Local .tgs/.webm/.webp sticker path
        """

        try:

            await self.bot.send_sticker(
                sticker
            )

            logger.success(
                "Telegram animated sticker sent successfully."
            )

        except Exception as ex:

            logger.exception(
                f"Failed to send Telegram animated sticker: {ex}"
            )

            raise

    # ==========================================================
    # Send from file
    # ==========================================================

    async def send_file(
        self,
        file_path: str | Path,
    ) -> None:
        """
        Send an animated sticker from a local file.
        """

        path = Path(file_path)

        if not path.exists():

            raise FileNotFoundError(
                f"Telegram sticker not found: {path}"
            )

        await self.send(path)

    # ==========================================================
    # Send by Telegram file_id
    # ==========================================================

    async def send_file_id(
        self,
        file_id: str,
    ) -> None:
        """
        Send an already uploaded Telegram sticker.

        This is the recommended method for GitHub Actions.
        """

        if not file_id:

            raise ValueError(
                "Telegram sticker file_id is empty."
            )

        await self.send(file_id)