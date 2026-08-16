from market_sentinel.providers.angelone.client import AngelOneClient

client = AngelOneClient()

print(hasattr(client.api, "gainersLosers"))

# from datetime import datetime
#
# from market_sentinel.briefs.health import MarketHealthEngine
# from market_sentinel.briefs.models import (
#     MorningBrief,
#     SectorSnapshot,
#     StockSnapshot,
# )
# from market_sentinel.providers.angelone.models import (
#     IndexSnapshot,
# )
#
# brief = MorningBrief(
#     generated_at=datetime.now(),
#     health_score=0,
#     market_sentiment="",
#     confidence=0,
# )
#
# brief.indices.extend([
#     IndexSnapshot(
#         name="NIFTY",
#         exchange="NSE",
#         token="1",
#         value=25000,
#         change=120,
#         percent_change=1.2,
#         open=0,
#         high=0,
#         low=0,
#         close=0,
#         volume=0,
#         updated_at=datetime.now(),
#     ),
#     IndexSnapshot(
#         name="BANKNIFTY",
#         exchange="NSE",
#         token="2",
#         value=56000,
#         change=-50,
#         percent_change=-0.3,
#         open=0,
#         high=0,
#         low=0,
#         close=0,
#         volume=0,
#         updated_at=datetime.now(),
#     ),
# ])
#
# brief.sectors.extend([
#     SectorSnapshot("IT", 42000, 2.1),
#     SectorSnapshot("AUTO", 32000, 1.3),
#     SectorSnapshot("REALTY", 18000, -0.9),
# ])
#
# brief.gainers.extend([
#     StockSnapshot("HAL", 5100, 5.8),
#     StockSnapshot("BEL", 420, 4.6),
#     StockSnapshot("RELIANCE", 3245, 3.1),
# ])
#
# brief.losers.extend([
#     StockSnapshot("ITC", 451, -1.2),
# ])
#
# engine = MarketHealthEngine()
#
# brief = engine.calculate(brief)
#
# print()
# print("Health Score :", brief.health_score)
# print("Sentiment    :", brief.market_sentiment)
# print("Confidence   :", brief.confidence)