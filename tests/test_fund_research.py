from market_sentinel.research.funds.models import FundSnapshot
from market_sentinel.research.funds.scorer import MutualFundResearchScorer


def test_fund_score_uses_cost_risk_and_concentration_not_returns_alone():
    card = MutualFundResearchScorer().score(FundSnapshot(
        name="Demo Equity Fund", category="Flexi Cap", five_year_return=16,
        max_drawdown=-18, expense_ratio=0.6, sharpe_ratio=1.1, top_ten_concentration=40,
    ))

    assert card.research_score == 100
    assert not card.risks
