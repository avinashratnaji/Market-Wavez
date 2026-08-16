"""
telegram/formatter.py

Formats Market Sentinel broadcasts.

Author : Market Sentinel
Version : 1.0.0
"""

from __future__ import annotations

from market_sentinel.briefs.models import (
    MorningBrief,
    # MarketIndex,
    # Catalyst,
    # Commodity,
    # StockWatch,
    # Risk,
)


class BroadcastFormatter:

    LINE = "━━━━━━━━━━━━━━━━━━━━━━"

    @staticmethod
    def _emoji(change: float) -> str:
        if change > 0:
            return "🟢"
        if change < 0:
            return "🔴"
        return "🟡"

    @staticmethod
    def _arrow(change: float) -> str:
        if change > 0:
            return "▲"
        if change < 0:
            return "▼"
        return "■"

    @classmethod
    def morning(cls, brief: MorningBrief) -> str:

        lines = []

        lines.append(cls.LINE)
        lines.append("🌍 <b>DAILY MARKET BRIEF</b>")
        lines.append(f"📅 {brief.generated_at}")
        lines.append(cls.LINE)
        lines.append("")

        lines.append(
            f"📊 <b>MARKET HEALTH:</b> {cls._health(brief.market_health_score)} ({brief.market_health_score}/100)"
        )

        lines.append(
            f"📈 Overall Sentiment: {brief.overall_sentiment}"
        )

        lines.append(
            f"(India: {brief.india_sentiment} | "
            f"US: {brief.us_sentiment} | "
            f"Crypto: {brief.crypto_sentiment})"
        )

        lines.append("")
        lines.append("🔥 <b>TOP CATALYSTS TODAY</b>")
        lines.append("")

        for i, catalyst in enumerate(brief.catalysts, start=1):
            lines.append(f"{i}. {catalyst.title}")
            lines.append(f"↳ {catalyst.impact}")
            lines.append("")

        lines.append(cls.LINE)
        lines.append("🇮🇳 <b>INDIAN MARKETS</b>")
        lines.append(cls.LINE)

        for market in brief.indian_markets:

            emoji = cls._emoji(market.change_percent)
            arrow = cls._arrow(market.change_percent)

            line = (
                f"{emoji} {market.name:<15}"
                f"{market.value:,.2f} | "
                f"{arrow} {market.change_percent:+.2f}%"
            )

            if market.volume and market.volume > 1:
                line += f" (Vol {market.volume:.2f}x)"

            lines.append(line)

        lines.append("")
        lines.append(cls.LINE)
        lines.append("🌍 <b>GLOBAL DESK</b>")
        lines.append(cls.LINE)

        for market in brief.global_markets:

            emoji = cls._emoji(market.change_percent)
            arrow = cls._arrow(market.change_percent)

            lines.append(
                f"{emoji} {market.name:<15}"
                f"{market.value:,.2f} | "
                f"{arrow} {market.change_percent:+.2f}%"
            )

        lines.append("")
        lines.append("🛢️ <b>COMMODITIES</b>")

        for item in brief.commodities:

            emoji = cls._emoji(item.change_percent)

            lines.append(
                f"{emoji} {item.name}: "
                f"{item.change_percent:+.2f}% "
                f"({item.comment})"
            )

        lines.append("")
        lines.append(cls.LINE)
        lines.append("🎯 <b>RADAR & STRATEGY</b>")
        lines.append(cls.LINE)

        lines.append("👀 <b>Stocks to Watch</b>")

        if brief.stocks_to_watch:

            for stock in brief.stocks_to_watch:
                lines.append(f"🟢 <b>{stock.symbol}</b>")
                lines.append(f"   ↳ {stock.reason}")

        else:

            lines.append("No stocks identified.")

        lines.append("")
        lines.append("⚠️ <b>Key Risks</b>")

        if brief.risks:

            for risk in brief.risks:
                lines.append(f"⚠ {risk.description}")

        else:

            lines.append("No major risks detected.")

        lines.append("")
        lines.append("💡 <b>Today's Playbook</b>")
        lines.append(brief.playbook)

        lines.append("")
        lines.append(cls.LINE)
        lines.append("<i>Powered by Market Wavez Analytics ⚡</i>")

        return "\n".join(lines)

    @staticmethod
    def _health(score: int):

        if score >= 80:
            return "🟢 Excellent"

        if score >= 65:
            return "🟢 Healthy"

        if score >= 50:
            return "🟡 Neutral"

        if score >= 35:
            return "🟠 Weak"

        return "🔴 Poor"