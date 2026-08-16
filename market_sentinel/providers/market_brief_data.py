"""Market-brief data sources for institutional flows and IPO GMP.

NSE cash-market FII/DII data is the authoritative input.  GMP is inherently
unofficial, so the provider only uses an explicitly configured JSON endpoint
and always retains its source for disclosure in the Telegram brief.
"""

from __future__ import annotations

import os
import re
from datetime import datetime, timedelta
from typing import Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from loguru import logger

from market_sentinel.briefs.models import InvestorFlowSnapshot, IpoGmpSnapshot


class InstitutionalFlowProvider:
    """Fetch FII/FPI and DII cash buy, sell, and net values from NSE."""

    NSE_HOME_URL = "https://www.nseindia.com"
    NSE_ACTIVITY_URL = "https://www.nseindia.com/api/fiidiiTradeReact"
    TIMEOUT_SECONDS = 12

    def __init__(self) -> None:
        self.last_error: str | None = None

    def fetch(self) -> InvestorFlowSnapshot:
        """Return the latest NSE cash flow, or an explicit unavailable state.

        The brief must never silently lose this section just because NSE or a
        third-party package changes.  Values are only displayed when both the
        source and parser succeed.
        """
        try:
            return self._fetch_from_nse()
        except Exception as exc:
            self.last_error = str(exc)
            logger.warning("Unable to fetch NSE FII/DII flow data: {}", exc)
            return InvestorFlowSnapshot(
                trade_date=datetime.now(),
                source="NSE data unavailable",
            )

    def _fetch_from_nse(self) -> InvestorFlowSnapshot:
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-IN,en;q=0.9",
            "Referer": f"{self.NSE_HOME_URL}/reports/fii-dii",
        })
        # Establish NSE cookies before calling the data endpoint.
        session.get(self.NSE_HOME_URL, timeout=self.TIMEOUT_SECONDS)
        response = session.get(self.NSE_ACTIVITY_URL, timeout=self.TIMEOUT_SECONDS)
        response.raise_for_status()
        payload = response.json()
        records = payload.get("data", payload) if isinstance(payload, dict) else payload
        if not isinstance(records, list):
            raise ValueError("NSE FII/DII response has no record list")

        fii = self._values_from_records(records, ("fii", "fpi"))
        dii = self._values_from_records(records, ("dii",))
        if fii is None and dii is None:
            raise ValueError("NSE FII/DII response contains no FII or DII rows")

        date_value = self._record_date(records)
        return InvestorFlowSnapshot(
            trade_date=date_value,
            fii_buy=fii[0] if fii else None,
            fii_sell=fii[1] if fii else None,
            fii_net=fii[2] if fii else None,
            dii_buy=dii[0] if dii else None,
            dii_sell=dii[1] if dii else None,
            dii_net=dii[2] if dii else None,
            source="NSE",
        )

    @classmethod
    def _values_from_records(
        cls,
        records: list[dict[str, Any]],
        category_terms: tuple[str, ...],
    ) -> tuple[float | None, float | None, float | None] | None:
        for record in records:
            category = str(
                record.get("category") or record.get("clientType") or record.get("type") or ""
            ).lower()
            if any(term in category for term in category_terms):
                buy = cls._mapping_number(record, "buyValue", "buy", "purchaseValue")
                sell = cls._mapping_number(record, "sellValue", "sell", "salesValue")
                net = cls._mapping_number(record, "netValue", "net", "netPurchaseSales")
                if net is None and buy is not None and sell is not None:
                    net = buy - sell
                return buy, sell, net
        return None

    @classmethod
    def _record_date(cls, records: list[dict[str, Any]]) -> datetime:
        for record in records:
            for key in ("date", "tradeDate", "timestamp"):
                value = record.get(key)
                if value:
                    parsed = cls._parse_date(value)
                    if parsed:
                        return parsed
        return datetime.now()

    @staticmethod
    def _number(row: Any, *names: str) -> float | None:
        for name in names:
            if name in row.index:
                try:
                    return float(str(row[name]).replace(",", ""))
                except (TypeError, ValueError):
                    return None
        return None

    @staticmethod
    def _mapping_number(record: dict[str, Any], *names: str) -> float | None:
        for name in names:
            if name in record:
                try:
                    return float(str(record[name]).replace(",", ""))
                except (TypeError, ValueError):
                    return None
        return None

    @staticmethod
    def _parse_date(value: Any) -> datetime | None:
        text = str(value).strip()
        for formatter in ("%d-%b-%Y", "%d-%m-%Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(text, formatter)
            except ValueError:
                continue
        return None

    @classmethod
    def _values_for_category(
        cls,
        frame: Any,
        category_terms: tuple[str, ...],
    ) -> tuple[float | None, float | None, float | None] | None:
        """Read a one-row-per-investor table returned by nselib/NSE."""
        columns = {str(column).lower(): column for column in frame.columns}
        category_column = next(
            (original for lowered, original in columns.items() if "category" in lowered or "client" in lowered),
            None,
        )
        if category_column is not None:
            rows = frame[
                frame[category_column].astype(str).str.lower().apply(
                    lambda value: any(term in value for term in category_terms)
                )
            ]
            if not rows.empty:
                row = rows.iloc[-1]
                net = cls._number(row, "Net Value", "Net", "Net Purchase / Sales")
                buy = cls._number(row, "Buy Value", "Buy", "Purchase Value")
                sell = cls._number(row, "Sell Value", "Sell", "Sales Value")
                if net is None and buy is not None and sell is not None:
                    net = buy - sell
                return buy, sell, net
        return None

    @staticmethod
    def _date(row: Any) -> datetime:
        for name in ("Date", "date", "Trade Date"):
            if name in row.index:
                try:
                    return datetime.fromisoformat(str(row[name]))
                except ValueError:
                    pass
        return datetime.now()


class IpoGmpProvider:
    """Fetch current open IPOs and rank them by GMP percentage.

    A configured JSON API takes precedence.  Without one, the provider reads
    InvestorGain's public GMP table and retains only IPOs whose subscription
    window is open today.  GMP is indicative and must never be presented as an
    official exchange price.
    """

    TIMEOUT_SECONDS = 10
    IPO_GURU_URL = "https://www.ipoguru.in/api/v1/ipos?status=open"
    INVESTOR_GAIN_URL = "https://www.investorgain.com/report/ipo-gmp-live/331/"
    IPO_WATCH_URL = "https://ipowatch.in/ipo-grey-market-premium-latest-ipo-gmp/"
    NSE_OPEN_ISSUES_URL = "https://www.nseindia.com/market-data/all-upcoming-issues-ipo"
    # The public page is populated client-side. This is its underlying data
    # feed, so an HTML shell can never be mistaken for "no IPOs".
    NSE_CURRENT_ISSUES_API = "https://www.nseindia.com/api/ipo-current-issue"

    def __init__(self, api_url: str | None = None) -> None:
        self.api_key = os.getenv("IPO_GMP_API_KEY", "").strip()
        self.api_url = api_url or os.getenv("IPO_GMP_API_URL", "").strip()
        if not self.api_url and self.api_key:
            self.api_url = self.IPO_GURU_URL

    def fetch_top(self, limit: int = 5) -> list[IpoGmpSnapshot]:
        if limit <= 0:
            return []
        today = datetime.now()
        gmp_ipos: list[IpoGmpSnapshot] = []
        if self.api_url:
            try:
                headers = {"X-API-KEY": self.api_key} if self.api_key else {}
                response = requests.get(self.api_url, timeout=self.TIMEOUT_SECONDS, headers=headers)
                response.raise_for_status()
                payload = response.json()
                records = payload.get("data", payload) if isinstance(payload, dict) else payload
                gmp_ipos = [ipo for record in records if isinstance(record, dict) if (ipo := self._parse(record)) is not None]
            except (requests.RequestException, ValueError, TypeError) as exc:
                logger.warning("Unable to fetch configured IPO GMP data: {}", exc)
        # These sources are intentionally independent.  A non-empty but stale
        # response from one site must never prevent IPO Watch from supplying
        # the live SME/Mainboard GMP table.
        gmp_ipos = self._dedupe_gmp_sources(
            gmp_ipos,
            self._fetch_investorgain(limit),
            self._fetch_ipowatch(today),
        )

        # GMP is enrichment only. The official current-issue list is always
        # merged, so an open mainboard/SME IPO is never hidden just because an
        # informal grey-market provider is empty or rate-limited.
        official_ipos = self._fetch_nse_open_issues(today)
        merged = self._merge_open_issues(official_ipos, gmp_ipos)
        merged.sort(key=lambda ipo: (
            ipo.gmp_percent is not None,
            ipo.gmp_percent or -1,
            ipo.subscription_close or datetime.max,
        ), reverse=True)
        return merged[:limit]

    @classmethod
    def _dedupe_gmp_sources(cls, *sources: list[IpoGmpSnapshot]) -> list[IpoGmpSnapshot]:
        """Keep the best live GMP row per IPO while retaining provenance."""
        result: dict[str, IpoGmpSnapshot] = {}
        for source in sources:
            for ipo in source:
                key = cls._normalise(ipo.name)
                current = result.get(key)
                if current is None:
                    result[key] = ipo
                    continue
                if (ipo.updated_at or datetime.min) >= (current.updated_at or datetime.min):
                    current.gmp = ipo.gmp
                    current.price_band_high = ipo.price_band_high or current.price_band_high
                    current.issue_type = ipo.issue_type or current.issue_type
                    current.lot_size = ipo.lot_size or current.lot_size
                    current.about = ipo.about or current.about
                    current.details_url = ipo.details_url or current.details_url
                    current.subscription_open = ipo.subscription_open or current.subscription_open
                    current.subscription_close = ipo.subscription_close or current.subscription_close
                if ipo.source and ipo.source not in current.source:
                    current.source = " + ".join(part for part in (current.source, ipo.source) if part)
        return list(result.values())

    @classmethod
    def _merge_open_issues(
        cls,
        official: list[IpoGmpSnapshot],
        gmp_ipos: list[IpoGmpSnapshot],
    ) -> list[IpoGmpSnapshot]:
        by_name = {cls._normalise(ipo.name): ipo for ipo in official}
        for gmp_ipo in gmp_ipos:
            key = cls._normalise(gmp_ipo.name)
            existing = by_name.get(key)
            if existing is None:
                by_name[key] = gmp_ipo
                continue
            existing.gmp = gmp_ipo.gmp
            existing.price_band_high = gmp_ipo.price_band_high or existing.price_band_high
            existing.issue_type = gmp_ipo.issue_type or existing.issue_type
            existing.lot_size = gmp_ipo.lot_size or existing.lot_size
            existing.about = gmp_ipo.about or existing.about
            existing.details_url = gmp_ipo.details_url or existing.details_url
            existing.updated_at = gmp_ipo.updated_at
            existing.source = f"NSE + {gmp_ipo.source}"
        return list(by_name.values())

    def _fetch_nse_open_issues(self, today: datetime) -> list[IpoGmpSnapshot]:
        try:
            session = requests.Session()
            session.headers.update({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Referer": "https://www.nseindia.com/",
            })
            session.get("https://www.nseindia.com", timeout=self.TIMEOUT_SECONDS)
            response = session.get(self.NSE_CURRENT_ISSUES_API, timeout=self.TIMEOUT_SECONDS)
            response.raise_for_status()
            try:
                issues = self._parse_nse_current_issues(response.json(), today)
            except ValueError:
                issues = []
            if issues:
                return issues

            # HTML is only a resilience fallback if NSE changes the JSON API.
            response = session.get(self.NSE_OPEN_ISSUES_URL, timeout=self.TIMEOUT_SECONDS)
            response.raise_for_status()
            issues = self._parse_nse_open_issues_html(response.text, today)
            if not issues:
                logger.warning("NSE returned no current IPO rows for {}", self._next_trading_day(today).date())
            return issues
        except requests.RequestException as exc:
            logger.warning("Unable to fetch NSE current IPO issues: {}", exc)
            return []

    @classmethod
    def _parse_nse_current_issues(cls, payload: Any, today: datetime) -> list[IpoGmpSnapshot]:
        """Parse NSE's current-issue JSON response, including SME offerings."""
        records = payload.get("data", payload) if isinstance(payload, dict) else payload
        if not isinstance(records, list):
            return []

        action_date = cls._next_trading_day(today).date()
        results: dict[str, IpoGmpSnapshot] = {}
        for record in records:
            if not isinstance(record, dict):
                continue
            name = str(
                record.get("companyName")
                or record.get("companyname")
                or record.get("name")
                or record.get("symbol")
                or ""
            ).strip()
            starts = cls._as_nse_date(
                record.get("issueStartDate") or record.get("issueStartDt") or record.get("startDate")
            )
            ends = cls._as_nse_date(
                record.get("issueEndDate") or record.get("issueEndDt") or record.get("endDate")
            )
            if not name or not starts or not ends or not starts.date() <= action_date <= ends.date():
                continue
            status = cls._normalise(str(record.get("status") or record.get("issueStatus") or ""))
            if status and not any(word in status for word in ("open", "current", "live")):
                continue
            price_value = (
                record.get("issuePrice")
                or record.get("priceBand")
                or record.get("price")
                or record.get("upperPrice")
            )
            price = cls._as_float(cls._upper_band(price_value))
            issue_type = str(record.get("issueType") or record.get("category") or record.get("segment") or "").strip()
            lot_size = cls._as_int(record.get("lotSize") or record.get("marketLot") or record.get("lot"))
            results[cls._normalise(name)] = IpoGmpSnapshot(
                name=name,
                gmp=None,
                price_band_high=price,
                issue_type=issue_type,
                lot_size=lot_size,
                subscription_open=starts,
                subscription_close=ends,
                updated_at=today,
                source="NSE current issue feed",
            )
        return list(results.values())

    @classmethod
    def _parse_nse_open_issues_html(cls, html: str, today: datetime) -> list[IpoGmpSnapshot]:
        """Read open Mainboard and SME rows from the public NSE issue table."""
        soup = BeautifulSoup(html, "html.parser")
        results: dict[str, IpoGmpSnapshot] = {}
        action_date = cls._next_trading_day(today).date()
        for table in soup.find_all("table"):
            header_row = table.find("tr")
            header_cells = header_row.find_all(["th", "td"]) if header_row else []
            headers = [cls._normalise(cell.get_text(" ", strip=True)) for cell in header_cells]
            if not any("company name" in header for header in headers):
                continue
            def column(*terms: str) -> int | None:
                return next((index for index, header in enumerate(headers) if any(term in header for term in terms)), None)
            name_idx = column("company name", "company")
            start_idx, end_idx, status_idx = column("issue start", "start date"), column("issue end", "end date"), column("status")
            price_idx = column("price band", "price")
            if None in (name_idx, start_idx, end_idx):
                continue
            for row in table.find_all("tr"):
                cells = [cell.get_text(" ", strip=True) for cell in row.find_all("td")]
                if len(cells) <= max(name_idx, start_idx, end_idx):
                    continue
                status = cls._normalise(cells[status_idx]) if status_idx is not None and len(cells) > status_idx else ""
                starts = cls._as_nse_date(cells[start_idx])
                ends = cls._as_nse_date(cells[end_idx])
                if not starts or not ends or not starts.date() <= action_date <= ends.date():
                    continue
                if status and "open" not in status and "current" not in status:
                    continue
                name = cells[name_idx].strip()
                if not name:
                    continue
                price = cls._as_float(cls._upper_band(cells[price_idx])) if price_idx is not None and len(cells) > price_idx else None
                results[cls._normalise(name)] = IpoGmpSnapshot(
                    name=name, gmp=None, price_band_high=price,
                    subscription_open=starts, subscription_close=ends,
                    updated_at=today, source="NSE official issue list",
                )
        return list(results.values())

    def _fetch_investorgain(self, limit: int) -> list[IpoGmpSnapshot]:
        """Read InvestorGain's visible table; no API key is required."""
        try:
            response = requests.get(
                self.INVESTOR_GAIN_URL,
                timeout=self.TIMEOUT_SECONDS,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122 Safari/537.36",
                    "Accept-Language": "en-IN,en;q=0.9",
                },
            )
            response.raise_for_status()
            today = datetime.now()
            ipos = self._parse_investorgain_html(response.text, today=today)
            logger.info("InvestorGain returned {} qualifying open IPO rows", len(ipos))
            ipos.sort(key=lambda ipo: (ipo.gmp_percent is not None, ipo.gmp_percent or ipo.gmp or -1), reverse=True)
            return ipos[:limit]
        except (requests.RequestException, ValueError, TypeError) as exc:
            logger.warning("Unable to fetch InvestorGain IPO GMP data: {}", exc)
            return []

    def _fetch_ipowatch(self, today: datetime) -> list[IpoGmpSnapshot]:
        try:
            session = requests.Session()
            session.headers.update({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": "en-IN,en-US;q=0.9,en;q=0.8",
                "Referer": "https://ipowatch.in/",
            })
            # Establish the same first-party session a browser uses. This
            # avoids a sparse anti-bot response which otherwise looks like an
            # empty IPO table.
            try:
                session.get("https://ipowatch.in/", timeout=self.TIMEOUT_SECONDS)
            except requests.RequestException:
                # The actual GMP page is still worth trying if the landing
                # page is temporarily unavailable.
                pass
            response = session.get(self.IPO_WATCH_URL, timeout=self.TIMEOUT_SECONDS)
            response.raise_for_status()
            ipos = self._parse_ipowatch_html(response.text, today)
            self._enrich_ipowatch_details(ipos, session)
            logger.info("IPO Watch returned {} qualifying open IPO rows", len(ipos))
            return ipos
        except requests.RequestException as exc:
            logger.warning("Unable to fetch IPO Watch GMP data: {}", exc)
            return []

    @classmethod
    def _parse_investorgain_html(cls, html: str, today: datetime) -> list[IpoGmpSnapshot]:
        """Extract open IPO rows from InvestorGain's GMP table.

        Header matching instead of fixed column positions keeps this resilient
        when the site adds subscription, lot-size, or listing-date columns.
        """
        soup = BeautifulSoup(html, "html.parser")
        results: dict[str, IpoGmpSnapshot] = {}
        for table in soup.find_all("table"):
            header_row = table.find("tr")
            header_cells = header_row.find_all(["th", "td"]) if header_row else []
            headers = [cls._normalise(cell.get_text(" ", strip=True)) for cell in header_cells]
            if not headers or not any("gmp" in header for header in headers):
                continue
            def column(*terms: str) -> int | None:
                return next((idx for idx, header in enumerate(headers) if any(term in header for term in terms)), None)

            name_idx = column("ipo name", "company", "ipo")
            gmp_idx = column("gmp")
            price_idx = column("price", "issue price")
            type_idx = column("type", "segment", "exchange")
            lot_idx = column("lot size", "lot")
            open_idx = column("open date", "open")
            close_idx = column("close date", "close")
            if name_idx is None or gmp_idx is None or open_idx is None or close_idx is None:
                continue
            for row in table.find_all("tr"):
                cell_tags = row.find_all("td")
                cells = [cell.get_text(" ", strip=True) for cell in cell_tags]
                if len(cells) <= max(name_idx, gmp_idx, open_idx, close_idx):
                    continue
                name = cells[name_idx].strip()
                gmp = cls._extract_number(cells[gmp_idx])
                opens = cls._as_investorgain_date(cells[open_idx], today.year)
                closes = cls._as_investorgain_date(cells[close_idx], today.year)
                if not name or gmp is None or opens is None or closes is None:
                    continue
                if not opens.date() <= cls._next_trading_day(today).date() <= closes.date():
                    continue
                price = cls._extract_number(cells[price_idx]) if price_idx is not None and len(cells) > price_idx else None
                issue_type = cells[type_idx] if type_idx is not None and len(cells) > type_idx else ""
                lot_size = cls._as_int(cells[lot_idx]) if lot_idx is not None and len(cells) > lot_idx else None
                key = cls._normalise(name)
                results[key] = IpoGmpSnapshot(
                    name=name,
                    gmp=gmp,
                    price_band_high=price,
                    issue_type=issue_type,
                    lot_size=lot_size,
                    subscription_open=opens,
                    subscription_close=closes,
                    updated_at=today,
                    source="InvestorGain",
                )
        return list(results.values())

    @classmethod
    def _parse_ipowatch_html(cls, html: str, today: datetime) -> list[IpoGmpSnapshot]:
        """Parse IPO Watch's public GMP table and retain only ``Open`` rows."""
        soup = BeautifulSoup(html, "html.parser")
        results: dict[str, IpoGmpSnapshot] = {}
        for table in soup.find_all("table"):
            header_row = table.find("tr")
            header_cells = header_row.find_all(["th", "td"]) if header_row else []
            headers = [cls._normalise(cell.get_text(" ", strip=True)) for cell in header_cells]
            def column(*terms: str) -> int | None:
                return next((idx for idx, header in enumerate(headers) if any(term in header for term in terms)), None)

            name_idx, gmp_idx = column("ipo name", "ipo"), column("ipo gmp", "gmp")
            price_idx, date_idx, status_idx = column("price band", "price"), column("date"), column("status")
            type_idx, lot_idx = column("type", "segment", "exchange"), column("lot size", "lot")
            # IPO Watch's published layout is stable (name, GMP, trend,
            # price, estimated listing, date, type, status). Use it when a
            # CDN/browser variant omits readable header cells.
            if not headers or not any("ipo gmp" in header or header == "gmp" for header in headers):
                name_idx, gmp_idx, price_idx, date_idx, type_idx, status_idx = 0, 1, 3, 5, 6, 7
            if name_idx is None or gmp_idx is None or date_idx is None:
                continue
            for row in table.find_all("tr"):
                cell_tags = row.find_all("td")
                cells = [cell.get_text(" ", strip=True) for cell in cell_tags]
                required = (name_idx, gmp_idx, date_idx)
                if len(cells) <= max(required):
                    continue
                # Subscription dates determine inclusion. They work even when
                # a source uses an icon/status badge instead of readable text
                # and correctly keep IPOs available on the next market day.
                dates = cls._date_range(cells[date_idx], today.year)
                if dates is None or not dates[0].date() <= cls._next_trading_day(today).date() <= dates[1].date():
                    continue
                gmp = cls._extract_number(cells[gmp_idx])
                name = cells[name_idx].strip()
                if not name or gmp is None:
                    continue
                price = cls._extract_number(cells[price_idx]) if price_idx is not None and len(cells) > price_idx else None
                issue_type = cells[type_idx] if type_idx is not None and len(cells) > type_idx else ""
                lot_size = cls._as_int(cells[lot_idx]) if lot_idx is not None and len(cells) > lot_idx else None
                detail_link = cell_tags[name_idx].find("a", href=True) if len(cell_tags) > name_idx else None
                details_url = urljoin(cls.IPO_WATCH_URL, detail_link["href"]) if detail_link else ""
                results[cls._normalise(name)] = IpoGmpSnapshot(
                    name=name, gmp=gmp, price_band_high=price,
                    issue_type=issue_type, lot_size=lot_size, details_url=details_url,
                    subscription_open=dates[0], subscription_close=dates[1],
                    updated_at=today, source="IPO Watch",
                )
        return list(results.values())

    def _enrich_ipowatch_details(self, ipos: list[IpoGmpSnapshot], session: requests.Session) -> None:
        """Fill lot size and a one-line business description from IPO Watch issue pages."""
        for ipo in ipos[:10]:
            if not ipo.details_url:
                continue
            try:
                response = session.get(ipo.details_url, timeout=self.TIMEOUT_SECONDS)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "html.parser")
                text = soup.get_text(" ", strip=True).replace("\xa0", " ")
                lot_match = re.search(
                    r"minimum (?:market )?lot (?:is|of)?\s*([\d,]+)\s*shares.*?(?:₹|Rs\.?)[\s]*([\d,]+)",
                    text,
                    flags=re.IGNORECASE,
                )
                if lot_match:
                    ipo.lot_size = self._as_int(lot_match.group(1)) or ipo.lot_size
                # Some pages embed unrelated recommended-IPO articles before
                # the issue content. Match the heading to this IPO's name so
                # a description is never copied from another company.
                name_terms = self._normalise(ipo.name).replace(" ipo", "").split()[:2]
                about_heading = next(
                    (
                        tag for tag in soup.find_all(["h2", "h3", "h4"])
                        if tag.get_text(" ", strip=True).lower().startswith("about ")
                        and all(term in self._normalise(tag.get_text(" ", strip=True)) for term in name_terms)
                    ),
                    None,
                )
                if about_heading:
                    paragraph = about_heading.find_next("p")
                    if paragraph:
                        ipo.about = " ".join(paragraph.get_text(" ", strip=True).split())
            except requests.RequestException as exc:
                logger.debug("IPO detail page unavailable for {}: {}", ipo.name, exc)

    def _parse(self, record: dict[str, Any]) -> IpoGmpSnapshot | None:
        name = str(record.get("name") or record.get("ipo_name") or "").strip()
        gmp_payload = record.get("gmp")
        gmp = self._as_float(
            gmp_payload.get("price") if isinstance(gmp_payload, dict)
            else gmp_payload or record.get("grey_market_premium")
        )
        if not name or gmp is None:
            return None
        close = self._as_date(record.get("subscription_close") or record.get("close_date"))
        updated = self._as_date(
            gmp_payload.get("updated_at") if isinstance(gmp_payload, dict)
            else record.get("gmp_updated_at")
        )
        return IpoGmpSnapshot(
            name=name,
            gmp=gmp,
            price_band_high=self._as_float(
                record.get("price_band_high")
                or record.get("upper_price")
                or record.get("issue_price")
                or self._upper_band(record.get("price_band"))
            ),
            issue_type=str(record.get("issue_type") or record.get("type") or record.get("segment") or "").strip(),
            lot_size=self._as_int(record.get("lot_size") or record.get("lot") or record.get("market_lot")),
            about=str(record.get("about") or record.get("description") or "").strip(),
            subscription_open=self._as_date(record.get("subscription_open") or record.get("open_date")),
            subscription_close=close,
            updated_at=updated,
            source=str(record.get("source") or self.api_url),
        )

    @staticmethod
    def _as_float(value: Any) -> float | None:
        try:
            cleaned = str(value).replace(",", "").replace("₹", "").strip()
            return float(cleaned)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _as_int(value: Any) -> int | None:
        number = IpoGmpProvider._extract_number(str(value))
        return int(number) if number is not None and number > 0 else None

    @staticmethod
    def _normalise(value: str) -> str:
        return " ".join(value.lower().split())

    @staticmethod
    def _extract_number(value: str) -> float | None:
        match = re.search(r"-?\d[\d,]*(?:\.\d+)?", value.replace("₹", ""))
        if not match:
            return None
        try:
            return float(match.group(0).replace(",", ""))
        except ValueError:
            return None

    @staticmethod
    def _as_investorgain_date(value: str, year: int) -> datetime | None:
        cleaned = re.sub(r"\s+", " ", value).strip().replace("-", " ")
        for pattern in ("%d %b", "%d %B"):
            try:
                # Supplying a year directly avoids Python 3.15's ambiguous
                # day/month-without-a-year parsing behaviour.
                return datetime.strptime(f"{cleaned} {year}", f"{pattern} %Y")
            except ValueError:
                continue
        return None

    @classmethod
    def _date_range(cls, value: str, year: int) -> tuple[datetime, datetime] | None:
        # Strip the ordinal markup used in live table cells, e.g.
        # "14th - 18th August", before handling standard date ranges.
        cleaned = str(value).replace("\xa0", " ")
        cleaned = re.sub(r"(?<=\d)\s*(?:st|nd|rd|th)\b", "", cleaned, flags=re.I)
        cleaned = cleaned.replace("–", "-").replace("—", "-")
        parts = re.findall(r"\d{1,2}\s*[- ]\s*[A-Za-z]+", cleaned)
        if len(parts) >= 2:
            start = cls._as_investorgain_date(parts[0], year)
            end = cls._as_investorgain_date(parts[1], year)
            if start and end:
                return start, end
        # IPO Watch commonly writes e.g. "22-24 July".
        value = cleaned
        match = re.search(r"(\d{1,2})\s*[-–]\s*(\d{1,2})\s+([A-Za-z]+)", value)
        if match:
            start = cls._as_investorgain_date(f"{match.group(1)} {match.group(3)}", year)
            end = cls._as_investorgain_date(f"{match.group(2)} {match.group(3)}", year)
            if start and end:
                return start, end
        month_first = re.search(r"([A-Za-z]+)\s+(\d{1,2})\s*[-]\s*(\d{1,2})", cleaned)
        if month_first:
            start = cls._as_investorgain_date(f"{month_first.group(2)} {month_first.group(1)}", year)
            end = cls._as_investorgain_date(f"{month_first.group(3)} {month_first.group(1)}", year)
            if start and end:
                return start, end
        return None

    @staticmethod
    def _next_trading_day(value: datetime) -> datetime:
        """Use the next weekday so Friday/weekend runs retain live open IPOs."""
        candidate = value
        while candidate.weekday() >= 5:
            candidate += timedelta(days=1)
        return candidate

    @staticmethod
    def _as_nse_date(value: str) -> datetime | None:
        if not value:
            return None
        cleaned = " ".join(str(value).replace("-", " ").replace("/", " ").split())
        for pattern in ("%d %b %Y", "%d %B %Y", "%d %b %y", "%Y %m %d", "%d %m %Y"):
            try:
                return datetime.strptime(cleaned, pattern)
            except ValueError:
                continue
        return None

    @staticmethod
    def _as_date(value: Any) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(str(value))
        except ValueError:
            return None

    @staticmethod
    def _upper_band(value: Any) -> str | None:
        if not value:
            return None
        return re.split(r"[-–—]", str(value))[-1].strip()
