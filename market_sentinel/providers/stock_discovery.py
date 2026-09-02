"""Broad, explainable NSE momentum and growth-research discovery."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import time
from urllib.parse import quote

import requests
from loguru import logger

from market_sentinel.briefs.models import StockResearchSignal
from market_sentinel.research.equity.premium import PremiumEquityAssessment, PremiumEquityResearchProvider


@dataclass(frozen=True, slots=True)
class _History:
    return_5d: float | None
    return_20d: float | None
    sma20: float | None
    sma50: float | None
    average_volume_20: float | None
    sma200: float | None = None
    high_52w: float | None = None
    low_52w: float | None = None
    support: float | None = None
    resistance: float | None = None
    return_5y_annualized: float | None = None


class StockDiscoveryProvider:
    """Rank liquid movers using price, trend, volume and reported fundamentals.

    The output is a research shortlist.  A stock is never labelled bullish or
    bearish from a headline alone, and a growth candidate requires reported
    year-on-year revenue growth plus earnings improvement.
    """

    HEADERS = {"User-Agent": "Mozilla/5.0 (Market Wavez research)"}
    MIN_PRICE = 10.0
    MIN_VOLUME = 100_000
    # Extended moves are still worth flagging for research (a strict circuit
    # filter is how early-stage rallies can disappear from a watchlist), but
    # they must carry an explicit reversal/liquidity warning in the output.
    MAX_ABS_DAILY_CHANGE = 35.0
    MAX_WORKERS = 10

    def __init__(self) -> None:
        self.premium = PremiumEquityResearchProvider()

    def analyze(self, gainers: list, losers: list, articles=(), fii_dii_context: str = "") -> tuple[list, list, list, list, list]:
        # Blend the largest percentage moves with the most liquid names so a
        # meaningful high-volume move is not hidden behind illiquid circuits.
        raw = []
        for side in (gainers, losers):
            raw.extend(side[:15])
            raw.extend(sorted(side, key=lambda item: float(getattr(item, "volume", 0) or 0), reverse=True)[:10])
        stocks = self._eligible(raw)
        histories = self._histories(stocks)
        assessments = self.premium.assess_many(stocks, histories, list(articles), fii_dii_context)
        bullish = self._daily(stocks, histories, assessments, "Bullish")[:5]
        bearish = self._daily(stocks, histories, assessments, "Bearish")[:5]
        week_bullish = self._weekly(stocks, histories, assessments, "Bullish")[:5]
        week_bearish = self._weekly(stocks, histories, assessments, "Bearish")[:5]
        growth = self._growth(stocks, histories, assessments)[:5]
        return bullish, bearish, week_bullish, week_bearish, growth

    def _eligible(self, stocks: list) -> list:
        unique = {}
        for stock in stocks:
            symbol = str(getattr(stock, "name", "")).replace("-EQ", "").strip().upper()
            price = float(getattr(stock, "value", 0) or 0)
            volume = float(getattr(stock, "volume", 0) or 0)
            change = abs(float(getattr(stock, "percent_change", 0) or 0))
            if symbol and price >= self.MIN_PRICE and volume >= self.MIN_VOLUME and change < self.MAX_ABS_DAILY_CHANGE:
                unique[symbol] = stock
        return list(unique.values())

    def _histories(self, stocks: list) -> dict[str, _History]:
        output: dict[str, _History] = {}
        with ThreadPoolExecutor(max_workers=self.MAX_WORKERS) as executor:
            futures = {
                executor.submit(self._history, self._symbol(stock)): self._symbol(stock)
                for stock in stocks
            }
            for future in as_completed(futures):
                symbol = futures[future]
                try:
                    output[symbol] = future.result()
                except Exception as exc:
                    logger.debug("History unavailable for {}: {}", symbol, exc)
        return output

    @classmethod
    def _history(cls, symbol: str) -> _History:
        response = requests.get(
            f"https://query1.finance.yahoo.com/v8/finance/chart/{quote(symbol + '.NS', safe='')}",
            # 200 DMA and annualised five-year return must be calculated from
            # a real multi-year series.  A six-month request silently made
            # both fields misleading or unavailable.
            params={"range": "5y", "interval": "1d"},
            headers=cls.HEADERS,
            timeout=12,
        )
        response.raise_for_status()
        result = (response.json().get("chart") or {}).get("result") or []
        quote_rows = ((result[0].get("indicators") or {}).get("quote") or []) if result else []
        closes = [float(value) for value in (quote_rows[0].get("close", []) if quote_rows else []) if value is not None]
        volumes = [float(value) for value in (quote_rows[0].get("volume", []) if quote_rows else []) if value not in (None, 0)]
        if len(closes) < 6:
            return _History(None, None, None, None, None, None, None, None, None, None)
        return_5y = (closes[-1] / closes[0]) ** (1 / 5) * 100 - 100 if len(closes) >= 900 and closes[0] > 0 else None
        return _History(
            (closes[-1] / closes[-6] - 1) * 100,
            (closes[-1] / closes[-21] - 1) * 100 if len(closes) >= 21 else None,
            sum(closes[-20:]) / min(20, len(closes)),
            sum(closes[-50:]) / min(50, len(closes)),
            sum(volumes[-20:]) / min(20, len(volumes)) if volumes else None,
            sum(closes[-200:]) / min(200, len(closes)),
            max(closes[-252:]) if len(closes) >= 252 else max(closes),
            min(closes[-252:]) if len(closes) >= 252 else min(closes),
            min(closes[-20:]),
            max(closes[-20:]),
            return_5y,
        )

    def _daily(self, stocks: list, histories: dict[str, _History], assessments: dict[str, PremiumEquityAssessment], bias: str) -> list[StockResearchSignal]:
        direction = 1 if bias == "Bullish" else -1
        output = []
        for stock in stocks:
            change = float(stock.percent_change)
            if change * direction <= 0 or abs(change) < 0.8:
                continue
            history = histories.get(self._symbol(stock))
            assessment = assessments.get(self._symbol(stock))
            if not assessment or assessment.confidence < 55:
                continue
            high, low, price = float(stock.high or 0), float(stock.low or 0), float(stock.value)
            range_position = (price - low) / (high - low) if high > low else 0.5
            strength = range_position if direction > 0 else 1 - range_position
            relative_volume = self._relative_volume(stock, history)
            trend_match = bool(history and history.sma20 and ((price > history.sma20) if direction > 0 else (price < history.sma20)))
            price_score = min(100, 28 + min(10, abs(change)) * 4.2 + strength * 13 + min(3, relative_volume or 0) * 4 + (7 if trend_match else 0))
            # New listings and turnaround names may have a genuine volume-led
            # catalyst before they have three/five years of reported history.
            # Surface that as a *limited-evidence* research lead instead of
            # silently missing it or falsely calling it high-quality growth.
            early_catalyst = (
                bias == "Bullish"
                and assessment.confidence <= 55
                and abs(change) >= 5
                and (relative_volume or 0) >= 1.5
            )
            if bias == "Bullish" and assessment.composite_score < 50 and not early_catalyst:
                continue
            if bias == "Bearish" and assessment.risk_score < 18 and assessment.technical_score >= 8:
                continue
            score = round(min(100, price_score * 0.35 + assessment.composite_score * 0.65))
            reasons = [f"Multi-factor score {assessment.composite_score}/100 ({assessment.confidence}% evidence coverage)"]
            if early_catalyst:
                reasons.append("early catalyst / momentum; long-term evidence is incomplete")
            reasons.extend(assessment.strengths[:2] if direction > 0 else assessment.risks[:2])
            if abs(change) >= 15:
                reasons.append("extended move; circuit/reversal risk")
            if relative_volume is not None:
                reasons.append(f"volume {relative_volume:.1f}x 20D average")
            if trend_match:
                reasons.append("trend confirms the move")
            output.append(self._signal(stock, bias, "Today", min(score, 55) if early_catalyst else score, reasons[:3], assessment))
        return sorted(output, key=lambda item: item.score, reverse=True)

    def _weekly(self, stocks: list, histories: dict[str, _History], assessments: dict[str, PremiumEquityAssessment], bias: str) -> list[StockResearchSignal]:
        direction = 1 if bias == "Bullish" else -1
        output = []
        for stock in stocks:
            history = histories.get(self._symbol(stock))
            assessment = assessments.get(self._symbol(stock))
            if not history or history.return_5d is None or history.sma20 is None:
                continue
            if not assessment or assessment.confidence < 55:
                continue
            price = float(stock.value)
            trend_ok = (history.return_5d * direction >= 1.5 and (price - history.sma20) * direction > 0)
            if not trend_ok:
                continue
            aligned_20d = history.return_20d is not None and history.return_20d * direction > 0
            price_score = min(100, 45 + min(12, abs(history.return_5d)) * 3 + (12 if aligned_20d else 0) + (8 if history.sma50 and (price - history.sma50) * direction > 0 else 0))
            if bias == "Bullish" and assessment.composite_score < 55:
                continue
            if bias == "Bearish" and assessment.risk_score < 18 and assessment.technical_score >= 8:
                continue
            score = round(min(100, price_score * 0.35 + assessment.composite_score * 0.65))
            reasons = [f"Research score {assessment.composite_score}/100", f"5D move {history.return_5d:+.1f}%"]
            reasons.extend(assessment.strengths[:1] if direction > 0 else assessment.risks[:1])
            if history.return_20d is not None:
                reasons.append(f"20D move {history.return_20d:+.1f}%")
            output.append(self._signal(stock, bias, "This week", score, reasons[:3], assessment))
        return sorted(output, key=lambda item: item.score, reverse=True)

    def _growth(self, stocks: list, histories: dict[str, _History], assessments: dict[str, PremiumEquityAssessment]) -> list[StockResearchSignal]:
        output = []
        for stock in stocks:
            symbol = self._symbol(stock)
            assessment = assessments.get(symbol)
            history = histories.get(symbol)
            if not assessment or assessment.confidence < 65 or assessment.growth_score < 14 or assessment.quality_score < 9:
                continue
            price = float(stock.value)
            trend_ok = bool(history and history.sma20 and price > history.sma20)
            score = round(min(100, assessment.composite_score + (5 if trend_ok else 0)))
            reasons = [f"Growth {assessment.growth_score}/26 · quality {assessment.quality_score}/24"]
            reasons.extend(assessment.strengths[:2])
            if trend_ok:
                reasons.append("price above 20D trend")
            signal = self._signal(stock, "Growth research", "Multi-year fundamentals + trend", score, reasons[:3], assessment)
            output.append(signal)
        return sorted(output, key=lambda item: item.score, reverse=True)

    def _fundamentals(self, stocks: list) -> dict[str, tuple[float | None, float | None]]:
        output = {}
        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = {executor.submit(self._one_fundamental, self._symbol(stock)): self._symbol(stock) for stock in stocks}
            for future in as_completed(futures):
                try:
                    output[futures[future]] = future.result()
                except Exception as exc:
                    logger.debug("Fundamentals unavailable for {}: {}", futures[future], exc)
        return output

    @classmethod
    def _one_fundamental(cls, symbol: str) -> tuple[float | None, float | None]:
        yahoo_symbol = symbol + ".NS"
        now = int(time.time())
        response = requests.get(
            f"https://query2.finance.yahoo.com/ws/fundamentals-timeseries/v1/finance/timeseries/{quote(yahoo_symbol, safe='')}",
            params={"symbol": yahoo_symbol, "type": "quarterlyTotalRevenue,quarterlyNetIncome", "period1": now - 700 * 86400, "period2": now},
            headers=cls.HEADERS,
            timeout=12,
        )
        response.raise_for_status()
        rows = (response.json().get("timeseries") or {}).get("result") or []
        series = {}
        for row in rows:
            types = (row.get("meta") or {}).get("type") or []
            if not types:
                continue
            values = [item.get("reportedValue", {}).get("raw") for item in row.get(types[0], [])]
            series[types[0]] = [float(value) for value in values if value is not None]
        revenue = cls._yoy(series.get("quarterlyTotalRevenue", []))
        earnings = cls._improvement(series.get("quarterlyNetIncome", []))
        return revenue, earnings

    @staticmethod
    def _yoy(values: list[float]) -> float | None:
        if len(values) < 5 or values[-5] == 0:
            return None
        return (values[-1] / values[-5] - 1) * 100

    @staticmethod
    def _improvement(values: list[float]) -> float | None:
        if len(values) < 5 or values[-5] == 0:
            return None
        return (values[-1] - values[-5]) / abs(values[-5]) * 100

    @staticmethod
    def _relative_volume(stock, history: _History | None) -> float | None:
        if not history or not history.average_volume_20:
            return None
        return float(stock.volume or 0) / history.average_volume_20

    @staticmethod
    def _symbol(stock) -> str:
        return str(getattr(stock, "name", "")).replace("-EQ", "").strip().upper()

    def _signal(self, stock, bias: str, horizon: str, score: int, reasons: list[str], assessment: PremiumEquityAssessment | None = None) -> StockResearchSignal:
        symbol = self._symbol(stock)
        return StockResearchSignal(
            symbol=symbol,
            company_name=str(getattr(stock, "company_name", "") or symbol),
            price=float(stock.value),
            percent_change=float(stock.percent_change),
            bias=bias,
            horizon=horizon,
            score=score,
            reasons=tuple(reasons),
            source=assessment.source if assessment else "NSE + Yahoo Finance",
            research_confidence=assessment.confidence if assessment else 0,
            growth_score=assessment.growth_score if assessment else 0,
            quality_score=assessment.quality_score if assessment else 0,
            ownership_score=assessment.ownership_score if assessment else 0,
            technical_score=assessment.technical_score if assessment else 0,
            catalyst_score=assessment.catalyst_score if assessment else 0,
            risk_score=assessment.risk_score if assessment else 0,
            key_risks=assessment.risks if assessment else (),
            data_gaps=assessment.data_gaps if assessment else (),
            metrics=assessment.metrics if assessment else (),
            report_url=assessment.report_url if assessment else "",
        )
