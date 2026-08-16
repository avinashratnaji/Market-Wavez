"""
scripts/test_telegram_animation.py

Test Telegram animated sticker support.

Author : Market Wavez
"""

from pathlib import Path

from market_sentinel.telegram.notifier import TelegramNotifier


# ==========================================================
# CONFIGURATION
# ==========================================================

STICKER_FILE = Path(
    "data/telegram_stickers/alert.tgs"
)


# ==========================================================
# MAIN
# ==========================================================

def main():

    print(
        "=============================================="
    )

    print(
        "       Market Wavez Telegram Animation"
    )

    print(
        "=============================================="
    )

    print()

    print(
        f"Sticker: {STICKER_FILE}"
    )

    print()

    if not STICKER_FILE.exists():

        print(
            "ERROR: Sticker file does not exist."
        )

        print()

        print(
            "Create this folder:"
        )

        print(
            "data/telegram_stickers/"
        )

        print()

        print(
            "Then place your animated .tgs sticker here:"
        )

        print(
            "data/telegram_stickers/alert.tgs"
        )

        return

    notifier = TelegramNotifier()

    notifier.notify_sticker(
        STICKER_FILE
    )

    print()

    print(
        "Animated sticker sent."
    )


if __name__ == "__main__":

    main()