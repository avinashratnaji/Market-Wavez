import asyncio

from market_sentinel.telegram.bot import TelegramBot


async def main():
    await TelegramBot().send_message("Hello from Market Wavez 🚀")


asyncio.run(main())