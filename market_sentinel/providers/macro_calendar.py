"""Official US releases that can materially move rates and risk assets."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import re
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup
from loguru import logger


@dataclass(frozen=True, slots=True)
class MacroEvent:
    name: str
    starts_at: datetime
    importance: str
    why_it_matters: str
    source: str
    url: str


class UsMacroCalendarProvider:
    """Combine official Fed, BLS and BEA calendars without manufacturing dates."""

    FED_URL = "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"
    # A harmless query parameter avoids the BLS edge cache returning its HTML
    # denial page for the bare .ics URL on some hosted runners.
    BLS_ICS_URL = "https://www.bls.gov/schedule/news_release/bls.ics?x=1"
    BLS_PAGES = {
        "Consumer Price Index": "https://www.bls.gov/schedule/news_release/cpi.htm",
        "Employment Situation": "https://www.bls.gov/schedule/news_release/empsit.htm",
        "Producer Price Index": "https://www.bls.gov/schedule/news_release/ppi.htm",
        "Job Openings and Labor Turnover": "https://www.bls.gov/schedule/news_release/jolts.htm",
        "Employment Cost Index": "https://www.bls.gov/schedule/news_release/eci.htm",
    }
    BEA_URL = "https://www.bea.gov/news/schedule/full"
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml",
        "Referer": "https://www.bls.gov/schedule/",
    }
    IMPORTANT_BLS = {
        "Consumer Price Index": "Inflation can reprice the expected Federal Reserve path.",
        "Employment Situation": "Payrolls and unemployment can reprice rates and growth expectations.",
        "Producer Price Index": "Pipeline inflation can affect bond yields and margin expectations.",
        "Job Openings and Labor Turnover": "Labour demand is an input to the Fed's employment assessment.",
        "Employment Cost Index": "Wage pressure is relevant to services inflation and Fed policy.",
    }

    def fetch(self, *, now: datetime | None = None, days: int = 45, limit: int = 8) -> list[MacroEvent]:
        now = now or datetime.now(timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
        events: list[MacroEvent] = []
        for label, operation in (
            ("Federal Reserve", self._fetch_fomc),
            ("BLS", self._fetch_bls),
            ("BEA", self._fetch_bea),
        ):
            try:
                events.extend(operation(now))
            except Exception as exc:
                logger.warning("{} macro calendar unavailable: {}", label, exc)
        cutoff = now + timedelta(days=days)
        unique: dict[tuple[str, str], MacroEvent] = {}
        for event in events:
            if now - timedelta(hours=12) <= event.starts_at <= cutoff:
                unique[(event.name.lower(), event.starts_at.date().isoformat())] = event
        return sorted(unique.values(), key=lambda event: event.starts_at)[:limit]

    def _fetch_bls(self, now: datetime) -> list[MacroEvent]:
        response = requests.get(self.BLS_ICS_URL, headers=self.HEADERS, timeout=15)
        if not response.ok or "BEGIN:VEVENT" not in response.text:
            return self._fetch_bls_pages()
        calendar_text = response.text.replace("\r\n", "\n")
        blocks = re.findall(r"BEGIN:VEVENT(.*?)END:VEVENT", calendar_text, re.S)
        output: list[MacroEvent] = []
        for block in blocks:
            summary_match = re.search(r"\nSUMMARY(?:;[^:]*)?:(.+)", "\n" + block)
            date_match = re.search(r"\nDTSTART(?:;[^:]*)?:(\d{8}(?:T\d{6}Z?)?)", "\n" + block)
            if not summary_match or not date_match:
                continue
            summary = summary_match.group(1).replace("\\,", ",").strip()
            matched_name = next((name for name in self.IMPORTANT_BLS if name.lower() in summary.lower()), None)
            if not matched_name:
                continue
            raw = date_match.group(1)
            parsed = datetime.strptime(raw.rstrip("Z"), "%Y%m%dT%H%M%S" if "T" in raw else "%Y%m%d")
            starts_at = parsed.replace(tzinfo=timezone.utc)
            output.append(MacroEvent(
                summary, starts_at, "High", self.IMPORTANT_BLS[matched_name],
                "U.S. Bureau of Labor Statistics", self.BLS_ICS_URL,
            ))
        return output

    def _fetch_bea(self, now: datetime) -> list[MacroEvent]:
        """Read PCE and GDP releases from the official BEA schedule."""
        response = requests.get(self.BEA_URL, headers=self.HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        eastern = ZoneInfo("America/New_York")
        output: list[MacroEvent] = []
        for row in soup.select("tr"):
            cells = [cell.get_text(" ", strip=True) for cell in row.select("th, td")]
            if len(cells) < 3:
                continue
            date_text, title = cells[0], cells[2]
            is_pce = "personal income and outlays" in title.lower()
            is_gdp = title.lower().startswith("gross domestic product,")
            if not (is_pce or is_gdp):
                continue
            match = re.search(
                r"([A-Z][a-z]+)\s+(\d{1,2})\s+(\d{1,2}:\d{2}\s+[AP]M)",
                date_text,
                re.I,
            )
            if not match:
                continue
            month, day, time_text = match.groups()
            local = datetime.strptime(
                f"{month} {day} {now.year} {time_text}", "%B %d %Y %I:%M %p"
            ).replace(tzinfo=eastern)
            name = "PCE inflation / Personal Income and Outlays" if is_pce else "U.S. GDP release"
            why = (
                "Core PCE is the Federal Reserve's preferred inflation gauge and can reprice the policy path."
                if is_pce else
                "Growth data can change rate expectations, bond yields and the earnings outlook."
            )
            output.append(MacroEvent(
                name, local.astimezone(timezone.utc), "High", why,
                "U.S. Bureau of Economic Analysis", self.BEA_URL,
            ))
        return output

    def _fetch_bls_pages(self) -> list[MacroEvent]:
        output: list[MacroEvent] = []
        eastern = ZoneInfo("America/New_York")
        for name, url in self.BLS_PAGES.items():
            response = requests.get(url, headers=self.HEADERS, timeout=12)
            if not response.ok:
                continue
            soup = BeautifulSoup(response.text, "html.parser")
            for row in soup.select("tr"):
                cells = [cell.get_text(" ", strip=True) for cell in row.select("th, td")]
                if len(cells) < 3:
                    continue
                date_text = next((cell for cell in cells if re.search(r"\b[A-Z][a-z]{2}\.\s+\d{1,2},\s+\d{4}\b", cell)), "")
                time_text = next((cell for cell in cells if re.search(r"\b\d{1,2}:\d{2}\s+[AP]M\b", cell, re.I)), "08:30 AM")
                match = re.search(r"([A-Z][a-z]{2})\.\s+(\d{1,2}),\s+(\d{4})", date_text)
                if not match:
                    continue
                month, day, year = match.groups()
                local = datetime.strptime(f"{month} {day} {year} {time_text}", "%b %d %Y %I:%M %p").replace(tzinfo=eastern)
                reference = cells[0] if cells else ""
                output.append(MacroEvent(
                    f"{name} — {reference}", local.astimezone(timezone.utc), "High",
                    self.IMPORTANT_BLS[name], "U.S. Bureau of Labor Statistics", url,
                ))
        return output

    def _fetch_fomc(self, now: datetime) -> list[MacroEvent]:
        response = requests.get(self.FED_URL, headers=self.HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        year = now.year
        heading = soup.find(lambda tag: tag.name == "h4" and f"{year} FOMC Meetings" in tag.get_text(" ", strip=True))
        panel = heading.parent.parent if heading and heading.parent else None
        if panel is None:
            return []
        output: list[MacroEvent] = []
        for row in panel.select(".fomc-meeting"):
            month_node = row.select_one(".fomc-meeting__month")
            date_node = row.select_one(".fomc-meeting__date")
            if not month_node or not date_node:
                continue
            month = month_node.get_text(" ", strip=True)
            days = re.findall(r"\d{1,2}", date_node.get_text(" ", strip=True))
            if not days:
                continue
            decision_day = int(days[-1])
            starts_at = datetime.strptime(f"{year} {month} {decision_day}", "%Y %B %d").replace(hour=18, tzinfo=timezone.utc)
            output.append(MacroEvent(
                "FOMC policy decision", starts_at, "High",
                "The policy statement, rate decision and projections can reprice global risk assets.",
                "Federal Reserve", self.FED_URL,
            ))
        return output
