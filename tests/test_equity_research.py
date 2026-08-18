from datetime import datetime

from market_sentinel.research.equity.models import FinancialSnapshot
from market_sentinel.research.equity.scorer import EquityQualityScorer


def test_quality_score_rewards_growth_profitability_cash_and_conservative_debt():
    card = EquityQualityScorer().score(FinancialSnapshot(
        symbol="DEMO", company_name="Demo Ltd", captured_at=datetime.now(),
        revenue_current=120, revenue_previous=100, net_income=24, operating_cash_flow=25,
        free_cash_flow=12, total_debt=10, equity=100, return_on_equity=24,
    ))

    assert card.quality_score == 90
    assert card.growth_score == 25
    assert card.balance_sheet_score == 20
    assert not card.data_gaps
