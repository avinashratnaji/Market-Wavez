from __future__ import annotations

import asyncio

from telegram import Bot
from market_sentinel.config.settings import settings


async def main():

    bot = Bot(
        token=settings.TELEGRAM_BOT_TOKEN
    )

    print("=" * 60)
    print("TELEGRAM BOT CONNECTION CHECK")
    print("=" * 60)

    # ------------------------------------------------------
    # Bot information
    # ------------------------------------------------------

    me = await bot.get_me()

    print()
    print("BOT:")
    print(f"Name     : {me.first_name}")
    print(f"Username : @{me.username}")
    print(f"ID       : {me.id}")

    # ------------------------------------------------------
    # Webhook information
    # ------------------------------------------------------

    webhook = await bot.get_webhook_info()

    print()
    print("WEBHOOK:")
    print(f"URL              : {webhook.url}")
    print(f"Pending updates  : {webhook.pending_update_count}")
    print(f"Last error       : {webhook.last_error_message}")
    print(f"Last error date  : {webhook.last_error_date}")

    print()
    print("=" * 60)

    if webhook.url:

        print("⚠️ WEBHOOK IS ACTIVE")
        print()
        print("getUpdates polling will not work.")
        print("We need to remove the webhook before")
        print("using the sticker-ID polling script.")

    else:

        print("✅ NO WEBHOOK")
        print()
        print("getUpdates should work.")

    print("=" * 60)


if __name__ == "__main__":

    asyncio.run(main())