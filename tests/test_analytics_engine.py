"""
Test script for Analytics Engine.

Run:
    python -m market_sentinel.tests.test_analytics_engine
"""

from pprint import pprint

from market_sentinel.analytics.engine import AnalyticsEngine
from market_sentinel.analytics.enums import MarketType


def main():

    asset = AnalyticsEngine.analyze(
        symbol="BTC",
        name="Bitcoin",
        market=MarketType.CRYPTO,
        current_price=118250.50,

        daily_change=5.42,
        weekly_change=11.84,
        monthly_change=18.61,

        current_volume=2_500_000,
        average_volume=1_200_000,
    )

    print("=" * 60)
    print("Analytics Engine Test")
    print("=" * 60)

    pprint(asset)


if __name__ == "__main__":
    main()