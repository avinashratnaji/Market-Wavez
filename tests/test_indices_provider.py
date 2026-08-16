from market_sentinel.providers.angelone.token_registry import TokenRegistry

registry = TokenRegistry()

keywords = [
    "small",
]

for instrument in registry.indices():

    symbol = instrument.symbol.lower()

    if any(word in symbol for word in keywords):
        print(instrument.symbol)