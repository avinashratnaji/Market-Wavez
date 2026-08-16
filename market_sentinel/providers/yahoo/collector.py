import yfinance as yf

from market_sentinel.providers.base import MarketCollector
from market_sentinel.providers.yahoo.mapper import YahooMapper
from market_sentinel.providers.yahoo.symbols import YAHOO_SYMBOLS
from market_sentinel.database.models.market_data import MarketData
from market_sentinel.utils import logger


class YahooCollector(MarketCollector):
    """
    Yahoo Finance market data collector.
    """

    def __init__(self):
        self.symbols = YAHOO_SYMBOLS

    def collect(self) -> list[MarketData]:
        """
        Collect market data from Yahoo Finance.
        """

        quotes: list[MarketData] = []

        logger.info("Collecting Yahoo Finance data...")

        for symbol, (name, exchange, asset_type) in self.symbols.items():

            try:
                ticker = yf.Ticker(symbol)

                info = ticker.fast_info
                history = ticker.history(period="1mo")

                record = YahooMapper.to_market_data(
                    symbol=symbol,
                    name=name,
                    exchange=exchange,
                    asset_type=asset_type,
                    info=info,
                    history=history,
                )

                quotes.append(record)

                logger.success(f"{name:<15} {record.price}")

            except Exception as ex:
                logger.error(f"{name} -> {ex}")

        return quotes