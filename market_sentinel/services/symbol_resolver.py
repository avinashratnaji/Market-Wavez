from market_sentinel.config.market_symbols import MARKET_SYMBOLS

class SymbolResolver:

    @staticmethod
    def resolve(symbol: str) -> str:
        symbol = symbol.strip().lower()
        # Direct Yahoo symbol
        for yahoo_symbol in MARKET_SYMBOLS:
            if yahoo_symbol.lower() == symbol:
                return yahoo_symbol
        # Display name
        for yahoo_symbol, info in MARKET_SYMBOLS.items():
            if info["name"].lower() == symbol:
                return yahoo_symbol
            for alias in info.get("aliases", []):
                if alias.lower() == symbol:
                    return yahoo_symbol
        raise ValueError(f"Unknown market symbol: {symbol}")