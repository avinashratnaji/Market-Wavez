"""Models for auditable long-term equity research."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class FinancialSnapshot:
    symbol: str
    company_name: str
    captured_at: datetime
    revenue_current: float | None = None
    revenue_previous: float | None = None
    net_income: float | None = None
    operating_cash_flow: float | None = None
    free_cash_flow: float | None = None
    total_debt: float | None = None
    cash: float | None = None
    equity: float | None = None
    return_on_equity: float | None = None
    trailing_pe: float | None = None
    source: str = ""


@dataclass(frozen=True, slots=True)
class EquityResearchCard:
    symbol: str
    company_name: str
    quality_score: int
    growth_score: int
    profitability_score: int
    balance_sheet_score: int
    cash_flow_score: int
    strengths: tuple[str, ...]
    risks: tuple[str, ...]
    data_gaps: tuple[str, ...]
    snapshot: FinancialSnapshot
    generated_at: datetime
