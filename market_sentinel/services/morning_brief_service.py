"""
services/morning_brief_service.py

Morning Brief Service.

Author : Market Sentinel
Version : 1.2.0
"""

from market_sentinel.briefs.morning import (
    MorningBriefBuilder,
)

from market_sentinel.config.telegram_stickers import (
    MARKET_STICKERS,
)

from market_sentinel.telegram.morning import (
    MorningFormatter,
)

from market_sentinel.telegram.notifier import (
    TelegramNotifier,
)

from market_sentinel.utils.logger import logger
from market_sentinel.visuals.brief_card import BriefCardRenderer
from html import escape


class MorningBriefService:
    """
    Builds and sends the Morning Brief.
    """

    def __init__(self):

        self.builder = MorningBriefBuilder()

        self.notifier = TelegramNotifier()

    def send(self, section: str = "full", window: str = "full") -> None:

        logger.info(
            "Building Morning Brief..."
        )

        brief = self.builder.build(window=window)

        logger.success(
            "Morning Brief built."
        )

        fallback_messages = self._section_messages(MorningFormatter.format_window(brief, window), section)
        messages = fallback_messages
        image_paths: list[str] = []
        if window in {"morning", "afternoon", "night"}:
            try:
                image_paths = [str(path) for path in BriefCardRenderer().render_cards(brief, window, section)]
                # Image cards contain the displayed data. Keep only compact,
                # clickable source links; do not post the same tables twice.
                if image_paths:
                    messages = self._source_messages(brief, window, section)
            except Exception as exc:
                logger.warning(f"Briefing card unavailable; continuing with text: {exc}")

        logger.info(
            "Sending Morning Brief..."
        )

        # ==================================================
        # DETERMINE SENTIMENT
        # ==================================================

        sentiment = (
            brief.market_sentiment
            .strip()
            .lower()
        )

        sticker_id = MARKET_STICKERS.get(
            sentiment
        )

        if sticker_id:

            logger.info(
                f"Sending {sentiment} sentiment sticker..."
            )

        else:

            logger.warning(
                f"No sticker configured for sentiment: "
                f"{brief.market_sentiment}"
            )

        # ==================================================
        # SEND EVERYTHING IN ONE EVENT LOOP
        # ==================================================

        self.notifier.send_brief(
            messages=messages,
            sticker_id=sticker_id,
            image_paths=image_paths,
        )

        logger.success(
            "Morning Brief sent successfully."
        )

    @staticmethod
    def _section_messages(messages: list[str], section: str) -> list[str]:
        """Return only the requested terminal panel for on-demand commands."""
        section = (section or "full").lower()
        if section == "full":
            return messages
        markers = {
            "indian_markets": ("INDIA MORNING BRIEF", "INDIAN MARKETS", "SECTOR HEATMAP"),
            "movers": ("TOP GAINERS",),
            "stock_research": ("STOCKS TO RESEARCH", "HIGH-GROWTH RESEARCH"),
            "global_markets": ("GLOBAL MARKET NEWS", "GLOBAL INDICES"),
            "us_movers": ("US MARKET TOP MOVERS",),
            "crypto": ("CRYPTO MARKET NEWS", "COMMODITIES & CRYPTO"),
            "ipos": ("CURRENT OPEN IPOs",),
            "flows": ("INSTITUTIONAL FLOWS",),
        }
        requested = markers.get(section)
        if not requested:
            raise ValueError(f"Unknown brief section: {section}")
        selected = [message for message in messages if any(marker in message for marker in requested)]
        return selected or messages[:1]

    @staticmethod
    def _source_messages(brief, window: str, section: str = "full") -> list[str]:
        """Send useful linked context alongside visual cards, not a source-only list."""
        section = (section or "full").lower()
        if window == "morning" and section == "full":
            groups = (("INDIA MARKET CATALYSTS", (brief.indian_news or brief.top_news) + brief.indian_events),)
        elif window == "morning" and section == "indian_markets":
            groups = (("INDIA MARKET CATALYSTS", (brief.indian_news or brief.top_news) + brief.indian_events),)
        elif window == "night" and section == "full":
            groups = (
                ("GLOBAL MARKET NEWS", brief.global_impact_news + brief.us_events),
                ("CRYPTO MARKET NEWS", brief.crypto_news),
            )
        elif window == "night" and section == "global_markets":
            groups = (("GLOBAL MARKET NEWS", brief.global_impact_news + brief.us_events),)
        elif window == "night" and section == "crypto":
            groups = (("CRYPTO MARKET NEWS", brief.crypto_news),)
        else:
            groups = ()

        messages: list[str] = []
        for title, articles in groups:
            selected = list(articles[:10])
            for page_start in range(0, len(selected), 5):
                page = selected[page_start:page_start + 5]
                page_number = page_start // 5 + 1
                page_total = (len(selected) + 4) // 5
                lines = [f"📰 <b>{title}" + (f" · {page_number}/{page_total}" if page_total > 1 else "") + "</b>", ""]
                for number, article in enumerate(page, page_start + 1):
                    source = escape((article.source or "Source").strip())
                    if article.url:
                        source = f'<a href="{escape(article.url, quote=True)}">{source}</a>'
                    summary = MorningFormatter._compact_summary(article)
                    if len(summary) > 260:
                        summary = summary[:257].rsplit(" ", 1)[0] + "…"
                    lines.append(f"<b>{number}. {escape(article.title or 'Market update')}</b>")
                    if summary:
                        lines.append(f"• {escape(summary)}")
                    lines.extend((f"↗ {source}", ""))
                lines.append("<i>Verified context for research; not investment advice.</i>")
                messages.append("\n".join(lines))
        if not messages:
            messages.append("<i>Market data is informational research, not investment advice.</i>")
        return messages
