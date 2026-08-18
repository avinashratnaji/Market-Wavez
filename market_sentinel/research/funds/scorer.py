"""Category-aware fund comparison without personal suitability claims."""

from __future__ import annotations

from market_sentinel.research.funds.models import FundResearchCard, FundSnapshot


class MutualFundResearchScorer:
    """Score a disclosed fund data record; comparisons must use one category."""

    def score(self, fund: FundSnapshot) -> FundResearchCard:
        strengths: list[str] = []
        risks: list[str] = []
        gaps: list[str] = []
        returns = self._returns(fund, strengths, risks, gaps)
        risk = self._risk(fund, strengths, risks, gaps)
        cost = self._cost(fund, strengths, risks, gaps)
        portfolio = self._portfolio(fund, strengths, risks, gaps)
        return FundResearchCard(
            fund=fund, research_score=returns + risk + cost + portfolio,
            return_score=returns, risk_score=risk, cost_score=cost, portfolio_score=portfolio,
            strengths=tuple(strengths), risks=tuple(risks), data_gaps=tuple(gaps),
        )

    @staticmethod
    def _returns(fund, strengths, risks, gaps) -> int:
        value = fund.five_year_return if fund.five_year_return is not None else fund.three_year_return
        period = "5-year" if fund.five_year_return is not None else "3-year"
        if value is None:
            gaps.append("Three- and five-year annualised return unavailable")
            return 0
        if value >= 15:
            strengths.append(f"{period} annualised return is {value:.1f}%")
            return 30
        if value >= 10:
            strengths.append(f"{period} annualised return is {value:.1f}%")
            return 20
        risks.append(f"{period} annualised return is modest at {value:.1f}%")
        return 10

    @staticmethod
    def _risk(fund, strengths, risks, gaps) -> int:
        score = 0
        if fund.max_drawdown is None:
            gaps.append("Maximum drawdown unavailable")
        elif fund.max_drawdown >= -20:
            strengths.append(f"Maximum drawdown was contained at {fund.max_drawdown:.1f}%")
            score += 15
        else:
            risks.append(f"Maximum drawdown reached {fund.max_drawdown:.1f}%")
        if fund.sharpe_ratio is None:
            gaps.append("Sharpe ratio unavailable")
        elif fund.sharpe_ratio >= 1:
            strengths.append(f"Sharpe ratio is {fund.sharpe_ratio:.2f}")
            score += 15
        elif fund.sharpe_ratio < 0.5:
            risks.append(f"Risk-adjusted return is weak (Sharpe {fund.sharpe_ratio:.2f})")
        return score

    @staticmethod
    def _cost(fund, strengths, risks, gaps) -> int:
        if fund.expense_ratio is None:
            gaps.append("Expense ratio unavailable")
            return 0
        if fund.expense_ratio <= 0.75:
            strengths.append(f"Expense ratio is efficient at {fund.expense_ratio:.2f}%")
            return 20
        if fund.expense_ratio <= 1.5:
            risks.append(f"Expense ratio needs peer comparison at {fund.expense_ratio:.2f}%")
            return 10
        risks.append(f"Expense ratio is elevated at {fund.expense_ratio:.2f}%")
        return 0

    @staticmethod
    def _portfolio(fund, strengths, risks, gaps) -> int:
        if fund.top_ten_concentration is None:
            gaps.append("Top-10 holding concentration unavailable")
            return 0
        if fund.top_ten_concentration <= 45:
            strengths.append(f"Top-10 holdings are diversified at {fund.top_ten_concentration:.1f}%")
            return 20
        if fund.top_ten_concentration <= 65:
            risks.append(f"Top-10 holdings concentration is {fund.top_ten_concentration:.1f}%")
            return 10
        risks.append(f"Portfolio concentration is high at {fund.top_ten_concentration:.1f}%")
        return 0
