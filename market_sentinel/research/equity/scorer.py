"""Transparent financial-quality scoring; not an investment recommendation."""

from __future__ import annotations

from datetime import datetime

from market_sentinel.research.equity.models import EquityResearchCard, FinancialSnapshot


class EquityQualityScorer:
    def score(self, snapshot: FinancialSnapshot) -> EquityResearchCard:
        strengths: list[str] = []
        risks: list[str] = []
        gaps: list[str] = []
        growth = self._growth(snapshot, strengths, risks, gaps)
        profitability = self._profitability(snapshot, strengths, risks, gaps)
        balance = self._balance_sheet(snapshot, strengths, risks, gaps)
        cash_flow = self._cash_flow(snapshot, strengths, risks, gaps)
        total = growth + profitability + balance + cash_flow
        # A missing data item must never increase a score.  This is a quality
        # score, not a forecast or a declaration that a company will multibag.
        return EquityResearchCard(
            symbol=snapshot.symbol, company_name=snapshot.company_name, quality_score=total,
            growth_score=growth, profitability_score=profitability, balance_sheet_score=balance,
            cash_flow_score=cash_flow, strengths=tuple(strengths), risks=tuple(risks),
            data_gaps=tuple(gaps), snapshot=snapshot, generated_at=datetime.now(),
        )

    @staticmethod
    def _growth(snapshot, strengths, risks, gaps) -> int:
        if not snapshot.revenue_current or not snapshot.revenue_previous:
            gaps.append("Two comparable annual revenue figures unavailable")
            return 0
        growth = (snapshot.revenue_current / snapshot.revenue_previous - 1) * 100
        # Tolerate floating-point representation around published thresholds.
        if growth >= 19.95:
            strengths.append(f"Annual revenue grew {growth:.1f}%")
            return 25
        if growth >= 10:
            strengths.append(f"Annual revenue grew {growth:.1f}%")
            return 18
        if growth > 0:
            risks.append(f"Revenue growth is modest at {growth:.1f}%")
            return 8
        risks.append(f"Annual revenue declined {abs(growth):.1f}%")
        return 0

    @staticmethod
    def _profitability(snapshot, strengths, risks, gaps) -> int:
        if snapshot.net_income is None or not snapshot.revenue_current:
            gaps.append("Profitability figures unavailable")
            return 0
        margin = snapshot.net_income / snapshot.revenue_current * 100
        score = 0
        if margin >= 15:
            strengths.append(f"Net margin is {margin:.1f}%")
            score += 15
        elif margin > 0:
            strengths.append(f"Company is profitable (net margin {margin:.1f}%)")
            score += 7
        else:
            risks.append("Company reported a net loss")
        if snapshot.return_on_equity is None:
            gaps.append("Return on equity unavailable")
        elif snapshot.return_on_equity >= 18:
            strengths.append(f"Return on equity is {snapshot.return_on_equity:.1f}%")
            score += 10
        elif snapshot.return_on_equity < 10:
            risks.append(f"Return on equity is low at {snapshot.return_on_equity:.1f}%")
        return score

    @staticmethod
    def _balance_sheet(snapshot, strengths, risks, gaps) -> int:
        if snapshot.total_debt is None or not snapshot.equity:
            gaps.append("Debt/equity data unavailable")
            return 0
        ratio = snapshot.total_debt / snapshot.equity
        if ratio <= 0.5:
            strengths.append(f"Debt-to-equity is conservative at {ratio:.2f}x")
            return 20
        if ratio <= 1.0:
            risks.append(f"Debt-to-equity requires monitoring at {ratio:.2f}x")
            return 10
        risks.append(f"Debt-to-equity is elevated at {ratio:.2f}x")
        return 0

    @staticmethod
    def _cash_flow(snapshot, strengths, risks, gaps) -> int:
        if snapshot.operating_cash_flow is None or snapshot.net_income is None:
            gaps.append("Cash-flow conversion data unavailable")
            return 0
        score = 0
        if snapshot.net_income > 0 and snapshot.operating_cash_flow / snapshot.net_income >= 0.8:
            strengths.append("Operating cash flow supports reported earnings")
            score += 10
        else:
            risks.append("Operating cash flow does not fully support reported earnings")
        if snapshot.free_cash_flow is None:
            gaps.append("Free cash flow unavailable")
        elif snapshot.free_cash_flow > 0:
            strengths.append("Free cash flow is positive")
            score += 10
        else:
            risks.append("Free cash flow is negative")
        return score
