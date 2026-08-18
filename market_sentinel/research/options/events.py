"""Sourced event and headline context for private option research.

Nothing is labelled as an insider event unless it comes from an official NSE
announcement.  RSS headlines are contextual only and never treated as facts
until a primary disclosure is available.
"""

from __future__ import annotations

from html import unescape
from urllib.parse import quote_plus

import feedparser
import requests

from market_sentinel.research.options.models import MarketEvent, WatchlistItem


class MarketEventProvider:
    NSE_HOME_URL = "https://www.nseindia.com"
    NSE_ANNOUNCEMENTS_URL = "https://www.nseindia.com/api/corporate-announcements"

    HIGH_RISK_TERMS = (
        "results", "earnings", "financial result", "board meeting", "merger", "acquisition", "buyback",
        "pledge", "resignation", "change in management", "penalty", "insider", "bulk deal", "block deal",
        "news verification", "regulatory", "investigation", "credit rating downgrade",
    )
    LOW_RISK_TERMS = ("esop", "esos", "esps", "newspaper publication", "general updates")
    NON_MATERIAL_HEADLINE_TERMS = (
        "share price", "stock price", "live nse", "live bse", "stock chart", "today -", "buy, sell or hold",
        "buy the dip", "target price", "technical analysis", "forecast",
    )

    def fetch(self, item: WatchlistItem, limit: int = 3) -> tuple[MarketEvent, ...]:
        events = self._official_announcements(item)
        events.extend(self._news_headlines(item))
        unique: list[MarketEvent] = []
        seen: set[str] = set()
        for event in events:
            key = event.title.casefold()
            if key and key not in seen:
                unique.append(event)
                seen.add(key)
            if len(unique) >= limit:
                break
        return tuple(unique)

    def _official_announcements(self, item: WatchlistItem) -> list[MarketEvent]:
        try:
            session = requests.Session()
            session.headers.update({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36",
                "Accept": "application/json, text/plain, */*",
                "Referer": "https://www.nseindia.com/companies-listing/corporate-filings-announcements",
            })
            session.get(self.NSE_HOME_URL, timeout=8)
            response = session.get(self.NSE_ANNOUNCEMENTS_URL, params={"index": "equities", "symbol": item.symbol}, timeout=8)
            response.raise_for_status()
            rows = response.json() or []
            if not isinstance(rows, list):
                return []
            output: list[MarketEvent] = []
            for row in rows[:3]:
                symbol = str(row.get("symbol") or "").upper().strip()
                # NSE's endpoint is expected to filter by symbol, but validate
                # it before publication in case the upstream filter changes.
                if symbol != item.symbol.upper():
                    continue
                description = str(row.get("desc") or "").strip()
                details = _compact(str(row.get("attchmntText") or row.get("subject") or ""))
                title = _filing_title(description, details)
                if not title or self._severity(f"{description} {details}") == "Low" and not self._is_material_filing(description, details):
                    continue
                attachment = str(row.get("attchmntFile") or row.get("attchmntFileName") or "")
                url = attachment if attachment.startswith("http") else ""
                combined = f"{description} {details}"
                output.append(MarketEvent(
                    title=title, source="NSE corporate announcement", url=url,
                    severity=self._severity(combined), category="Exchange filing",
                    impact=self._impact(combined),
                ))
            return output
        except Exception:
            return []

    def _news_headlines(self, item: WatchlistItem) -> list[MarketEvent]:
        try:
            query = quote_plus(f'"{item.display_name}" shares India')
            feed = feedparser.parse(f"https://news.google.com/rss/search?q={query}+when:3d&hl=en-IN&gl=IN&ceid=IN:en")
            output: list[MarketEvent] = []
            for entry in feed.entries[:5]:
                title = unescape(str(entry.get("title") or "")).strip()
                if title and self._is_material_headline(title):
                    output.append(MarketEvent(
                        title=title, source="Google News (publisher headline)",
                        url=str(entry.get("link") or ""), severity=self._severity(title), category="News",
                        impact=self._impact(title),
                    ))
            return output
        except Exception:
            return []

    def _severity(self, text: str) -> str:
        lowered = text.casefold()
        if any(term in lowered for term in self.HIGH_RISK_TERMS):
            return "High"
        if any(term in lowered for term in self.LOW_RISK_TERMS):
            return "Low"
        return "Medium"

    def _is_material_filing(self, description: str, details: str) -> bool:
        text = f"{description} {details}".casefold()
        return any(term in text for term in self.HIGH_RISK_TERMS + (
            "credit rating", "investor meet", "conference call", "allotment of securities", "dividend",
            "order", "contract", "litigation", "fund raising",
        ))

    def _is_material_headline(self, title: str) -> bool:
        lowered = title.casefold()
        if any(term in lowered for term in self.NON_MATERIAL_HEADLINE_TERMS):
            return False
        return any(term in lowered for term in self.HIGH_RISK_TERMS + (
            "credit rating", "order", "contract", "guidance", "revenue", "profit", "loss", "stake",
            "dividend", "fund raise", "fundraising", "debt", "litigation",
        ))

    @staticmethod
    def _impact(text: str) -> str:
        lowered = text.casefold()
        if any(term in lowered for term in ("resignation", "change in management", "investigation", "penalty", "pledge")):
            return "Governance or regulatory risk — verify the filing details"
        if any(term in lowered for term in ("results", "earnings", "financial result", "board meeting")):
            return "Potential earnings/guidance volatility"
        if "credit rating" in lowered:
            return "Funding-cost and credit-perception risk"
        if any(term in lowered for term in ("allotment", "esop", "esos", "fund raising")):
            return "Potential dilution or capital-structure impact"
        if any(term in lowered for term in ("investor meet", "conference call")):
            return "Management commentary or guidance risk"
        if any(term in lowered for term in ("order", "contract", "acquisition", "merger")):
            return "Potential operating or valuation catalyst"
        return "Verify the disclosure and assess company-specific relevance"


def _compact(text: str) -> str:
    return " ".join(unescape(text).split())


def _filing_title(description: str, details: str) -> str:
    if details:
        return details[:220].rstrip(" .")
    return description[:220].rstrip(" .")
