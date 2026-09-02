"""Orchestrates the five-stock daily options research scan."""

from __future__ import annotations

from dataclasses import replace
from html import escape
import os

from market_sentinel.research.options.events import MarketEventProvider
from market_sentinel.research.options.models import FALLBACK_LIQUID_OPTIONS_UNIVERSE, OptionResearchSetup
from market_sentinel.research.options.providers import (
    AngelOneOptionChainProvider,
    NseOptionChainProvider,
    NseActiveFnoProvider,
    SnapshotStore,
    YahooTechnicalProvider,
)
from market_sentinel.research.options.scanner import OptionResearchScanner


class DailyOptionsRadarService:
    """Fetch, persist, rank, and format the daily private options radar."""

    def __init__(self) -> None:
        self.chain_provider = NseOptionChainProvider()
        self.universe_provider = NseActiveFnoProvider()
        self.angel_chain_provider = AngelOneOptionChainProvider()
        self.technical_provider = YahooTechnicalProvider()
        self.store = SnapshotStore()
        self.scanner = OptionResearchScanner()
        self.event_provider = MarketEventProvider()
        self.last_watchlist = ()

    def run(self) -> tuple[list[OptionResearchSetup], list[str]]:
        setups: list[OptionResearchSetup] = []
        failures: list[str] = []
        try:
            watchlist = self.universe_provider.fetch_top(limit=5)
        except Exception as exc:
            watchlist = FALLBACK_LIQUID_OPTIONS_UNIVERSE
            failures.append(f"Active F&O universe: {exc}; used labelled fallback")
        self.last_watchlist = tuple(watchlist)
        for item in watchlist:
            try:
                technicals = self.technical_provider.fetch(item)
                previous_chain = self.store.previous_session_eod(item.symbol)
                try:
                    chain = self.chain_provider.fetch(item.nse_option_symbol)
                except Exception:
                    chain = self.angel_chain_provider.fetch(item.symbol, technicals.close)
                self.store.save(chain, kind=os.getenv("MARKET_SENTINEL_SNAPSHOT_KIND", "live"))
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
        return setups[:5], failures

    @staticmethod
    def format_messages(setups: list[OptionResearchSetup], failures: list[str]) -> list[str]:
        header = (
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📊 TOP 5 LIQUID F&O NAMES — RESEARCH RADAR\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Tracked liquid F&O universe; evidence scan, not a trade recommendation.\n"
        )
        lines = [header.rstrip(), ""]
        for number, setup in enumerate(setups, start=1):
            pcr = f"{setup.pcr:.2f}" if setup.pcr is not None else "N/A"
            support = f"₹{setup.support:,.0f}" if setup.support else "No verified put OI base below spot"
            resistance = f"₹{setup.resistance:,.0f}" if setup.resistance else "No verified call OI wall above spot"
            bias = setup.bias.replace(" option-chain setup", "")
            event = setup.market_events[0] if setup.market_events else None
            event_line = ""
            if event:
                event_title = escape(event.title[:100])
                if event.url:
                    event_title = f'<a href="{escape(event.url, quote=True)}">{event_title}</a>'
                event_line = f"\n   Event: [{escape(event.severity)}] {event_title}"
            oi_comparison = next((item for item in setup.evidence if item.startswith(("OI vs", "Previous EOD"))), "Previous EOD snapshot unavailable")
            live_oi = next((item for item in setup.evidence if "OI build-up" in item), "No dominant live OI build-up")
            trend = next((item for item in setup.evidence if item.startswith(("Price is", "EMA 20"))), setup.evidence[0] if setup.evidence else "Mixed evidence")
            spot = setup.chain.spot_price or setup.technicals.close
            lines.extend((
                f"<blockquote><b>{number}. {escape(setup.display_name)} — {escape(bias)}</b>",
                f"Spot ₹{spot:,.2f} | PCR {pcr} | Confidence {setup.confidence_score}/100",
                f"S/R {support} / {resistance} | Expiry {escape(setup.chain.expiry)}",
                f"Why: {escape(trend)}; {escape(live_oi)}",
                f"OI: {escape(oi_comparison)}{event_line}",
                f"Invalidation: {escape(setup.invalidation)}</blockquote>",
                "",
            ))
        if failures:
            lines.append("<i>Data notes: " + escape("; ".join(failures[:3])) + "</i>")
        lines.append("<i>Previous EOD OI and live OI changes are used when a verified EOD snapshot exists. Research only; not a trade recommendation.</i>")
        return ["\n".join(lines)]
