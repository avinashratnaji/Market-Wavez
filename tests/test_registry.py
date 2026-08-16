"""
tests/test_registry.py

Tests the Enterprise Token Registry.

Author : Market Sentinel
"""

from pprint import pprint
from market_sentinel.providers.angelone.token_registry import TokenRegistry


def title(text: str):
    print("\n" + "=" * 80)
    print(text)
    print("=" * 80)


registry = TokenRegistry()

# ============================================================================
title("LOAD")
# ============================================================================

registry.load()

# ============================================================================
title("LOOKUP : EXCHANGE + SYMBOL")
# ============================================================================

pprint(
    registry.find(
        "NSE",
        "NIFTY",
    )
)

pprint(
    registry.find(
        "NSE",
        "BANKNIFTY",
    )
)

pprint(
    registry.find(
        "NSE",
        "RELIANCE",
    )
)

# ============================================================================
title("LOOKUP : TRADING SYMBOL")
# ============================================================================

pprint(
    registry.find_by_trading_symbol(
        "TCS-EQ"
    )
)

pprint(
    registry.find_by_trading_symbol(
        "RELIANCE-EQ"
    )
)

# ============================================================================
title("LOOKUP : TOKEN")
# ============================================================================

pprint(
    registry.find_by_token(
        "99926000"
    )
)

pprint(
    registry.find_by_token(
        "11536"
    )
)

# ============================================================================
title("SMART LOOKUP")
# ============================================================================

queries = [
    "nifty",
    "NIFTY50",
    "Nifty 50",
    "bank nifty",
    "BANKNIFTY",
    "reliance",
    "tcs",
    "tcs-eq",
]

for query in queries:

    print(f"\n{query}")

    pprint(
        registry.lookup(query)
    )

# ============================================================================
title("SEARCH : NIFTY")
# ============================================================================

results = registry.search(
    "nifty",
    limit=15,
)

for instrument in results:
    print(
        instrument.trading_symbol,
        instrument.exchange,
    )

# ============================================================================
title("SEARCH : BANK")
# ============================================================================

results = registry.search(
    "bank",
    limit=15,
)

for instrument in results:
    print(
        instrument.trading_symbol,
        instrument.exchange,
    )

# ============================================================================
title("SEARCH : RELIANCE")
# ============================================================================

results = registry.search(
    "reliance",
    limit=10,
)

for instrument in results:
    print(
        instrument.trading_symbol,
        instrument.exchange,
    )

# ============================================================================
title("CATEGORY COUNTS")
# ============================================================================

print("Stocks   :", len(registry.stocks()))
print("Indices  :", len(registry.indices()))
print("ETFs     :", len(registry.etfs()))
print("Futures  :", len(registry.futures()))
print("Options  :", len(registry.options()))
print("Total    :", registry.count())

# ============================================================================
title("FIRST 10 INDICES")
# ============================================================================

for instrument in registry.indices()[:10]:
    print(
        instrument.trading_symbol,
        instrument.token,
    )

# ============================================================================
title("FIRST 10 STOCKS")
# ============================================================================

for instrument in registry.stocks()[:10]:
    print(
        instrument.trading_symbol,
        instrument.token,
    )

# ============================================================================
title("EXISTS")
# ============================================================================

print(
    "NIFTY :",
    registry.exists(
        "NSE",
        "NIFTY",
    )
)

print(
    "TCS :",
    registry.exists(
        "NSE",
        "TCS",
    )
)

print(
    "INVALID :",
    registry.exists(
        "NSE",
        "ABCDEFGHIJK",
    )
)

# ============================================================================
title("TOTAL INSTRUMENTS")
# ============================================================================

print(registry.count())

print("\nRegistry tests completed successfully.")