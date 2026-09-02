"""Multi-factor, source-attributed equity research evidence for public screens.

This module deliberately does not create trade calls.  It turns reported
financials, ownership data, price structure and verifiable company news into
an inspectable research ledger; missing or stale evidence lowers confidence.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
import re
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

from market_sentinel.news.models import NewsArticle


@dataclass(frozen=True, slots=True)
class PremiumEquityAssessment:
    symbol: str
    company_name: str
    composite_score: int
    growth_score: int
    quality_score: int
    ownership_score: int
    technical_score: int
    catalyst_score: int
    risk_score: int
    confidence: int
    strengths: tuple[str, ...]
    risks: tuple[str, ...]
    data_gaps: tuple[str, ...]
    metrics: tuple[str, ...]
    report_url: str
    source: str = "Screener reported data + Yahoo Finance price history + NSE/news context"


class PremiumEquityResearchProvider:
    """Fetch and score public-company evidence with conservative data controls."""

    URL = "https://www.screener.in/company/{symbol}/consolidated/"
    HEADERS = {"User-Agent": "Mozilla/5.0 (Market Wavez research; public-data screen)"}
    MAX_WORKERS = 6

    def assess_many(
        self,
        stocks: list,
        histories: dict,
        articles: list[NewsArticle] = (),
        fii_dii_context: str = "",
    ) -> dict[str, PremiumEquityAssessment]:
        output: dict[str, PremiumEquityAssessment] = {}
        with ThreadPoolExecutor(max_workers=self.MAX_WORKERS) as executor:
            futures = {
                executor.submit(self.assess_one, stock, histories.get(self._symbol(stock)), articles, fii_dii_context): self._symbol(stock)
                for stock in stocks
            }
            for future in as_completed(futures):
                symbol = futures[future]
                try:
                    output[symbol] = future.result()
                except Exception:
                    # Candidate cards remain available from deterministic price
                    # evidence; a failed enrichment is never treated as good.
                    continue
        return output

    def assess_one(self, stock, history, articles: list[NewsArticle], fii_dii_context: str = "") -> PremiumEquityAssessment:
        symbol = self._symbol(stock)
        report_url = self.URL.format(symbol=quote(symbol, safe=""))
        payload = self._fetch(report_url)
        name = payload.get("company_name") or getattr(stock, "company_name", "") or symbol
        strengths: list[str] = []
        risks: list[str] = []
        gaps: list[str] = []
        metrics: list[str] = []

        sales_3y = payload.get("sales_3y")
        profit_3y = payload.get("profit_3y")
        sales_5y = payload.get("sales_5y")
        profit_5y = payload.get("profit_5y")
        sales_yoy = payload.get("sales_yoy")
        profit_yoy = payload.get("profit_yoy")
        opm = payload.get("opm")
        roce = payload.get("roce")
        roe = payload.get("roe")
        debt_equity = payload.get("debt_equity")
        cfo = payload.get("cfo")
        net_profit = payload.get("net_profit")
        operating_profit = payload.get("operating_profit")
        interest = payload.get("interest")
        capex = payload.get("capex")
        tax_rate = payload.get("tax_rate")
        promoter = payload.get("promoter")
        promoter_change = payload.get("promoter_change")
        fii_change = payload.get("fii_change")
        dii_change = payload.get("dii_change")
        promoter_pledge = payload.get("promoter_pledge")

        growth = 0
        for label, value, maximum in (("Sales 3Y CAGR", sales_3y, 6), ("Profit 3Y CAGR", profit_3y, 6), ("Sales 5Y CAGR", sales_5y, 4), ("Profit 5Y CAGR", profit_5y, 4), ("Sales YoY", sales_yoy, 3), ("Profit YoY", profit_yoy, 3)):
            if value is None:
                gaps.append(f"{label} unavailable")
            elif value >= 15:
                growth += maximum
                strengths.append(f"{label} growth {value:.1f}%")
                metrics.append(f"{label} {value:+.1f}%")
            elif value > 0:
                growth += round(maximum * 0.45)
                metrics.append(f"{label} {value:+.1f}%")
            else:
                risks.append(f"{label} is negative ({value:.1f}%)")
                metrics.append(f"{label} {value:+.1f}%")

        quality = 0
        if opm is None:
            gaps.append("Operating margin unavailable")
        elif opm >= 15:
            quality += 6; strengths.append(f"Operating margin {opm:.1f}%"); metrics.append(f"OPM {opm:.1f}%")
        elif opm > 0:
            quality += 3; metrics.append(f"OPM {opm:.1f}%")
        else:
            risks.append("Operating margin is negative")
        if roce is None:
            gaps.append("ROCE unavailable")
        elif roce >= 15:
            quality += 8; strengths.append(f"ROCE {roce:.1f}%"); metrics.append(f"ROCE {roce:.1f}%")
        elif roce >= 10:
            quality += 4; metrics.append(f"ROCE {roce:.1f}%")
        else:
            risks.append(f"Low ROCE ({roce:.1f}%)")
        if roe is not None:
            metrics.append(f"ROE {roe:.1f}%")
        if debt_equity is None:
            gaps.append("Debt/equity unavailable")
        elif debt_equity <= 0.5:
            quality += 5; strengths.append(f"Debt/equity {debt_equity:.2f}x"); metrics.append(f"D/E {debt_equity:.2f}x")
        elif debt_equity <= 1.0:
            quality += 2; risks.append(f"Debt/equity needs monitoring ({debt_equity:.2f}x)")
        else:
            risks.append(f"Elevated debt/equity ({debt_equity:.2f}x)")
        if cfo is None or net_profit is None:
            gaps.append("Cash-flow conversion unavailable")
        elif net_profit > 0 and cfo / net_profit >= 0.8:
            quality += 5; strengths.append("Operating cash flow supports reported profit")
        elif net_profit > 0:
            risks.append("Operating cash flow does not fully support reported profit")
        if operating_profit is None or interest is None:
            gaps.append("Interest-coverage check unavailable")
        elif interest > 0:
            interest_cover = operating_profit / interest
            metrics.append(f"Interest cover {interest_cover:.1f}x")
            if interest_cover < 2:
                risks.append(f"Weak interest cover ({interest_cover:.1f}x)")
            elif interest_cover >= 4:
                strengths.append(f"Interest cover {interest_cover:.1f}x")
        if cfo is not None and capex is not None:
            free_cash_flow = cfo + capex
            metrics.append(f"Free cash flow {'positive' if free_cash_flow >= 0 else 'negative'}")
            if free_cash_flow < 0 and net_profit and net_profit > 0:
                risks.append("Free cash flow is negative despite reported profit")
        if tax_rate is not None:
            metrics.append(f"Tax rate {tax_rate:.1f}%")

        ownership = 0
        if promoter is None:
            gaps.append("Latest promoter holding unavailable")
        else:
            metrics.append(f"Promoters {promoter:.1f}%")
            if promoter >= 45:
                ownership += 4
            if promoter_change is not None:
                metrics.append(f"Promoter Δ {promoter_change:+.2f}pp")
                if promoter_change >= 0:
                    ownership += 3
                elif promoter_change <= -1:
                    risks.append(f"Promoter holding fell {abs(promoter_change):.2f}pp")
            if fii_change is not None:
                metrics.append(f"FII Δ {fii_change:+.2f}pp")
                if fii_change > 0:
                    ownership += 3
            if dii_change is not None:
                metrics.append(f"DII Δ {dii_change:+.2f}pp")
                if dii_change > 0:
                    ownership += 3
            if promoter_pledge is not None:
                metrics.append(f"Promoter pledge {promoter_pledge:.1f}%")
                if promoter_pledge > 5:
                    risks.append(f"Promoter pledge is elevated ({promoter_pledge:.1f}%)")
        if fii_dii_context:
            metrics.append(fii_dii_context)

        technical = 0
        if history is None:
            gaps.append("Multi-year price history unavailable")
        else:
            price = float(getattr(stock, "value", 0) or 0)
            for average, label, points in ((getattr(history, "sma20", None), "20 DMA", 3), (getattr(history, "sma50", None), "50 DMA", 4), (getattr(history, "sma200", None), "200 DMA", 5)):
                if average is not None and price > average:
                    technical += points
                elif average is not None:
                    risks.append(f"Price is below {label}")
            high_52 = getattr(history, "high_52w", None)
            low_52 = getattr(history, "low_52w", None)
            if high_52 and low_52 and high_52 > low_52:
                position = (price - low_52) / (high_52 - low_52)
                metrics.append(f"52W range position {position:.0%}")
                if 0.45 <= position <= 0.9:
                    technical += 3
                elif position > 0.97:
                    risks.append("Price is extended near the 52-week high")
            if getattr(history, "return_5y_annualized", None) is not None:
                metrics.append(f"5Y price CAGR {history.return_5y_annualized:+.1f}%")
            support, resistance = getattr(history, "support", None), getattr(history, "resistance", None)
            if support and resistance:
                metrics.append(f"Support/Resistance ₹{support:,.0f}/₹{resistance:,.0f}")

        catalyst, event_risks = self._event_evidence(symbol, name, articles)
        if catalyst:
            strengths.extend(catalyst[:2])
        risks.extend(event_risks[:2])
        catalyst_score = min(12, 4 * len(catalyst))
        risk_score = min(100, 12 * len(risks) + (18 if len(gaps) >= 5 else 0))
        raw = growth + quality + ownership + technical + catalyst_score
        coverage = sum(value is not None for value in (sales_3y, profit_3y, opm, roce, debt_equity, promoter, getattr(history, "sma50", None) if history else None))
        confidence = min(92, 35 + coverage * 8 + min(9, len(catalyst) * 3))
        # Avoid a deceptively precise high score when most public evidence is absent.
        composite = round(min(100, raw / 87 * 100))
        if coverage < 4:
            composite = min(composite, 55)
            confidence = min(confidence, 55)
        return PremiumEquityAssessment(
            symbol=symbol, company_name=name, composite_score=round(composite), growth_score=min(26, growth),
            quality_score=min(24, quality), ownership_score=min(10, ownership), technical_score=min(15, technical),
            catalyst_score=catalyst_score, risk_score=risk_score, confidence=round(confidence),
            strengths=tuple(dict.fromkeys(strengths))[:6], risks=tuple(dict.fromkeys(risks))[:6],
            data_gaps=tuple(dict.fromkeys(gaps))[:6], metrics=tuple(metrics)[:9], report_url=report_url,
        )

    def _fetch(self, url: str) -> dict[str, object]:
        response = requests.get(url, headers=self.HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        title = soup.select_one("h1")
        payload: dict[str, object] = {"company_name": title.get_text(" ", strip=True) if title else ""}
        top = {self._clean(node.select_one("span.name").get_text(" ", strip=True) if node.select_one("span.name") else node.get_text(" ", strip=True)): self._number(node.select_one("span.value").get_text(" ", strip=True) if node.select_one("span.value") else node.get_text(" ", strip=True)) for node in soup.select("#top-ratios li")}
        payload["roce"] = top.get("roce")
        payload["roe"] = top.get("roe")
        payload.update({
            "sales_yoy": self._growth(soup, "quarters", "sales"),
            "profit_yoy": self._growth(soup, "quarters", "net profit"),
            "sales_3y": self._growth(soup, "profit-loss", "sales", years=3),
            "profit_3y": self._growth(soup, "profit-loss", "net profit", years=3),
            "sales_5y": self._growth(soup, "profit-loss", "sales", years=5),
            "profit_5y": self._growth(soup, "profit-loss", "net profit", years=5),
            "opm": self._latest(soup, "profit-loss", "opm"),
            "net_profit": self._latest(soup, "profit-loss", "net profit"),
            "operating_profit": self._latest(soup, "profit-loss", "operating profit"),
            "interest": self._latest(soup, "profit-loss", "interest"),
            "tax_rate": self._latest(soup, "profit-loss", "tax"),
            "cfo": self._latest(soup, "cash-flow", "cash from operating activity"),
            # Screener represents asset purchases as a negative cash-flow
            # item, so CFO + capex is the simple reported free-cash-flow
            # direction used for this screen.
            "capex": self._latest(soup, "cash-flow", "fixed assets purchased"),
            "debt_equity": self._debt_equity(soup),
        })
        payload.update(self._ownership(soup))
        return payload

    @staticmethod
    def _symbol(stock) -> str:
        return str(getattr(stock, "name", "")).replace("-EQ", "").strip().upper()

    @staticmethod
    def _clean(value: str) -> str:
        return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()

    @classmethod
    def _number(cls, value: str) -> float | None:
        value = value.replace(",", "").replace("₹", "").replace("%", "").strip()
        match = re.search(r"-?\d+(?:\.\d+)?", value)
        return float(match.group()) if match else None

    @classmethod
    def _row(cls, soup: BeautifulSoup, section_id: str, label: str) -> list[float | None]:
        section = soup.select_one(f"#{section_id}")
        if not section:
            return []
        needle = cls._clean(label)
        for row in section.select("tbody tr"):
            cells = row.select("th,td")
            if cells and cls._clean(cells[0].get_text(" ", strip=True)).startswith(needle):
                return [cls._number(cell.get_text(" ", strip=True)) for cell in cells[1:]]
        return []

    @classmethod
    def _latest(cls, soup: BeautifulSoup, section_id: str, label: str) -> float | None:
        values = [value for value in cls._row(soup, section_id, label) if value is not None]
        return values[-1] if values else None

    @classmethod
    def _growth(cls, soup: BeautifulSoup, section_id: str, label: str, years: int = 1) -> float | None:
        values = [value for value in cls._row(soup, section_id, label) if value is not None]
        if len(values) <= years or values[-1 - years] == 0:
            return None
        ratio = values[-1] / values[-1 - years]
        return ((ratio ** (1 / years)) - 1) * 100 if years > 1 and ratio > 0 else (ratio - 1) * 100

    @classmethod
    def _debt_equity(cls, soup: BeautifulSoup) -> float | None:
        debt = cls._latest(soup, "balance-sheet", "borrowings")
        equity_capital = cls._latest(soup, "balance-sheet", "equity capital")
        reserves = cls._latest(soup, "balance-sheet", "reserves")
        if debt is None or equity_capital is None or reserves is None or equity_capital + reserves <= 0:
            return None
        return debt / (equity_capital + reserves)

    @classmethod
    def _ownership(cls, soup: BeautifulSoup) -> dict[str, float | None]:
        result: dict[str, float | None] = {"promoter": None, "promoter_change": None, "fii_change": None, "dii_change": None, "promoter_pledge": None}
        for name, prefix in (("promoters", "promoter"), ("fiis", "fii"), ("diis", "dii")):
            values = [value for value in cls._row(soup, "shareholding", name) if value is not None]
            if values:
                if prefix == "promoter":
                    result["promoter"] = values[-1]
                result[f"{prefix}_change"] = values[-1] - values[-2] if len(values) >= 2 else None
        pledge = [value for value in cls._row(soup, "shareholding", "pledged percentage") if value is not None]
        if pledge:
            result["promoter_pledge"] = pledge[-1]
        return result

    @staticmethod
    def _event_evidence(symbol: str, company_name: str, articles: list[NewsArticle]) -> tuple[list[str], list[str]]:
        aliases = {symbol.lower(), *(part.lower() for part in company_name.split() if len(part) >= 4)}
        positive_terms = ("order", "contract", "order book", "acquisition", "merger", "approval", "profit rises", "profit jumps", "revenue rises", "guidance", "expansion", "capacity", "buyback", "dividend")
        risk_terms = ("pledge", "resignation", "fraud", "default", "loss widens", "profit falls", "rating downgrade", "regulatory action", "debt", "stake sale", "investigation", "litigation", "governance", "dilution")
        positives: list[str] = []
        risks: list[str] = []
        for article in articles:
            text = f"{article.title} {article.summary}".lower()
            if not any(alias in text for alias in aliases):
                continue
            if any(term in text for term in positive_terms):
                positives.append(f"Catalyst: {article.title[:115]}")
            if any(term in text for term in risk_terms):
                risks.append(f"Event risk: {article.title[:115]}")
        return list(dict.fromkeys(positives)), list(dict.fromkeys(risks))
