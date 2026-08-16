"""
Market Wavez
Fresh Telegram Animated Sticker Collector

Collects ONLY stickers sent AFTER this script starts.
"""

from __future__ import annotations

import asyncio

from telegram import Bot
from market_sentinel.config.settings import settings


STICKER_TYPES = [
    ("BULLISH", "🐂"),
    ("BEARISH", "🐻"),
    ("NEUTRAL", "😐"),
]


async def main():

    bot = Bot(
        token=settings.TELEGRAM_BOT_TOKEN
    )

    me = await bot.get_me()

    print()
    print("=" * 70)
    print("🌊 MARKET WAVEZ - FRESH STICKER COLLECTOR")
    print("=" * 70)

    print()
    print(f"Bot      : @{me.username}")
    print(f"Bot ID   : {me.id}")

    # ======================================================
    # STEP 1
    # CLEAR OLD UPDATES
    # ======================================================

    print()
    print("🧹 Clearing old Telegram updates...")

    old_updates = await bot.get_updates(
        offset=-1,
        timeout=1,
        allowed_updates=["message"],
    )

    if old_updates:
        print(
            f"Found {len(old_updates)} old update(s)."
        )

        latest_update_id = old_updates[-1].update_id

        await bot.get_updates(
            offset=latest_update_id + 1,
            timeout=1,
            allowed_updates=["message"],
        )

        offset = latest_update_id + 1

    else:

        print("No old updates found.")

        offset = None

    print()
    print("✅ Old updates cleared.")
    print()
    print("=" * 70)

    # ======================================================
    # STEP 2
    # COLLECT NEW STICKERS
    # ======================================================

    results = {}

    for sticker_name, emoji in STICKER_TYPES:

        print()
        print("=" * 70)
        print(
            f"{emoji} SEND NEW {sticker_name} STICKER NOW"
        )
        print("=" * 70)

        print()
        print(
            "IMPORTANT:"
        )
        print(
            "Send the sticker DIRECTLY to the bot."
        )
        print(
            "Only a sticker sent AFTER this message will be accepted."
        )
        print()

        while True:

            updates = await bot.get_updates(
                offset=offset,
                timeout=30,
                allowed_updates=["message"],
            )

            if not updates:
                continue

            for update in updates:

                offset = update.update_id + 1

                message = update.message

                if message is None:
                    continue

                # ------------------------------------------------
                # Ignore messages without stickers
                # ------------------------------------------------

                if message.sticker is None:

                    print(
                        "Ignoring non-sticker message..."
                    )

                    continue

                sticker = message.sticker

                # ------------------------------------------------
                # Reject non-animated stickers
                # ------------------------------------------------

                if not sticker.is_animated:

                    print()
                    print(
                        "⚠️ Sticker received, but it is NOT animated."
                    )

                    print(
                        "Please send an animated sticker."
                    )

                    continue

                # ------------------------------------------------
                # Accept sticker
                # ------------------------------------------------

                results[sticker_name.lower()] = {
                    "file_id": sticker.file_id,
                    "file_unique_id": sticker.file_unique_id,
                    "animated": sticker.is_animated,
                    "video": sticker.is_video,
                    "width": sticker.width,
                    "height": sticker.height,
                }

                print()
                print("=" * 70)
                print(
                    f"✅ NEW {sticker_name} STICKER RECEIVED"
                )
                print("=" * 70)

                print()
                print(
                    f"File ID   : {sticker.file_id}"
                )

                print(
                    f"Unique ID : {sticker.file_unique_id}"
                )

                print(
                    f"Animated  : {sticker.is_animated}"
                )

                print(
                    f"Video     : {sticker.is_video}"
                )

                print(
                    f"Size      : {sticker.width} x {sticker.height}"
                )

                break

            else:
                continue

            break

    # ======================================================
    # STEP 3
    # FINAL CONFIGURATION
    # ======================================================

    print()
    print()
    print("=" * 70)
    print("🎉 FRESH STICKER COLLECTION COMPLETE")
    print("=" * 70)

    print()
    print("MARKET_STICKERS = {")

    for name, data in results.items():

        print(
            f'    "{name}": "{data["file_id"]}",'
        )

    print("}")

    print()
    print("=" * 70)
    print("DO NOT SEND ANY MORE STICKERS.")
    print("=" * 70)
    print()


if __name__ == "__main__":

    try:

        asyncio.run(main())

    except KeyboardInterrupt:

        print()
        print()
        print("❌ Collector stopped.")