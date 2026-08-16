"""
market_sentinel/telegram/morning.py
Formats the Morning Brief for Telegram.
Author : Market Wavez
"""

from __future__ import annotations

from html import escape

from market_sentinel.briefs.models import MorningBrief


class MorningFormatter:

    LINE = "━━━━━━━━━━━━━━━━━━━━"

    # ==========================================================
    # MAIN FORMATTER
    # ==========================================================

    @staticmethod
    def format(
        brief: MorningBrief,
    ) -> list[str]:

        messages: list[str] = []

        # ======================================================
        # MESSAGE 1
        # Executive Summary
        # ======================================================

        lines: list[str] = []

        sentiment = (
            brief.market_sentiment
            or "Neutral"
        )

        sentiment_emoji = (
            MorningFormatter._sentiment_emoji(
                sentiment
            )
        )

        lines.append(
            f"📅 <b>{brief.generated_at:%d %b %Y}</b>"
            f" | ⏰ <b>{brief.generated_at:%I:%M %p} IST</b>"
        )

        lines.append("")

        lines.append(
            f"🩺 <b>Health:</b> "
            f"<code>{brief.health_score}/100</code>"
        )

        lines.append(
            f"🐻 <b>Sentiment:</b> "
            f"<b>{escape(sentiment)}</b> "
            f"({brief.confidence}%) "
            f"{sentiment_emoji}"
        )

        lines.append("")

        lines.append(
            "📰 <b>TOP 5 THINGS TODAY</b>"
        )

        lines.append(
            MorningFormatter.LINE
        )

        lines.append("")

        if brief.ai_summary:
            lines.append("<b>MARKET READ</b>")
            lines.append(MorningFormatter.LINE)
            lines.append(escape(brief.ai_summary))
            lines.append("")

        indian_news = brief.indian_news or brief.top_news

        if indian_news:

            for number, article in enumerate(
                indian_news[:5],
                start=1,
            ):

                title = (
                    article.title
                    or "Market update"
                )

                lines.append(
                    f"{number}️⃣ "
                    f"{escape(title)}"
                )

        else:

            lines.append(
                "No major market-moving events today."
            )

        # Compose the public lead message in the detailed channel format.
        lines = MorningFormatter._india_news_message(brief)

        messages.append(
            "\n".join(lines)
        )

        # ======================================================
        # MESSAGE 2
        # Indian Markets
        # ======================================================

        if brief.indices:

            lines = []

            lines.append(
                "📊 <b>INDIAN MARKETS</b>"
            )

            lines.append(
                MorningFormatter.LINE
            )

            # ----------------------------------------------
            # Separate UP / DOWN
            # ----------------------------------------------

            up = sorted(
                [
                    index
                    for index in brief.indices
                    if index.percent_change >= 0
                ],
                key=lambda x: x.percent_change,
                reverse=True,
            )

            down = sorted(
                [
                    index
                    for index in brief.indices
                    if index.percent_change < 0
                ],
                key=lambda x: x.percent_change,
            )

            # ----------------------------------------------
            # UP
            # ----------------------------------------------

            if up:

                lines.append("")

                lines.append(
                    "🟢 <b>UP</b>"
                )

                lines.append("")

                for index in up:

                    lines.append(
                        MorningFormatter._market_row(
                            index
                        )
                    )

            # ----------------------------------------------
            # DOWN
            # ----------------------------------------------

            if down:

                lines.append("")

                lines.append(
                    "🔴 <b>DOWN</b>"
                )

                lines.append("")

                for index in down:

                    lines.append(
                        MorningFormatter._market_row(
                            index
                        )
                    )

            messages.append(
                "\n".join(lines)
            )

        # ======================================================
        # MESSAGE 3
        # Sector Heatmap
        # ======================================================

        if brief.sectors:

            lines = []

            lines.append(
                "🌡 <b>SECTOR HEATMAP</b>"
            )

            lines.append(
                MorningFormatter.LINE
            )

            positive = []
            neutral = []
            negative = []

            # ----------------------------------------------
            # Sort strongest to weakest
            # ----------------------------------------------

            sectors = sorted(
                brief.sectors,
                key=lambda s: s.percent_change,
                reverse=True,
            )

            for sector in sectors:

                row = (
                    MorningFormatter._sector_row(
                        sector
                    )
                )

                if sector.percent_change > 0.20:

                    positive.append(row)

                elif sector.percent_change < -0.20:

                    negative.append(row)

                else:

                    neutral.append(row)

            # ----------------------------------------------
            # BULLISH
            # ----------------------------------------------

            if positive:

                lines.append("")

                lines.append(
                    "🟢 <b>BULLISH</b>"
                )

                for row in positive:
                    lines.append(row)

            # ----------------------------------------------
            # NEUTRAL
            # ----------------------------------------------

            if neutral:

                lines.append("")

                lines.append(
                    "🟡 <b>NEUTRAL</b>"
                )

                for row in neutral:
                    lines.append(row)

            # ----------------------------------------------
            # BEARISH
            # ----------------------------------------------

            if negative:

                lines.append("")

                lines.append(
                    "🔴 <b>BEARISH</b>"
                )

                for row in negative:
                    lines.append(row)

            messages.append(
                "\n".join(lines)
            )

        # ======================================================
        # MESSAGE 4
        # Top Movers
        # ======================================================

        if brief.gainers or brief.losers:

            lines = []

            # ==================================================
            # TOP GAINERS
            # ==================================================

            if brief.gainers:

                lines.append(
                    "🚀 <b>TOP GAINERS</b>"
                )

                lines.append(
                    MorningFormatter.LINE
                )

                lines.append("")

                gainers = sorted(
                    brief.gainers,
                    key=lambda s: s.percent_change,
                    reverse=True,
                )

                for stock in gainers[:5]:

                    lines.append(
                        MorningFormatter._stock_row(
                            stock,
                            direction="up",
                        )
                    )

            # ==================================================
            # TOP LOSERS
            # ==================================================

            if brief.losers:

                lines.append("")

                lines.append(
                    "🩸 <b>TOP LOSERS</b>"
                )

                lines.append(
                    MorningFormatter.LINE
                )

                lines.append("")

                losers = sorted(
                    brief.losers,
                    key=lambda s: s.percent_change,
                )

                for stock in losers[:5]:

                    lines.append(
                        MorningFormatter._stock_row(
                            stock,
                            direction="down",
                        )
                    )

            messages.append(
                "\n".join(lines)
            )

        # ======================================================
        # MESSAGE 5
        # Top Market News
        # ======================================================

        # Indian Top 5 is already sent in the first message. Keep this legacy
        # detail message only for callers that have not populated indian_news.
        if brief.top_news and not brief.indian_news:

            lines = []

            lines.append(
                "🌐 <b>TOP MARKET NEWS</b>"
            )

            lines.append(
                MorningFormatter.LINE
            )

            lines.append("")

            for article in brief.top_news[:8]:

                title = (
                    article.title
                    or "Market News"
                )

                title = escape(title)

                if article.url:

                    lines.append(
                        f'🔗 <a href="{escape(article.url, quote=True)}">'
                        f"{title}"
                        f"</a>"
                    )

                else:

                    lines.append(
                        f"📰 {title}"
                    )

                source = (
                    article.source
                    or ""
                ).strip()

                if source:

                    lines.append(
                        f"   <i>{escape(source)}</i>"
                    )

                lines.append("")

            messages.append(
                "\n".join(lines)
            )

        # This is always present so a feed failure cannot silently make the
        # global-market watch disappear from the daily brief.
        messages.append("\n".join(MorningFormatter._global_news_message(brief)))
        messages.append("\n".join(MorningFormatter._external_markets_message(brief)))
        messages.append("\n".join(MorningFormatter._us_movers_message(brief)))
        messages.append("\n".join(MorningFormatter._crypto_news_message(brief)))

        if brief.investor_flows or brief.top_ipos:
            lines = [
                "<b>INSTITUTIONAL FLOWS</b>",
                MorningFormatter.LINE,
                "",
            ]
            if brief.investor_flows:
                flow = brief.investor_flows
                lines.append(f"<b>FII / DII CASH MARKET — {flow.trade_date:%d %b %Y}</b>")
                lines.append("")
                lines.extend(MorningFormatter._institutional_ledger("FII / FPI", flow.fii_buy, flow.fii_sell, flow.fii_net))
                lines.append("")
                lines.extend(MorningFormatter._institutional_ledger("DII", flow.dii_buy, flow.dii_sell, flow.dii_net))
                lines.append(f"<i>Source: {escape(flow.source)}</i>")
                if flow.source != "NSE":
                    lines.append("<i>Values were not published in this run; no estimate is shown.</i>")
                lines.append("")
            lines.append("<b>CURRENT OPEN IPOs — GMP WATCH</b>")
            lines.append("<i>Ranked by GMP %; includes IPOs live for the next trading session.</i>")
            lines.append("")
            if brief.top_ipos:
                mainboard = [ipo for ipo in brief.top_ipos if "MAIN" in (ipo.issue_type or "").upper()]
                sme = [ipo for ipo in brief.top_ipos if "SME" in (ipo.issue_type or "").upper()]
                unclassified = [ipo for ipo in brief.top_ipos if ipo not in mainboard and ipo not in sme]
                groups = (("MAINBOARD IPOs", mainboard), ("SME IPOs", sme), ("OTHER OPEN IPOs", unclassified))
                for section_title, ipos in groups:
                    if not ipos:
                        continue
                    lines.extend((f"<b>{section_title}</b>", ""))
                    for number, ipo in enumerate(ipos[:5], start=1):
                        percent = f" ({ipo.gmp_percent:.1f}%)" if ipo.gmp_percent is not None else ""
                        issue_price = f"₹{ipo.price_band_high:,.0f}" if ipo.price_band_high is not None else "Not published"
                        subscription = (
                            f" | {ipo.subscription_open:%d %b}–{ipo.subscription_close:%d %b}"
                            if ipo.subscription_open and ipo.subscription_close
                            else f" | Closes {ipo.subscription_close:%d %b}" if ipo.subscription_close else ""
                        )
                        availability = (
                            f" (Opens {ipo.subscription_open:%d %b})"
                            if ipo.subscription_open and ipo.subscription_open.date() > brief.generated_at.date()
                            else ""
                        )
                        gmp = f"<code>₹{ipo.gmp:,.0f}</code>{percent}" if ipo.gmp is not None else "<code>Awaiting GMP quote</code>"
                        issue_type = MorningFormatter._ipo_type(ipo.issue_type)
                        lot = f"{ipo.lot_size:,}" if ipo.lot_size else "Not published"
                        amount = (
                            f"₹{ipo.lot_size * ipo.price_band_high:,.0f}"
                            if ipo.lot_size and ipo.price_band_high else "Not published"
                        )
                        about = " ".join((ipo.about or "").split()) or "Company details are being verified."
                        if len(about) > 180:
                            about = about[:177].rsplit(" ", 1)[0] + "…"
                        lines.append(
                            f"{number}. <b>{escape(ipo.name)}</b>\n"
                            f"   Type        : <code>{escape(issue_type)}</code>\n"
                            f"   GMP         : {gmp}\n"
                            f"   Issue Price : <code>{issue_price}</code>\n"
                            f"   Minimum Qty : <code>{lot}</code>\n"
                            f"   Amount      : <code>{amount}</code>\n"
                            f"   Valid from  : <code>{subscription.lstrip(' |')}</code>{availability}\n"
                            f"   About       : {escape(about)}\n"
                        )
                lines.extend(("", "<i>GMP is informal, volatile, and not an official exchange price.</i>"))
            else:
                lines.append("No open Mainboard or SME IPO was returned by the official NSE issue list or GMP sources in this run.")

            if False and brief.top_ipos:
                lines.append("<b>TOP 5 IPO GMP (INDICATIVE)</b>")
                for number, ipo in enumerate(brief.top_ipos[:5], start=1):
                    percent = f" ({ipo.gmp_percent:.1f}%)" if ipo.gmp_percent is not None else ""
                    close = f" | closes {ipo.subscription_close:%d %b}" if ipo.subscription_close else ""
                    updated = f" | GMP {ipo.updated_at:%d %b %I:%M %p}" if ipo.updated_at else ""
                    lines.append(
                        f"{number}. <b>{escape(ipo.name)}</b> — "
                        f"<code>Rs {ipo.gmp:,.0f}</code>{percent}{close}{updated}"
                    )
                lines.extend(("", "<i>GMP is informal, volatile, and not an official exchange price.</i>"))
            ipo_start = next(
                (index for index, line in enumerate(lines) if "CURRENT OPEN IPOs" in line),
                None,
            )
            if ipo_start is None:
                messages.append("\n".join(lines))
            else:
                messages.append("\n".join(lines[:ipo_start]))
                messages.append("\n".join(lines[ipo_start:]))

        return messages

    @staticmethod
    def format_window(brief: MorningBrief, window: str = "full") -> list[str]:
        """Render one scheduled terminal window without duplicating a full brief."""
        window = (window or "full").lower()
        if window == "full":
            return MorningFormatter.format(brief)
        if window == "morning":
            messages = [
                "\n".join(MorningFormatter._premarket_message(brief)),
                "\n".join(MorningFormatter._compact_news_message(brief.indian_news or brief.top_news, "TOP 5 STORIES DRIVING THE SESSION")),
            ]
            messages.extend(message for message in MorningFormatter.format(brief) if "CURRENT OPEN IPOs" in message)
            return messages
        if window == "afternoon":
            full = MorningFormatter.format(brief)
            panels = ["\n".join(MorningFormatter._postmarket_message(brief))]
            panels.extend(message for message in full if "INSTITUTIONAL FLOWS" in message)
            return panels
        if window == "night":
            return [
                "\n".join(MorningFormatter._night_header(brief)),
                "\n".join(MorningFormatter._compact_news_message(brief.global_impact_news, "GLOBAL MARKET NEWS", include_summary=False)),
                "\n".join(MorningFormatter._external_markets_message(brief)),
                "\n".join(MorningFormatter._us_movers_message(brief)),
                "\n".join(MorningFormatter._compact_news_message(brief.crypto_news, "CRYPTO MARKET NEWS", include_summary=False)),
            ]
        raise ValueError(f"Unknown briefing window: {window}")

    @staticmethod
    def _premarket_message(brief: MorningBrief) -> list[str]:
        health, health_icon = MorningFormatter._health_label(brief.health_score)
        sentiment = brief.market_sentiment or "Neutral"
        nifty = MorningFormatter._find_index(brief, "NIFTY")
        gift = brief.gift_nifty or MorningFormatter._find_index(brief, "GIFT NIFTY")
        levels = MorningFormatter._nifty_levels(nifty.value) if nifty else None
        bank_nifty = MorningFormatter._find_index(brief, "BANKNIFTY")
        bank_levels = MorningFormatter._banknifty_levels(bank_nifty.value) if bank_nifty else None
        india_vix = MorningFormatter._find_index(brief, "VIX")
        sensex = MorningFormatter._find_index(brief, "SENSEX")
        us_indices = [item for item in brief.global_indices if item.name.upper() in {"NASDAQ", "S&P 500"}]
        gift_line = MorningFormatter._market_row(gift) if gift else "• GIFT Nifty: <i>Live quote unavailable</i>"
        if brief.fo_ban_symbols:
            ban = ", ".join(brief.fo_ban_symbols)
        elif brief.fo_ban_available:
            ban = "None (NSE live list)"
        else:
            ban = "Live list temporarily unavailable"
        lines = [
            MorningFormatter.LINE,
            "🇮🇳 <b>MARKET WAVES — MORNING PRE-MARKET BRIEF</b>",
            MorningFormatter.LINE,
            f"📅 {brief.generated_at:%d %b %Y} | ⏰ {brief.generated_at:%I:%M %p} IST",
            "",
            f"📊 <b>Market Health:</b> {health_icon} <code>{brief.health_score}/100</code> <b>{health}</b>",
            f"🧠 <b>Sentiment:</b> {escape(sentiment)} ({brief.confidence}% confidence)",
            "",
            "🚨 <b>PRE-MARKET INDICATORS</b>",
            MorningFormatter.LINE,
            gift_line,
            MorningFormatter._market_row(india_vix) if india_vix else "• India VIX: <i>Live quote unavailable</i>",
            MorningFormatter._market_row(nifty) if nifty else "• Nifty 50: <i>Live quote unavailable</i>",
            MorningFormatter._market_row(bank_nifty) if bank_nifty else "• Bank Nifty: <i>Live quote unavailable</i>",
            MorningFormatter._market_row(sensex) if sensex else "• Sensex: <i>Live quote unavailable</i>",
            *(MorningFormatter._quote_line(item, include_note=False) for item in us_indices),
            f"• F&O Ban List: <code>{escape(ban)}</code>",
            "",
            "📈 <b>KEY NIFTY 50 LEVELS TO WATCH</b>",
            MorningFormatter.LINE,
            f"• Immediate Support: <code>{levels[0]:,.0f}</code>" if levels else "• Immediate Support: <i>Needs a live Nifty quote</i>",
            f"• Immediate Resistance: <code>{levels[1]:,.0f}</code>" if levels else "• Immediate Resistance: <i>Needs a live Nifty quote</i>",
            "",
            "🏦 <b>KEY BANK NIFTY LEVELS TO WATCH</b>",
            MorningFormatter.LINE,
            f"• Immediate Support: <code>{bank_levels[0]:,.0f}</code>" if bank_levels else "• Immediate Support: <i>Needs a live Bank Nifty quote</i>",
            f"• Immediate Resistance: <code>{bank_levels[1]:,.0f}</code>" if bank_levels else "• Immediate Resistance: <i>Needs a live Bank Nifty quote</i>",
            "",
            "<i>Levels are rule-based reference zones, not investment advice.</i>",
        ]
        return lines

    @staticmethod
    def _postmarket_message(brief: MorningBrief) -> list[str]:
        lines = [MorningFormatter.LINE, "🇮🇳 <b>MARKET WAVES — POST-MARKET BRIEF</b>", MorningFormatter.LINE,
                 f"📅 {brief.generated_at:%d %b %Y} | ⏰ {brief.generated_at:%I:%M %p} IST", "",
                 "📊 <b>BENCHMARK CLOSING PRICES</b>", MorningFormatter.LINE]
        lines.extend(MorningFormatter._market_row(index) for index in brief.indices)
        lines.extend(("", "🔥 <b>SECTOR PERFORMANCE</b>", MorningFormatter.LINE))
        lines.extend(MorningFormatter._sector_row(sector) for sector in brief.sectors)
        lines.extend(("", "🟢 <b>TOP GAINERS</b>"))
        lines.extend(MorningFormatter._stock_compact_row(stock, "up") for stock in brief.gainers[:5])
        lines.extend(("", "🔴 <b>TOP LOSERS</b>"))
        lines.extend(MorningFormatter._stock_compact_row(stock, "down") for stock in brief.losers[:5])
        return lines

    @staticmethod
    def _night_header(brief: MorningBrief) -> list[str]:
        return [MorningFormatter.LINE, "🌍 <b>MARKET WAVES — GLOBAL MARKETS & CRYPTO BRIEF</b>", MorningFormatter.LINE,
                f"📅 {brief.generated_at:%d %b %Y} | ⏰ {brief.generated_at:%I:%M %p} IST"]

    @staticmethod
    def _compact_news_message(articles, title: str, include_summary: bool = True) -> list[str]:
        lines = ["🔥 <b>" + title + "</b>", MorningFormatter.LINE, ""]
        for number, article in enumerate(articles[:5], start=1):
            score = max(0, min(100, int(article.score or article.impact or 0)))
            source = escape((article.source or "Not supplied").strip())
            if article.url:
                source = f'<a href="{escape(article.url, quote=True)}">{source}</a>'
            lines.append(f"<b>{number}. {escape(article.title or 'Market update')}</b>")
            if include_summary:
                summary = MorningFormatter._compact_summary(article)
                if len(summary) > 240:
                    summary = summary[:237].rsplit(" ", 1)[0] + "…"
                lines.append(f"   • Summary: {escape(summary)}")
            lines.extend((f"   • Source: {source}", ""))
        return lines if len(lines) > 3 else lines + ["No major market-moving stories were verified."]

    @staticmethod
    def _find_index(brief: MorningBrief, name: str):
        needle = name.upper()
        return next((item for item in brief.indices if needle in item.name.upper()), None)

    @staticmethod
    def _nifty_levels(value: float) -> tuple[float, float]:
        base = round(value / 50) * 50
        return base - 100, base + 100

    @staticmethod
    def _banknifty_levels(value: float) -> tuple[float, float]:
        base = round(value / 100) * 100
        return base - 250, base + 250

    # ==========================================================
    # HELPERS
    # ==========================================================

    @staticmethod
    def _india_news_message(brief: MorningBrief) -> list[str]:
        sentiment = brief.market_sentiment or "Neutral"
        sentiment_icon = MorningFormatter._sentiment_emoji(sentiment)
        sentiment_animal = MorningFormatter._sentiment_animal(sentiment)
        health_label, health_icon = MorningFormatter._health_label(brief.health_score)
        lines = [
            "━━━━━━━━━━━━━━━━━━━━",
            "🇮🇳 <b>MARKET WAVES — INDIA MORNING BRIEF</b>",
            "━━━━━━━━━━━━━━━━━━━━",
            f"📅 {brief.generated_at:%d %b %Y} | ⏰ {brief.generated_at:%I:%M %p} IST",
            "",
            f"🩺 <b>Market Health:</b> {health_icon} <code>{brief.health_score}/100</code> <b>{health_label}</b>",
            f"{sentiment_animal} <b>Sentiment:</b> {escape(sentiment)} ({brief.confidence}% confidence) {sentiment_icon}",
            "",
            "📰 <b>TOP 5 THINGS TODAY</b>",
            "━━━━━━━━━━━━━━━━━━━━",
            "",
        ]
        articles = brief.indian_news or brief.top_news
        if not articles:
            return lines + ["No major Indian market-moving events were verified in this run."]
        for number, article in enumerate(articles[:5], start=1):
            lines.extend(MorningFormatter._news_card_lines(number, article))
        return lines

    @staticmethod
    def _global_news_message(brief: MorningBrief) -> list[str]:
        return MorningFormatter._compact_news_message(
            brief.global_impact_news,
            "GLOBAL MARKET NEWS",
            include_summary=False,
        )

        # Legacy detailed renderer retained below for reference.
        lines = [
            "━━━━━━━━━━━━━━━━━━━━",
            "🌍 <b>GLOBAL MARKET NEWS</b>",
            "━━━━━━━━━━━━━━━━━━━━",
            "",
        ]
        for number, article in enumerate(brief.global_impact_news[:5], start=1):
            lines.extend(MorningFormatter._news_card_lines(number, article))
        if not brief.global_impact_news:
            lines.append("No fresh high-priority global market stories were available from the configured sources in this run.")
        return lines

    @staticmethod
    def _crypto_news_message(brief: MorningBrief) -> list[str]:
        return MorningFormatter._compact_news_message(
            brief.crypto_news,
            "CRYPTO MARKET NEWS",
            include_summary=False,
        )

        # Legacy detailed renderer retained below for reference.
        lines = ["━━━━━━━━━━━━━━━━━━━━", "🪙 <b>CRYPTO MARKET NEWS</b>", "━━━━━━━━━━━━━━━━━━━━", ""]
        if not brief.crypto_news:
            return lines + ["No high-priority crypto market event was verified in this run."]
        for number, article in enumerate(brief.crypto_news[:5], start=1):
            lines.extend(MorningFormatter._news_card_lines(number, article))
        return lines

    @staticmethod
    def _external_markets_message(brief: MorningBrief) -> list[str]:
        lines = ["━━━━━━━━━━━━━━━━━━━━", "🌍 <b>GLOBAL INDICES</b>", "━━━━━━━━━━━━━━━━━━━━"]
        lines.extend(MorningFormatter._quote_line(item) for item in brief.global_indices)
        if not brief.global_indices:
            lines.append("Live global index quotes unavailable in this run.")
        lines.extend(("", "━━━━━━━━━━━━━━━━━━━━", "🛢 <b>COMMODITIES</b>", "━━━━━━━━━━━━━━━━━━━━"))
        lines.extend(MorningFormatter._quote_line(item, include_note=False) for item in brief.commodities)
        lines.extend(("", "━━━━━━━━━━━━━━━━━━━━", "🪙 <b>CRYPTO MARKETS</b>", "━━━━━━━━━━━━━━━━━━━━"))
        lines.extend(MorningFormatter._quote_line(item, include_note=False) for item in brief.crypto)
        if not brief.commodities and not brief.crypto:
            lines.append("Live commodity and crypto quotes unavailable in this run.")
        return lines

    @staticmethod
    def _us_movers_message(brief: MorningBrief) -> list[str]:
        lines = [MorningFormatter.LINE, "🇺🇸 <b>US MARKET TOP MOVERS</b>", MorningFormatter.LINE]
        if brief.us_gainers:
            lines.extend(("", "🟢 <b>TOP GAINERS</b>"))
            lines.extend(MorningFormatter._us_mover_row(item, "up") for item in brief.us_gainers[:5])
        if brief.us_losers:
            lines.extend(("", "🔴 <b>TOP LOSERS</b>"))
            lines.extend(MorningFormatter._us_mover_row(item, "down") for item in brief.us_losers[:5])
        if not brief.us_gainers and not brief.us_losers:
            lines.append("Live US mover data unavailable in this run.")
        return lines

    @staticmethod
    def _us_mover_row(quote, direction: str) -> str:
        icon = "📈" if direction == "up" else "📉"
        arrow = "▲" if direction == "up" else "▼"
        return f"{icon} <b>{escape(quote.name)}</b> = ${quote.value:,.2f} ({arrow} {abs(quote.percent_change):.2f}%)"

    @staticmethod
    def _quote_line(quote, include_note: bool = True) -> str:
        direction = "▲" if quote.percent_change >= 0 else "▼"
        icon = "🟢" if quote.percent_change > 0.15 else "🔴" if quote.percent_change < -0.15 else "🟡"
        value = f"₹{quote.value:,.0f}" if quote.unit.startswith("₹") else f"${quote.value:,.2f}" if quote.unit == "$" else f"{quote.value:,.2f}"
        suffix = f" {quote.unit}" if quote.unit and not quote.unit.startswith(("₹", "$")) else ""
        name_map = {
            "Gold 24K INDIA": "Gold IND (24K)",
            "Silver INDIA": "Silver IND",
            "Gold (COMEX INR equiv.)": "Gold US",
            "Silver (COMEX INR equiv.)": "Silver US",
        }
        name = name_map.get(quote.name, quote.name)
        note = f" <i>({escape(quote.note)})</i>" if include_note and quote.note else ""
        return f"{icon}<b>{escape(name)}</b> : {value}{suffix} ({direction}{quote.percent_change:+.2f}%){note}"

    @staticmethod
    def _compact_summary(article) -> str:
        """Keep a compact card useful when a feed repeats its own headline."""
        title = " ".join((article.title or "").split()).lower()
        summary = " ".join((article.summary or "").split())
        lowered = summary.lower()
        if title and lowered.startswith(title):
            summary = summary[len(article.title or ""):].lstrip(" -:|–—.")
        if not summary or summary.lower() == title:
            return "No additional publisher summary was supplied."
        return summary

    @staticmethod
    def _ipo_type(value: str) -> str:
        text = " ".join((value or "").split()).upper()
        if "SME" in text:
            return "SME IPO"
        if "MAIN" in text:
            return "Mainboard IPO"
        return "IPO (classification not published)"

    @staticmethod
    def _news_card_lines(number: int, article) -> list[str]:
        summary = MorningFormatter._compact_summary(article)
        if len(summary) > 360:
            summary = f"{summary[:357].rsplit(' ', 1)[0]}…"
        title = escape(article.title or "Market update")
        source = escape((article.source or "Source not supplied").strip())
        if article.url:
            source = f'<a href="{escape(article.url, quote=True)}">{source}</a>'
        lines = [
            f"<b>{number}. {title}</b>",
            f"   • Summary: {escape(summary)}",
            f"   • Source: {source}",
        ]
        lines.append("")
        return lines

    @staticmethod
    def _health_label(score: int) -> tuple[str, str]:
        if score >= 70:
            return "GOOD", "🟢"
        if score >= 40:
            return "CAUTION", "🟡"
        return "POOR", "🔴"

    @staticmethod
    def _impact_label(score: int) -> tuple[str, str]:
        if score >= 80:
            return "HIGH", "🔴"
        if score >= 55:
            return "MEDIUM", "🟡"
        return "LOW", "⚪"

    @staticmethod
    def _institutional_ledger(
        label: str,
        buy: float | None,
        sell: float | None,
        net: float | None,
    ) -> list[str]:
        if net is None:
            return [f"<b>{label} ACTIVITY</b>", "Data: <code>Not available from NSE</code>"]
        direction_icon = "🟢" if net >= 0 else "🔴"
        buy_text = f"Rs {buy:,.2f} Cr" if buy is not None else "Not published"
        sell_text = f"Rs {sell:,.2f} Cr" if sell is not None else "Not published"
        return [
            f"<b>{label} ACTIVITY</b>",
            f"Gross Buy  : <code>{buy_text}</code>",
            f"Gross Sell : <code>{sell_text}</code>",
            f"Net Flow   : {direction_icon} <code>{net:+,.2f} Cr ₹</code>",
        ]

    @staticmethod
    def _flow_row(
        label: str,
        buy: float | None,
        sell: float | None,
        net: float | None,
    ) -> str:
        if net is None:
            return f"{label:<8}: <code>Not available</code>"
        direction = "NET BUYING" if net >= 0 else "NET SELLING"
        gross = (
            f" | Buy Rs {buy:,.0f} cr | Sell Rs {sell:,.0f} cr"
            if buy is not None and sell is not None else ""
        )
        return f"{label:<8}: <code>Rs {abs(net):,.0f} cr</code> <b>{direction}</b>{gross}"

    @staticmethod
    def _sentiment_emoji(
        value: str,
    ) -> str:

        value = (
            value
            or ""
        ).strip().lower()

        if value == "bullish":
            return "🟢"

        if value == "bearish":
            return "🔴"

        return "🟡"

    @staticmethod
    def _sentiment_animal(value: str) -> str:
        value = (value or "").strip().lower()
        if value == "bullish":
            return "🐂"
        if value == "bearish":
            return "🐻"
        return "🧭"

    # ==========================================================
    # MARKET ROW
    # ==========================================================

    @staticmethod
    def _market_row(index) -> str:

        change = index.percent_change

        if change >= 0:

            icon = "📈"
            arrow = "▲"

        else:

            icon = "📉"
            arrow = "▼"

        name = (
            MorningFormatter._short_index_name(
                index.name
            )
        )

        return (
            f"{icon} "
            f"<b>{escape(name)}</b> : "
            f"<code>{index.value:,.2f}</code> "
            f"({arrow} {abs(change):.2f}%)"
        )

    # ==========================================================
    # SECTOR ROW
    # ==========================================================

    @staticmethod
    def _sector_row(sector) -> str:

        change = sector.percent_change

        if change >= 0:

            arrow = "▲"

        else:

            arrow = "▼"

        name = (
            MorningFormatter._short_sector_name(
                sector.name
            )
        )

        # ------------------------------------------------------
        # Visual spacing
        # ------------------------------------------------------

        dots = "." * max(
            5,
            18 - len(name),
        )

        return (
            f"• <b>{escape(name)}</b> "
            f"<code>{dots}</code> "
            f"({arrow} {abs(change):.2f}%)"
        )

    # ==========================================================
    # STOCK ROW
    # ==========================================================

    @staticmethod
    def _stock_row(
        stock,
        direction: str,
    ) -> str:

        return MorningFormatter._stock_compact_row(stock, direction)

        # Legacy detailed renderer retained below for reference.

        change = stock.percent_change

        if direction == "up":

            icon = "📈"
            arrow = "▲"

        else:

            icon = "📉"
            arrow = "▼"

        name = (
            MorningFormatter._short_stock_name(
                stock.name
            )
        )

        # ------------------------------------------------------
        # Keep stock names aligned
        # ------------------------------------------------------

        name_display = (
            f"{name:<10}"
        )

        return (
            f"{icon} "
            f"<b>{escape(name_display)}</b>"
            f" | "
            f"<code>₹{stock.value:,.2f}</code> "
            f"({arrow} {abs(change):.2f}%)"
        )

    @staticmethod
    def _stock_compact_row(stock, direction: str) -> str:
        """A proportional-monospace-safe mover row for Telegram clients."""
        change = stock.percent_change
        icon = "📈" if direction == "up" else "📉"
        arrow = "▲" if direction == "up" else "▼"
        name = MorningFormatter._short_stock_name(stock.name)
        return f"{icon} <b>{escape(name)}</b> = ₹{stock.value:,.2f} ({arrow} {abs(change):.2f}%)"

    # ==========================================================
    # SHORT INDEX NAMES
    # ==========================================================

    @staticmethod
    def _short_index_name(
        name: str,
    ) -> str:

        mapping = {

            "NIFTY 50": "Nifty 50",
            "NIFTY": "Nifty 50",

            "NIFTY BANK": "BANKNIFTY",
            "BANKNIFTY": "BANKNIFTY",

            "NIFTY FIN SERVICE": "FINNIFTY",
            "NIFTY FIN SERVICE": "FINNIFTY",
            "FINNIFTY": "FINNIFTY",

            "NIFTY MIDCAP SELECT": "Midcap 50",
            "Nifty Midcap 50": "Midcap 50",
            "NIFTY MIDCAP 50": "Midcap 50",

            "NIFTY IT": "Nifty IT",
            "Nifty IT": "Nifty IT",

            "NIFTY PHARMA": "Nifty Pharma",
            "Nifty Pharma": "Nifty Pharma",

            "INDIA VIX": "India VIX",
            "INDIA VIX ": "India VIX",
        }

        cleaned = (
            name
            or ""
        ).strip()

        return mapping.get(
            cleaned,
            cleaned,
        )

    # ==========================================================
    # SHORT SECTOR NAMES
    # ==========================================================

    @staticmethod
    def _short_sector_name(
        name: str,
    ) -> str:

        mapping = {

            "Nifty Pharma": "Pharma",
            "NIFTY PHARMA": "Pharma",

            "Nifty PSU Bank": "PSU Bank",
            "NIFTY PSU BANK": "PSU Bank",

            "Nifty Metal": "Metal",
            "NIFTY METAL": "Metal",

            "Nifty Media": "Media",
            "NIFTY MEDIA": "Media",

            "Nifty Energy": "Energy",
            "NIFTY ENERGY": "Energy",

            "Nifty FMCG": "FMCG",
            "NIFTY FMCG": "FMCG",

            "Nifty Auto": "Auto",
            "NIFTY AUTO": "Auto",

            "Nifty Realty": "Realty",
            "NIFTY REALTY": "Realty",

            "Nifty IT": "IT",
            "NIFTY IT": "IT",
        }

        cleaned = (
            name
            or ""
        ).strip()

        return mapping.get(
            cleaned,
            cleaned.replace(
                "Nifty ",
                "",
            ).replace(
                "NIFTY ",
                "",
            ),
        )

    # ==========================================================
    # SHORT STOCK NAMES
    # ==========================================================

    @staticmethod
    def _short_stock_name(
        name: str,
    ) -> str:

        cleaned = (
            name
            or ""
        ).strip()

        # ------------------------------------------------------
        # Common long names -> compact trading names
        # ------------------------------------------------------

        mapping = {

            "GODREJ CONSUMER": "GODREJCP",
            "GODREJ CONSUMER PRODUCTS": "GODREJCP",

            "PIRAMAL ENTERPRISES": "PIIND",

            "FORTIS HEALTHCARE": "FORTIS",

            "TATA CONSULTANCY SERVICES": "TCS",

            "MAX HEALTHCARE": "MAXHEALTH",

            "BSE LIMITED": "BSE",

            "UNO MINDA": "UNOMINDA",

            "LARSEN & TOUBRO": "LTM",

            "KPIT TECHNOLOGIES": "KPITTECH",

            "POWER INDIA": "POWERINDIA",

            "NATIONAL ALUMINIUM": "NATIONALUM",

            "IDEA": "IDEA",

            "BHARAT HEAVY ELECTRICALS": "BHEL",

            "INDUS TOWERS": "INDUSTOWER",

            "KAYNES TECHNOLOGY": "KAYNES",

            "BOSCH": "BOSCHLTD",
        }

        if cleaned in mapping:

            return mapping[cleaned]

        # ------------------------------------------------------
        # Don't allow extremely long names
        # ------------------------------------------------------

        return cleaned[:12]
