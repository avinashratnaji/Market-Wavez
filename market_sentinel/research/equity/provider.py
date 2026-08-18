"""Read-only financial-statement adapter for private research."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from market_sentinel.research.equity.models import FinancialSnapshot


class YahooFinancialProvider:
    """Fetchs reported financial fields; unavailable fields stay unavailable."""

    def fetch(self, symbol: str) -> FinancialSnapshot:
        import yfinance as yf

        ticker = yf.Ticker(symbol if symbol.endswith(".NS") else f"{symbol}.NS")
        financials = ticker.financials
        balance = ticker.balance_sheet
        cashflow = ticker.cashflow
        info = ticker.info or {}
        revenue = _row(financials, "Total Revenue")
        net_income = _latest(_row(financials, "Net Income"))
        equity = _latest(_row(balance, "Stockholders Equity", "Stockholders' Equity"))
        debt = _latest(_row(balance, "Total Debt"))
        cash = _latest(_row(balance, "Cash Cash Equivalents And Short Term Investments", "Cash And Cash Equivalents"))
        operating_cash_flow = _latest(_row(cashflow, "Operating Cash Flow", "Total Cash From Operating Activities"))
        free_cash_flow = _latest(_row(cashflow, "Free Cash Flow"))
        return FinancialSnapshot(
            symbol=symbol.removesuffix(".NS"), company_name=str(info.get("longName") or symbol), captured_at=datetime.now(),
            revenue_current=_latest(revenue), revenue_previous=_previous(revenue), net_income=net_income,
            operating_cash_flow=operating_cash_flow, free_cash_flow=free_cash_flow, total_debt=debt, cash=cash,
            equity=equity, return_on_equity=_ratio_percent(net_income, equity), trailing_pe=_float_or_none(info.get("trailingPE")),
            source="Yahoo Finance reported financials (validate against exchange filings before use)",
        )


def _row(frame: Any, *names: str):
    if frame is None or getattr(frame, "empty", True):
        return None
    for name in names:
        if name in frame.index:
            return frame.loc[name]
    return None


def _latest(series: Any) -> float | None:
    if series is None or len(series) == 0:
        return None
    return _float_or_none(series.iloc[0])


def _previous(series: Any) -> float | None:
    if series is None or len(series) < 2:
        return None
    return _float_or_none(series.iloc[1])


def _ratio_percent(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or not denominator:
        return None
    return numerator / denominator * 100


def _float_or_none(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
