"""
tests/test_telegram_stickers.py

Test Market Wavez sentiment stickers.

Author : Market Wavez
"""

import asyncio

from market_sentinel.telegram.bot import TelegramBot


MARKET_STICKERS = {
    "bullish": (
        "CAACAgIAAxkBAANiany1FRV9qDItFJspH6Aa3mpDXbgAArcMAAKYCFBLqkZ6AAFX8EpcPQQ"
    ),

    "bearish": (
        "CAACAgIAAxkBAANjany1HIbPOQ1CvryVmeJWcjrI6FUAAn0LAAL1TulLxOy6yqzKgrA9BA"
    ),

    "neutral": (
        "CAACAgIAAxkBAANkany1PnJHIFsiISaNntwJznsUxCkAAvIAA_cCyA-_2j2KsgEYyj0E"
    ),
}


async def send_stickers():

    bot = TelegramBot()

    print()
    print("=" * 60)
    print("🌊 MARKET WAVEZ - SENTIMENT STICKER TEST")
    print("=" * 60)

    for sentiment, sticker_id in MARKET_STICKERS.items():

        print()
        print(
            f"Sending {sentiment.upper()} sticker..."
        )

        message = await bot.bot.send_sticker(
            chat_id=bot.chat_id,
            sticker=sticker_id,
        )

        print(
            f"✅ {sentiment.upper()} sticker sent"
        )

        print(
            f"Message ID: {message.message_id}"
        )

        await asyncio.sleep(2)

    print()
    print("=" * 60)
    print("✅ ALL THREE STICKERS SENT")
    print("=" * 60)


def test_sentiment_stickers():

    asyncio.run(
        send_stickers()
    )