from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FundSnapshot:
    name: str
    category: str
    three_year_return: float | None = None
    five_year_return: float | None = None
    max_drawdown: float | None = None
    expense_ratio: float | None = None
    sharpe_ratio: float | None = None
    top_ten_concentration: float | None = None
    aum_cr: float | None = None


@dataclass(frozen=True, slots=True)
class FundResearchCard:
    fund: FundSnapshot
    research_score: int
    return_score: int
    risk_score: int
    cost_score: int
    portfolio_score: int
    strengths: tuple[str, ...]
    risks: tuple[str, ...]
    data_gaps: tuple[str, ...]
