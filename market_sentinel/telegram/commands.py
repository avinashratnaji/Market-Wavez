"""On-demand Telegram terminal commands backed by GitHub Actions."""

from __future__ import annotations

import requests
from telegram import BotCommand, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from market_sentinel.config.settings import settings


class GitHubActionsDispatcher:
    """Dispatch the existing workflow with a requested terminal panel."""

    WORKFLOW = "morning_brief.yml"

    def dispatch(self, section: str) -> None:
        if not settings.GITHUB_REPOSITORY or not settings.GITHUB_ACTIONS_TOKEN:
            raise RuntimeError("GitHub dispatch is not configured. Set GITHUB_REPOSITORY and GITHUB_ACTIONS_TOKEN.")
        response = requests.post(
            f"https://api.github.com/repos/{settings.GITHUB_REPOSITORY}/actions/workflows/{self.WORKFLOW}/dispatches",
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {settings.GITHUB_ACTIONS_TOKEN}",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            json={
                "ref": settings.GITHUB_REF,
                "inputs": {
                    "section": "full" if section in {"morning", "afternoon", "night"} else section,
                    "brief": section if section in {"morning", "afternoon", "night"} else "full",
                },
            },
            timeout=15,
        )
        if response.status_code == 403:
            raise RuntimeError(
                "GitHub token lacks Actions: write access for this repository. "
                "Create/update a fine-grained token for this repository with Actions = Read and write, "
                "then replace GITHUB_ACTIONS_TOKEN and restart the listener."
            )
        if response.status_code == 422:
            raise RuntimeError(
                "The GitHub workflow on the selected branch is not the updated command-enabled version. "
                "Commit and push this workspace (including .github/workflows/morning_brief.yml) to the configured GITHUB_REF, then retry."
            )
        if response.status_code != 204:
            raise RuntimeError(f"GitHub Actions dispatch failed ({response.status_code}). Check repository, branch, and token settings.")


class TelegramCommandServer:
    """Long-polling command listener. Host it continuously for live commands."""

    COMMANDS = {
        "morningbrief": "morning",
        "afternoonbrief": "afternoon",
        "nightbrief": "night",
        "indianmarkets": "indian_markets",
        "topgainersandlosers": "movers",
        "globalmarkets": "global_markets",
        "usmovers": "us_movers",
        "cryptomarkets": "crypto",
        "ipos": "ipos",
        "fiidiiflows": "flows",
        "marketbrief": "full",
    }

    def __init__(self) -> None:
        if not settings.TELEGRAM_BOT_TOKEN:
            raise ValueError("Telegram token is missing. Set TELEGRAM_BOT_TOKEN in .env.")
        self.dispatcher = GitHubActionsDispatcher()

    def run(self) -> None:
        application = (
            ApplicationBuilder()
            .token(settings.TELEGRAM_BOT_TOKEN)
            .post_init(self._register_commands)
            .build()
        )
        application.add_handler(CommandHandler("start", self._start))
        application.add_handler(CommandHandler("whoami", self._whoami))
        for command, section in self.COMMANDS.items():
            application.add_handler(CommandHandler(command, self._dispatch(section)))
        application.run_polling(allowed_updates=Update.ALL_TYPES)

    async def _register_commands(self, application) -> None:
        """Publish the slash-command menu shown by Telegram clients."""
        await application.bot.set_my_commands([
            BotCommand("marketbrief", "Full live market brief"),
            BotCommand("morningbrief", "Indian pre-market brief"),
            BotCommand("afternoonbrief", "Post-market, flows and IPOs"),
            BotCommand("nightbrief", "Global markets and crypto brief"),
            BotCommand("whoami", "Show this chat ID for command access"),
            BotCommand("indianmarkets", "Indian indices and sector heatmap"),
            BotCommand("topgainersandlosers", "NSE cash-market movers"),
            BotCommand("globalmarkets", "Global news and indices"),
            BotCommand("usmovers", "US market top gainers and losers"),
            BotCommand("cryptomarkets", "Crypto quotes and top crypto news"),
            BotCommand("ipos", "Open IPOs ranked by GMP"),
            BotCommand("fiidiiflows", "FII/FPI and DII cash-market flows"),
        ])

    async def _start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not update.effective_message:
            return
        await update.effective_message.reply_text(
            "Market Wavez terminal commands:\n"
            "/indianmarkets\n/topgainersandlosers\n/globalmarkets\n"
            "/usmovers\n/cryptomarkets\n/ipos\n/fiidiiflows\n/marketbrief\n"
            "/morningbrief\n/afternoonbrief\n/nightbrief\n\n"
            "If a command is restricted, run /whoami and set its ID as TELEGRAM_COMMAND_CHAT_ID."
        )

    async def _whoami(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not update.effective_message or not update.effective_chat:
            return
        await update.effective_message.reply_text(
            f"Your private command chat ID is: {update.effective_chat.id}\n\n"
            "Set this exact value in .env as TELEGRAM_COMMAND_CHAT_ID, then restart telegram-listen."
        )

    def _dispatch(self, section: str):
        async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
            if not update.effective_chat or not update.effective_message:
                return
            permitted_chat = settings.TELEGRAM_COMMAND_CHAT_ID or settings.TELEGRAM_CHAT_ID
            if permitted_chat and str(update.effective_chat.id) != str(permitted_chat):
                await update.effective_message.reply_text(
                    "This command chat is not authorized. Run /whoami, copy the returned ID into "
                    "TELEGRAM_COMMAND_CHAT_ID in .env, then restart telegram-listen."
                )
                return
            try:
                self.dispatcher.dispatch(section)
            except RuntimeError as exc:
                await update.effective_message.reply_text(f"Unable to request the live panel: {exc}")
                return
            await update.effective_message.reply_text("Live data requested. The selected terminal panel will be posted shortly.")
        return handler
