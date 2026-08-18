"""Orchestrates the ten-stock daily options research scan."""

from __future__ import annotations

from dataclasses import replace
from html import escape

from market_sentinel.research.options.events import MarketEventProvider
from market_sentinel.research.options.models import DEFAULT_OPTIONS_WATCHLIST, OptionResearchSetup
from market_sentinel.research.options.providers import (
    AngelOneOptionChainProvider,
    NseOptionChainProvider,
    SnapshotStore,
    YahooTechnicalProvider,
)
from market_sentinel.research.options.scanner import OptionResearchScanner


class DailyOptionsRadarService:
    """Fetch, persist, rank, and format the daily private options radar."""

    def __init__(self) -> None:
        self.chain_provider = NseOptionChainProvider()
        self.angel_chain_provider = AngelOneOptionChainProvider()
        self.technical_provider = YahooTechnicalProvider()
        self.store = SnapshotStore()
        self.scanner = OptionResearchScanner()
        self.event_provider = MarketEventProvider()

    def run(self) -> tuple[list[OptionResearchSetup], list[str]]:
        setups: list[OptionResearchSetup] = []
        failures: list[str] = []
        for item in DEFAULT_OPTIONS_WATCHLIST:
            try:
                technicals = self.technical_provider.fetch(item)
                previous_chain = self.store.latest(item.symbol)
                try:
                    chain = self.chain_provider.fetch(item.nse_option_symbol)
                except Exception:
                    chain = self.angel_chain_provider.fetch(item.symbol, technicals.close)
                self.store.save(chain)
                setup = self.scanner.analyze(item, chain, technicals, previous_chain=previous_chain)
                events = self.event_provider.fetch(item)
                if events:
                    high_risk = sum(event.severity == "High" for event in events)
                    setup = replace(
                        setup,
                        market_events=events,
                        confidence_score=max(0, setup.confidence_score - high_risk * 5),
                        risk_notes=setup.risk_notes + ("Company-specific event/headline context is listed below",),
                    )
                setups.append(setup)
            except Exception as exc:
                failures.append(f"{item.symbol}: {exc}")
        # Volume ranks the tracked liquid F&O universe; confidence is the
        # tie-breaker.  Never imply that this is the entire derivatives market.
        setups.sort(
            key=lambda setup: (sum(item.volume for item in setup.chain.contracts), setup.confidence_score),
            reverse=True,
        )
        return setups, failures

    @staticmethod
    def format_messages(setups: list[OptionResearchSetup], failures: list[str]) -> list[str]:
        header = (
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📊 TOP 10 LIQUID F&O NAMES — OPTION VOLUME RANKED\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Tracked liquid F&O universe; evidence scan, not a trade recommendation.\n"
        )
        messages = [header]
        for number, setup in enumerate(setups, start=1):
            pcr = f"{setup.pcr:.2f}" if setup.pcr is not None else "N/A"
            support = f"₹{setup.support:,.0f}" if setup.support else "No verified put OI base below spot"
            resistance = f"₹{setup.resistance:,.0f}" if setup.resistance else "No verified call OI wall above spot"
            evidence = "\n".join(f"• {item}" for item in setup.evidence)
            risks = "\n".join(f"• {item}" for item in setup.risk_notes)
            events = "\n".join(
                f"• [{escape(event.severity)}] {escape(event.category)}: "
                + (f'<a href="{escape(event.url, quote=True)}">{escape(event.title)}</a>' if event.url else escape(event.title))
                + f"\n  Impact: {escape(event.impact)} — {escape(event.source)}"
                for event in setup.market_events
            ) or "• No verified company-specific event returned in this run"
            messages.append(
                "<blockquote>\n"
                f"{number}. <b>{escape(setup.display_name)}</b> — {escape(setup.bias)}\n"
                f"Confidence: {setup.confidence_score}/100 | PCR: {pcr}\n\n"
                f"Evidence:\n{evidence}\n\n"
                f"Key zones:\n• Support: {support}\n• Resistance: {resistance}\n\n"
                f"Event & news context:\n{events}\n\n"
                f"Risk:\n• {setup.invalidation}\n{risks}\n\n"
                f"Data: {setup.data_quality} | {setup.source}\n"
                "This is market analysis, not a trade recommendation.\n"
                "</blockquote>"
            )
        if failures:
            messages.append("Data unavailable for: " + "; ".join(failures))
        return messages
