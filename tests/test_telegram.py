"""
tests/test_telegram.py

Telegram integration tests for Market Wavez.

Tests:
    1. Morning Brief
    2. Animated Telegram Sticker

Author : Market Wavez
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from market_sentinel.services.morning_brief_service import (
    MorningBriefService,
)

from market_sentinel.telegram.bot import (
    TelegramBot,
)


# ==========================================================
# CONFIGURATION
# ==========================================================

STICKER_FILE = Path(
    "data/telegram_stickers/alert.tgs"
)


# ==========================================================
# TEST 1
# MORNING BRIEF
# ==========================================================

def test_morning_brief():

    print()
    print("=" * 60)
    print("TEST 1 : MORNING BRIEF")
    print("=" * 60)
    print()

    MorningBriefService().send()

    print()
    print("Morning Brief sent successfully.")
    print()


# ==========================================================
# TEST 2
# ANIMATED STICKER
# ==========================================================

def test_animated_sticker():

    print()
    print("=" * 60)
    print("TEST 2 : ANIMATED TELEGRAM STICKER")
    print("=" * 60)
    print()

    print(
        f"Sticker path: {STICKER_FILE}"
    )

    # ------------------------------------------------------
    # Check sticker file
    # ------------------------------------------------------

    if not STICKER_FILE.exists():

        raise FileNotFoundError(
            f"""
Animated sticker not found.

Expected file:
{STICKER_FILE}

Create:

data/
└── telegram_stickers/
    └── alert.tgs
"""
        )

    # ------------------------------------------------------
    # Async operation
    # ------------------------------------------------------

    async def send_sticker():

        bot = TelegramBot()

        print(
            "Sending animated sticker..."
        )

        result = await bot.bot.send_sticker(
            chat_id=bot.chat_id,
            sticker=STICKER_FILE.open("rb"),
        )

        return result

    # ------------------------------------------------------
    # Execute async Telegram call
    # ------------------------------------------------------

    try:

        result = asyncio.run(
            send_sticker()
        )

        print()
        print("✅ ANIMATED STICKER SENT")
        print()

        print(
            f"Telegram Message ID: {result.message_id}"
        )

        print()

    except Exception as ex:

        print()
        print("❌ ANIMATED STICKER FAILED")
        print()

        print(
            f"Error Type : {type(ex).__name__}"
        )

        print(
            f"Error      : {ex}"
        )

        print()

        raise