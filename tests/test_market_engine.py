from market_sentinel.market.engine import (
    IndianMarketEngine,
)

engine = IndianMarketEngine()

snapshot = engine.build()

print(snapshot)